package libXray

// Reconstructed behavior constrained by published-v7-lifecycle.json.
// Barrier starts admit either legal mutex order; no sleeps or timing assertions.
import (
	"encoding/json"
	"net"
	"strings"
	"sync"
	"testing"
)

type lifecycleReply struct {
	Success bool            `json:"success"`
	Data    json.RawMessage `json:"data"`
	Error   string          `json:"error"`
}

func lifecycleInvoke(method, config string) lifecycleReply {
	req := map[string]any{"apiVersion": 2, "method": method}
	if config != "" {
		req["payload"] = map[string]string{"xrayJson": config}
	}
	raw, _ := json.Marshal(req)
	var result lifecycleReply
	if err := json.Unmarshal([]byte(Invoke(string(raw))), &result); err != nil {
		panic(err)
	}
	return result
}

func lifecycleParallel(calls ...func() lifecycleReply) []lifecycleReply {
	barrier := make(chan struct{})
	var ready, done sync.WaitGroup
	ready.Add(len(calls))
	done.Add(len(calls))
	result := make([]lifecycleReply, len(calls))
	for i, call := range calls {
		go func(i int, call func() lifecycleReply) {
			defer done.Done()
			ready.Done()
			<-barrier
			result[i] = call()
		}(i, call)
	}
	ready.Wait()
	close(barrier)
	done.Wait()
	return result
}

func TestPublishedLifecycle(t *testing.T) {
	valid := `{"outbounds":[{"protocol":"freedom","tag":"direct"}]}`
	run := func() lifecycleReply { return lifecycleInvoke("runXray", valid) }
	stop := func() lifecycleReply { return lifecycleInvoke("stopXray", "") }
	test := func() lifecycleReply { return lifecycleInvoke("testXray", valid) }
	ok := func(r lifecycleReply) {
		t.Helper()
		if !r.Success || r.Error != "" || string(r.Data) != "{}" {
			t.Fatalf("expected no-data success: %+v", r)
		}
	}
	state := func(want bool) {
		t.Helper()
		r := lifecycleInvoke("getXrayState", "")
		var value struct {
			Running bool `json:"running"`
		}
		if err := json.Unmarshal(r.Data, &value); err != nil || !r.Success || value.Running != want {
			t.Fatalf("state wanted %v: %+v", want, r)
		}
	}
	ok(stop())
	t.Cleanup(func() { stop() })
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	busyPort := listener.Addr().(*net.TCPAddr).Port
	available, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	freePort := available.Addr().(*net.TCPAddr).Port
	available.Close()
	config := func(ports ...int) string {
		inbounds := []any{}
		for _, port := range ports {
			inbounds = append(inbounds, map[string]any{
				"listen": "127.0.0.1", "port": port, "protocol": "socks", "settings": map[string]bool{"udp": false},
			})
		}
		raw, _ := json.Marshal(map[string]any{"inbounds": inbounds,
			"outbounds": []any{map[string]string{"protocol": "freedom"}}})
		return string(raw)
	}
	ok(lifecycleInvoke("testXray", config(busyPort)))
	state(false)
	r := lifecycleInvoke("runXray", config(freePort, busyPort))
	if r.Success || !strings.Contains(r.Error, "address already in use") {
		t.Fatalf("expected failed partial Start: %+v", r)
	}
	state(false)
	ok(lifecycleInvoke("runXray", config(freePort)))
	ok(stop())
	for _, method := range []string{"runXray", "testXray"} {
		r = lifecycleInvoke(method, "invalid")
		if r.Success || string(r.Data) != "null" {
			t.Fatalf("invalid %s: %+v", method, r)
		}
		state(false)
	}
	replies := lifecycleParallel(run, run)
	successes, rejected := 0, 0
	for _, reply := range replies {
		if reply.Success {
			successes++
		} else if reply.Error == "xray is already running" {
			rejected++
		}
	}
	if successes != 1 || rejected != 1 {
		t.Fatalf("competing run: %+v", replies)
	}
	state(true)
	ok(test())
	state(true)
	if r = lifecycleInvoke("runXray", "invalid"); r.Error != "xray is already running" {
		t.Fatalf("running guard precedence: %+v", r)
	}
	replies = lifecycleParallel(stop, run)
	ok(replies[0])
	if !replies[1].Success && replies[1].Error != "xray is already running" {
		t.Fatalf("overlap: %+v", replies)
	}
	state(replies[1].Success)
	ok(stop())
	for _, reply := range lifecycleParallel(stop, stop) {
		ok(reply)
	}
	for _, reply := range lifecycleParallel(test, run) {
		ok(reply)
	}
	state(true)
	ok(stop())
	state(false)
}
