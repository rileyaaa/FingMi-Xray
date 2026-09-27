// Tests the fixed core's actual DialSystem, not a replica of its selection logic.
package nodedns_test

import (
	"context"
	"io"
	"net"
	"sync/atomic"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
	"golang.org/x/net/dns/dnsmessage"
)

// The local server answers AAAA-only or dual-stack; never contacts external DNS.
func localDNS(t *testing.T) *atomic.Int32 {
	t.Helper()
	c, err := net.ListenPacket("udp4", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	count := new(atomic.Int32)
	done := make(chan struct{})
	go func() {
		defer close(done)
		b := make([]byte, 2048)
		for {
			n, a, e := c.ReadFrom(b)
			if e != nil {
				return
			}
			count.Add(1)
			var msg dnsmessage.Message
			if msg.Unpack(b[:n]) != nil {
				continue
			}
			out := dnsmessage.Message{Header: dnsmessage.Header{ID: msg.ID, Response: true, RecursionDesired: true, RecursionAvailable: true}, Questions: msg.Questions}
			for _, q := range msg.Questions {
				h := dnsmessage.ResourceHeader{Name: q.Name, Class: dnsmessage.ClassINET, TTL: 0}
				if q.Type == dnsmessage.TypeAAAA {
					h.Type = q.Type
					out.Answers = append(out.Answers, dnsmessage.Resource{Header: h, Body: &dnsmessage.AAAAResource{AAAA: [16]byte{15: 1}}})
				}
				if q.Type == dnsmessage.TypeA && q.Name.String() == "dual.synthetic.invalid." {
					h.Type = q.Type
					out.Answers = append(out.Answers, dnsmessage.Resource{Header: h, Body: &dnsmessage.AResource{A: [4]byte{127, 0, 0, 2}}})
				}
			}
			data, e := out.Pack()
			if e == nil {
				c.WriteTo(data, a)
			}
		}
	}()
	// Preserve the pointer shared by Xray's common/net aliases.
	original := *net.DefaultResolver
	*net.DefaultResolver = net.Resolver{PreferGo: true, Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, "udp4", c.LocalAddr().String())
	}}
	t.Cleanup(func() { *net.DefaultResolver = original; c.Close(); <-done })
	return count
}

func TestEndpointResolverOwnership(t *testing.T) {
	queries := localDNS(t)
	// Configured Xray DNS deliberately left uninitialized. These calls must use
	// system resolver with nil/AsIs sockopt, regardless of outbound targetStrategy.
	for _, name := range []string{"aaaa.synthetic.invalid", "dual.synthetic.invalid", "::1"} {
		for _, explicitAsIs := range []bool{false, true} {
			t.Run(name+map[bool]string{false: "/nil", true: "/AsIs"}[explicitAsIs], func(t *testing.T) {
				l, e := net.Listen("tcp6", "[::1]:0")
				if e != nil {
					t.Fatal(e)
				}
				defer l.Close()
				accepted := make(chan error, 1)
				go func() {
					c, e := l.Accept()
					if e == nil {
						_, e = c.Write([]byte("ok"))
						c.Close()
					}
					accepted <- e
				}()
				before := queries.Load()
				var sock *internet.SocketConfig
				if explicitAsIs {
					sock = &internet.SocketConfig{DomainStrategy: internet.DomainStrategy_AS_IS}
				}
				dest := xnet.TCPDestination(xnet.ParseAddress(name), xnet.Port(l.Addr().(*net.TCPAddr).Port))
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				defer cancel()
				c, e := internet.DialSystem(ctx, dest, sock)
				if e != nil {
					t.Fatal(e)
				}
				defer c.Close()
				c.SetReadDeadline(time.Now().Add(5 * time.Second))
				data := make([]byte, 2)
				if _, e = io.ReadFull(c, data); e != nil || string(data) != "ok" {
					t.Fatalf("read: %v", e)
				}
				if e = <-accepted; e != nil {
					t.Fatal(e)
				}
				if name == "::1" && queries.Load() != before {
					t.Fatal("Literal IPv6 queried DNS")
				}
				if name != "::1" && queries.Load() == before {
					t.Fatal("Domain did not reach resolver")
				}
				if dest.Address.String() != name && name != "::1" {
					t.Fatal("Caller endpoint mutated")
				}
				tc := (&xtls.Config{ServerName: "sni.synthetic.invalid"}).GetTLSConfig(xtls.WithDestination(dest))
				if tc.ServerName != "sni.synthetic.invalid" {
					t.Fatal("TLS identity overwritten")
				}
			})
		}
	}
	// HY2/KCP use this same UDP branch; it selects a single address, no TCP-style race.
	for _, name := range []string{"aaaa.synthetic.invalid", "dual.synthetic.invalid", "::1"} {
		t.Run("udp/"+name, func(t *testing.T) {
			before := queries.Load()
			bind := "[::1]:0"
			network := "udp6"
			if name == "dual.synthetic.invalid" {
				bind = "127.0.0.2:0"
				network = "udp4"
			}
			peer, e := net.ListenPacket(network, bind)
			if e != nil {
				t.Fatal(e)
			}
			defer peer.Close()
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			c, e := internet.DialSystem(ctx, xnet.UDPDestination(xnet.ParseAddress(name), xnet.Port(peer.LocalAddr().(*net.UDPAddr).Port)), nil)
			if e != nil {
				t.Fatal(e)
			}
			defer c.Close()
			got := c.RemoteAddr().(*net.UDPAddr).IP
			expected := net.ParseIP("::1")
			if name == "dual.synthetic.invalid" {
				expected = net.ParseIP("127.0.0.2")
			}
			if !got.Equal(expected) {
				t.Fatalf("UDP selected %v, want %v", got, expected)
			}
			if name == "::1" && queries.Load() != before {
				t.Fatal("Literal UDP IPv6 queried DNS")
			}
			if _, e = c.Write([]byte("synthetic")); e != nil {
				t.Fatal(e)
			}
			peer.SetReadDeadline(time.Now().Add(5 * time.Second))
			data := make([]byte, 32)
			n, _, e := peer.ReadFrom(data)
			if e != nil || string(data[:n]) != "synthetic" {
				t.Fatalf("UDP receive: %v", e)
			}
		})
	}
}
