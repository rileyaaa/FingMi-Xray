// Local synthetic peers for published JNI differential tests. No user endpoints.
package main

import (
	"bufio"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"sync"
	"time"

	quic "github.com/apernet/quic-go"
	lib "github.com/xtls/libxray"
)

var outputMu sync.Mutex

func emit(value any) {
	outputMu.Lock()
	defer outputMu.Unlock()
	if err := json.NewEncoder(os.Stdout).Encode(value); err != nil {
		panic(err)
	}
}
func check(err error) {
	if err != nil {
		panic(err)
	}
}

func main() {
	if len(os.Args) == 2 && os.Args[1] == "invoke" {
		scanner := bufio.NewScanner(os.Stdin)
		scanner.Buffer(make([]byte, 4096), 32<<20)
		for scanner.Scan() {
			fmt.Println(lib.Invoke(scanner.Text()))
		}
		check(scanner.Err())
		return
	}
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	check(err)
	template := &x509.Certificate{SerialNumber: big.NewInt(42), Subject: pkix.Name{CommonName: "synthetic.invalid"}, DNSNames: []string{"synthetic.invalid"}, NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(time.Hour), KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	check(err)
	config := &tls.Config{Certificates: []tls.Certificate{{Certificate: [][]byte{der}, PrivateKey: key}}, NextProtos: []string{"h3"}, GetConfigForClient: func(hello *tls.ClientHelloInfo) (*tls.Config, error) {
		emit(map[string]any{"event": "hello", "sni": hello.ServerName, "alpn": hello.SupportedProtos})
		return nil, nil
	}}
	listener, err := quic.ListenAddrEarly("127.0.0.1:0", config, &quic.Config{EnableDatagrams: true})
	check(err)
	defer listener.Close()
	sum := sha256.Sum256(der)
	emit(map[string]any{"event": "ready", "address": listener.Addr().String(), "sha256": hex.EncodeToString(sum[:]), "leaf_der_base64": base64.StdEncoding.EncodeToString(der)})
	for {
		conn, err := listener.Accept(context.Background())
		check(err)
		go func(c *quic.Conn) {
			<-c.Context().Done()
			emit(map[string]any{"event": "accepted", "alpn": c.ConnectionState().TLS.NegotiatedProtocol})
			emit(map[string]any{"event": "closed", "reason": context.Cause(c.Context()).Error()})
		}(conn)
	}
}
