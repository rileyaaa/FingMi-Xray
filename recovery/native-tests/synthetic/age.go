package main

import (
	"bytes"
	"encoding/base64"
	"strings"

	"github.com/metacubex/age"
	"github.com/metacubex/age/armor"
)

// All keys and ciphertexts here are disposable synthetic regression material.
func ageCases() {
	key, err := age.GenerateX25519Identity()
	check(err)
	wrong, err := age.GenerateX25519Identity()
	check(err)
	pq, err := age.GenerateHybridIdentity()
	check(err)
	encrypted := func(plain string, recipient age.Recipient) string {
		var output bytes.Buffer
		arm := armor.NewWriter(&output)
		writer, err := age.Encrypt(arm, recipient)
		check(err)
		_, err = writer.Write([]byte(plain))
		check(err)
		check(writer.Close())
		check(arm.Close())
		return output.String()
	}
	link := "trojan://synthetic@example.invalid:443#synthetic"
	sealed := encrypted(link, key.Recipient())
	cases := []any{}
	add := func(id, input, secret string) {
		cases = append(cases, map[string]any{"id": id, "request": map[string]any{"apiVersion": 2, "method": "convertShareLinksToXrayJson", "payload": map[string]any{"text": input, "age": map[string]string{"secretKey": secret}}}})
	}
	add("age_x25519_success", sealed, key.String())
	add("age_hybrid_success", encrypted(link, pq.Recipient()), pq.String())
	add("age_wrong_identity", sealed, wrong.String())
	add("age_unsupported_identity", sealed, "AGE-PLUGIN-YUBIKEY-1SYNTHETIC")
	add("age_malformed_identity", sealed, "AGE-SECRET-KEY-1BAD")
	add("age_recipient_as_identity", sealed, key.Recipient().String())
	add("age_missing_identity", sealed, "")
	add("age_malformed_armor", armor.Header+"\n!not base64!\n"+armor.Footer, key.String())
	add("age_armor_truncated", strings.TrimSuffix(sealed, armor.Footer+"\n"), key.String())
	add("age_empty_armor", armor.Header+"\n"+armor.Footer, key.String())
	add("age_decrypted_invalid", encrypted("not a share link", key.Recipient()), key.String())
	add("age_empty_plaintext", encrypted("", key.Recipient()), key.String())
	add("age_multiple_links", encrypted(link+"\n"+"vless://00000000-0000-0000-0000-000000000001@example.invalid:443?security=tls#two", key.Recipient()), key.String())
	add("age_plain_then_encrypted", link+"\n"+sealed, key.String())
	add("age_encrypted_then_plain", sealed+"\n"+link, key.String())
	add("age_two_encrypted", sealed+"\n"+sealed, key.String())
	add("age_whitespace_crlf", " \r\n"+strings.ReplaceAll(sealed, "\n", "\r\n")+" \r\n", " "+key.String()+" ")
	lines := strings.Split(strings.TrimSpace(sealed), "\n")
	body, err := base64.StdEncoding.DecodeString(strings.Join(lines[1:len(lines)-1], ""))
	check(err)
	body[len(body)-1] ^= 1
	var corrupted bytes.Buffer
	arm := armor.NewWriter(&corrupted)
	_, err = arm.Write(body)
	check(err)
	check(arm.Close())
	add("age_corrupt_ciphertext", corrupted.String(), key.String())
	for _, kind := range []string{"", "x25519", "hybrid", " X25519 ", "HYBRID", "scrypt", "ssh", "invalid"} {
		cases = append(cases, map[string]any{"id": "key_" + kind, "request": map[string]any{"apiVersion": 2, "method": "generateAgeKeyPair", "payload": map[string]string{"keyType": kind}}})
	}
	cases = append(cases, map[string]any{"id": "key_bad_payload", "request": map[string]any{"apiVersion": 2, "method": "generateAgeKeyPair", "payload": map[string]int{"keyType": 3}}})
	emit(cases)
}
