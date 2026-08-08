// Cap API Gateway — edge JWT verification, role checks, reverse proxy (net/http).
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/HDAI654/Cap/gateway/internal/auth"
	"github.com/HDAI654/Cap/gateway/internal/config"
	"github.com/HDAI654/Cap/gateway/internal/middleware"
	"github.com/HDAI654/Cap/gateway/internal/proxy"
	"github.com/HDAI654/Cap/gateway/internal/router"
)

func writeJSON(w http.ResponseWriter, status int, body string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write([]byte(body))
}

func main() {
	cfg := config.Load()

	var validator *auth.Validator
	if strings.TrimSpace(cfg.AuthPublicKeyPEM) != "" {
		v, err := auth.NewValidator(cfg.AuthPublicKeyPEM)
		if err != nil {
			log.Fatalf("jwt validator: %v", err)
		}
		validator = v
	} else {
		log.Println("WARNING: AUTH_PUBLIC_KEY empty — protected routes will return 503")
	}

	table := router.Build(
		cfg.AuthServiceURL,
		cfg.OrderServiceURL,
		cfg.WalletServiceURL,
		cfg.AdminServiceURL,
		cfg.MarketDataServiceURL,
	)

	// Pre-build reverse proxies per upstream base URL.
	proxies := map[string]http.Handler{}
	for _, rule := range table {
		if _, ok := proxies[rule.UpstreamBase]; ok {
			continue
		}
		p, err := proxy.New(rule.UpstreamBase)
		if err != nil {
			log.Fatalf("proxy for %s: %v", rule.UpstreamBase, err)
		}
		proxies[rule.UpstreamBase] = p
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{
			"status":  "ok",
			"service": cfg.AppName,
		})
	})

	// Catch-all API proxy.
	apiHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rule := table.Match(r.URL.Path)
		if rule == nil {
			writeJSON(w, http.StatusNotFound, `{"detail":"No route"}`)
			return
		}

		if rule.RequiredRoles != nil {
			if validator == nil {
				writeJSON(w, http.StatusServiceUnavailable, `{"detail":"Gateway AUTH_PUBLIC_KEY is not configured"}`)
				return
			}
			principal, err := validator.ValidateAccessToken(r.Header.Get("Authorization"))
			if err != nil {
				if ae, ok := err.(*auth.AuthError); ok {
					writeJSON(w, ae.Status, `{"detail":"`+ae.Message+`"}`)
					return
				}
				writeJSON(w, http.StatusUnauthorized, `{"detail":"Unauthorized"}`)
				return
			}
			if err := auth.RequireRoles(principal, rule.RequiredRoles); err != nil {
				if ae, ok := err.(*auth.AuthError); ok {
					writeJSON(w, ae.Status, `{"detail":"`+ae.Message+`"}`)
					return
				}
				writeJSON(w, http.StatusForbidden, `{"detail":"Forbidden"}`)
				return
			}
			// Propagate identity for upstream services that trust gateway headers.
			r.Header.Set("X-User-Id", principal.UserID)
			r.Header.Set("X-User-Role", principal.Role)
			if principal.SessionID != "" {
				r.Header.Set("X-Session-Id", principal.SessionID)
			}
		}

		upstream, ok := proxies[rule.UpstreamBase]
		if !ok {
			writeJSON(w, http.StatusBadGateway, `{"detail":"Bad gateway"}`)
			return
		}
		upstream.ServeHTTP(w, r)
	})

	// WebSocket auth gate for notifications (identity only; upgrade proxied if needed later).
	mux.HandleFunc("/ws/v1/notifications/", func(w http.ResponseWriter, r *http.Request) {
		if validator == nil {
			writeJSON(w, http.StatusServiceUnavailable, `{"detail":"Gateway AUTH_PUBLIC_KEY is not configured"}`)
			return
		}
		// trader_id is the path suffix after /ws/v1/notifications/
		traderID := strings.TrimPrefix(r.URL.Path, "/ws/v1/notifications/")
		traderID = strings.Trim(traderID, "/")
		if traderID == "" || strings.Contains(traderID, "/") {
			writeJSON(w, http.StatusBadRequest, `{"detail":"Invalid trader_id"}`)
			return
		}

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			if tok := r.URL.Query().Get("access_token"); tok != "" {
				authHeader = "Bearer " + tok
			}
		}
		principal, err := validator.ValidateAccessToken(authHeader)
		if err != nil {
			writeJSON(w, http.StatusUnauthorized, `{"detail":"Unauthorized"}`)
			return
		}
		if principal.Role != router.RoleAdmin && principal.UserID != traderID {
			writeJSON(w, http.StatusForbidden, `{"detail":"Forbidden"}`)
			return
		}

		// Full WS reverse-proxy can be enabled when co-located; identity gate is required.
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{
			"type":      "gateway.ws.authorized",
			"trader_id": traderID,
			"user_id":   principal.UserID,
			"role":      principal.Role,
			"upstream":  cfg.NotificationWSURL + "/ws/v1/notifications/" + traderID,
		})
	})

	mux.Handle("/api/", apiHandler)

	handler := middleware.NewRateLimiter(cfg.RateLimitPerMinute).Middleware(mux)

	log.Printf("%s listening on %s", cfg.AppName, cfg.HTTPAddr)
	if err := http.ListenAndServe(cfg.HTTPAddr, handler); err != nil {
		log.Println(err)
		os.Exit(1)
	}
}
