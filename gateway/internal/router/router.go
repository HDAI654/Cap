// Package router defines gateway route rules and role requirements.
package router

import "strings"

// Role constants aligned with Cap Auth Service claims.
const (
	RoleUser  = "USER"
	RoleAdmin = "ADMIN"
)

// Rule matches a path prefix and forwards to an upstream base URL.
type Rule struct {
	PathPrefix    string
	UpstreamBase  string
	RequiredRoles map[string]struct{} // nil => public
}

// Table is an ordered list of rules (first match wins).
type Table []Rule

// Build constructs the Cap gateway route table.
func Build(authURL, orderURL, walletURL, adminURL, mdaURL string) Table {
	authenticated := map[string]struct{}{RoleUser: {}, RoleAdmin: {}}
	adminOnly := map[string]struct{}{RoleAdmin: {}}

	return Table{
		// Public — Auth Service owns its own checks
		{PathPrefix: "/api/v1/auth", UpstreamBase: authURL, RequiredRoles: nil},
		// Admin-only
		{PathPrefix: "/api/v1/instruments", UpstreamBase: adminURL, RequiredRoles: adminOnly},
		// Authenticated trader APIs
		{PathPrefix: "/api/v1/orders", UpstreamBase: orderURL, RequiredRoles: authenticated},
		{PathPrefix: "/api/v1/wallets", UpstreamBase: walletURL, RequiredRoles: authenticated},
		{PathPrefix: "/api/v1/market-data", UpstreamBase: mdaURL, RequiredRoles: authenticated},
	}
}

// Match returns the first rule whose path prefix matches, or nil.
func (t Table) Match(path string) *Rule {
	for i := range t {
		rule := &t[i]
		prefix := rule.PathPrefix
		if path == prefix || strings.HasPrefix(path, prefix+"/") {
			return rule
		}
	}
	return nil
}
