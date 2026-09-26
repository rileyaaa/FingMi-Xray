package libXray

import (
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"

	"github.com/metacubex/age"
)

func TestPublishedAgeMatrix(t *testing.T) {
	path := os.Getenv("PUBLISHED_AGE_FIXTURE")
	if path == "" {
		t.Skip("set PUBLISHED_AGE_FIXTURE to the frozen published-v7-age-matrix.json")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Cases []struct {
			ID       string
			Request  json.RawMessage
			Response json.RawMessage
		}
	}
	if err = json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, row := range fixture.Cases {
		t.Run(row.ID, func(t *testing.T) {
			actual := Invoke(string(row.Request))
			var got, want map[string]any
			if err := json.Unmarshal([]byte(actual), &got); err != nil {
				t.Fatal(err)
			}
			if err := json.Unmarshal(row.Response, &want); err != nil {
				t.Fatal(err)
			}
			if strings.HasPrefix(row.ID, "key_") && want["success"] == true {
				validate := func(value map[string]any) {
					t.Helper()
					if len(value) != 3 || value["success"] != true || value["error"] != "" {
						t.Fatalf("key envelope: %v", value)
					}
					pair, ok := value["data"].(map[string]any)
					if !ok || len(pair) != 2 {
						t.Fatalf("key shape: %v", value)
					}
					secret, ok := pair["secretKey"].(string)
					if !ok {
						t.Fatal("missing secretKey")
					}
					if row.ID == "key_hybrid" {
						key, err := age.ParseHybridIdentity(secret)
						if err != nil {
							t.Fatal(err)
						}
						if key.Recipient().String() != pair["publicKey"] {
							t.Fatal("hybrid public key mismatch")
						}
					} else {
						key, err := age.ParseX25519Identity(secret)
						if err != nil {
							t.Fatal(err)
						}
						if key.Recipient().String() != pair["publicKey"] {
							t.Fatal("x25519 public key mismatch")
						}
					}
				}
				validate(want)
				validate(got)
			} else if !reflect.DeepEqual(got, want) {
				t.Fatalf("published=%s\nreconstructed=%s", row.Response, actual)
			}
		})
	}
}
