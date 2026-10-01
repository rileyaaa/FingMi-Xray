package libXray

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

// Only the conversion handler is under recovery here. API v2 dispatch, probes,
// age encryption, start/stop and inline core calls are explicitly outside scope.
func TestRecoveredPublishedConverter(t *testing.T) {
	path := os.Getenv("PUBLISHED_CONVERTER_FIXTURE")
	if path == "" {
		t.Skip("set PUBLISHED_CONVERTER_FIXTURE")
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	var fixture struct {
		Cases []struct {
			ID       string
			Request  json.RawMessage
			Response any
		}
	}
	if e = json.Unmarshal(raw, &fixture); e != nil {
		t.Fatal(e)
	}
	count := 0
	for _, c := range fixture.Cases {
		var req struct {
			APIVersion int
			Method     string
			Payload    json.RawMessage
		}
		if json.Unmarshal(c.Request, &req) != nil || req.APIVersion != 2 || req.Method != "convertShareLinksToXrayJson" {
			continue
		}
		count++
		t.Run(c.ID, func(t *testing.T) {
			actual := invokeConvertShareLinksToXrayJson(req.Payload)
			var parsed any
			if e := json.Unmarshal([]byte(actual), &parsed); e != nil {
				t.Fatal(e)
			}
			if !reflect.DeepEqual(parsed, c.Response) {
				expected, _ := json.Marshal(c.Response)
				t.Errorf("published response mismatch\nactual: %s\nexpected: %s", actual, expected)
			}
		})
	}
	if count == 0 {
		t.Fatal("no conversion cases")
	}
	t.Logf("Compared %d real native conversion responses", count)
}
