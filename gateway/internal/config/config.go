// Package config loads gateway settings from the environment.
package config

import (
	"os"
	"strconv"
	"strings"
)

// Config holds process configuration for the Cap API Gateway.
type Config struct {
	AppName  string
	HTTPAddr string

	AuthServiceURL       string
	OrderServiceURL      string
	WalletServiceURL     string
	AdminServiceURL      string
	MarketDataServiceURL string
	NotificationWSURL    string // http(s) base; upgraded to ws(s) by clients/proxy

	// PEM-encoded RSA public key used to verify access tokens (same as Auth).
	AuthPublicKeyPEM string
	JWTAlgorithm     string

	RateLimitPerMinute int
}

// Load reads configuration from environment variables with safe defaults.
func Load() Config {
	return Config{
		AppName:              getenv("APP_NAME", "CapGateway"),
		HTTPAddr:             getenv("HTTP_ADDR", ":8080"),
		AuthServiceURL:       strings.TrimRight(getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8000"), "/"),
		OrderServiceURL:      strings.TrimRight(getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003"), "/"),
		WalletServiceURL:     strings.TrimRight(getenv("WALLET_SERVICE_URL", "http://127.0.0.1:8001"), "/"),
		AdminServiceURL:      strings.TrimRight(getenv("ADMIN_SERVICE_URL", "http://127.0.0.1:8002"), "/"),
		MarketDataServiceURL: strings.TrimRight(getenv("MARKET_DATA_SERVICE_URL", "http://127.0.0.1:8004"), "/"),
		NotificationWSURL:    strings.TrimRight(getenv("NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8005"), "/"),
		AuthPublicKeyPEM:     getenv("AUTH_PUBLIC_KEY", ""),
		JWTAlgorithm:         getenv("AUTH_TOKEN_ALGORITHM", "RS256"),
		RateLimitPerMinute:   getenvInt("RATE_LIMIT_PER_MINUTE", 0),
	}
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func getenvInt(key string, def int) int {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}
