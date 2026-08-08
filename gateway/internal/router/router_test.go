package router

import "testing"

func TestMatchAuthPublic(t *testing.T) {
	table := Build("http://auth", "http://orders", "http://wallets", "http://admin", "http://mda")
	rule := table.Match("/api/v1/auth/login")
	if rule == nil {
		t.Fatal("expected match")
	}
	if rule.RequiredRoles != nil {
		t.Fatal("auth routes must be public")
	}
}

func TestMatchOrdersAuthenticated(t *testing.T) {
	table := Build("http://auth", "http://orders", "http://wallets", "http://admin", "http://mda")
	rule := table.Match("/api/v1/orders/abc")
	if rule == nil {
		t.Fatal("expected match")
	}
	if _, ok := rule.RequiredRoles[RoleUser]; !ok {
		t.Fatal("USER must be allowed")
	}
}

func TestMatchInstrumentsAdminOnly(t *testing.T) {
	table := Build("http://auth", "http://orders", "http://wallets", "http://admin", "http://mda")
	rule := table.Match("/api/v1/instruments")
	if rule == nil {
		t.Fatal("expected match")
	}
	if _, ok := rule.RequiredRoles[RoleUser]; ok {
		t.Fatal("USER must not access instruments")
	}
	if _, ok := rule.RequiredRoles[RoleAdmin]; !ok {
		t.Fatal("ADMIN required")
	}
}

func TestNoMatch(t *testing.T) {
	table := Build("http://auth", "http://orders", "http://wallets", "http://admin", "http://mda")
	if table.Match("/api/v1/unknown") != nil {
		t.Fatal("expected no match")
	}
}
