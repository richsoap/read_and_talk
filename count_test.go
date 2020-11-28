package main

import "testing"

func TestCountOne(t *testing.T) {
	t.Logf("count 6 %v", countOne(6))
	t.Logf("count 1 %v", countOne(1))
	t.Logf("count 9 %v", countOne(9))
	t.Logf("count 16 %v", countOne(16))
}
