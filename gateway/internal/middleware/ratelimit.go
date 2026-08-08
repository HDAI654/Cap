// Package middleware provides optional edge middleware for the gateway.
package middleware

import (
	"net/http"
	"sync"
	"time"
)

// RateLimiter is a simple per-client fixed-window limiter (process-local).
type RateLimiter struct {
	limit int
	mu    sync.Mutex
	start map[string]time.Time
	count map[string]int
}

// NewRateLimiter returns a limiter; limit <= 0 disables enforcement.
func NewRateLimiter(limitPerMinute int) *RateLimiter {
	return &RateLimiter{
		limit: limitPerMinute,
		start: make(map[string]time.Time),
		count: make(map[string]int),
	}
}

// Allow reports whether clientKey may proceed.
func (r *RateLimiter) Allow(clientKey string) bool {
	if r.limit <= 0 {
		return true
	}
	now := time.Now()
	r.mu.Lock()
	defer r.mu.Unlock()
	start, ok := r.start[clientKey]
	if !ok || now.Sub(start) >= time.Minute {
		r.start[clientKey] = now
		r.count[clientKey] = 1
		return true
	}
	if r.count[clientKey] >= r.limit {
		return false
	}
	r.count[clientKey]++
	return true
}

// Middleware wraps a handler with rate limiting by remote IP.
func (r *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		key := req.RemoteAddr
		if !r.Allow(key) {
			http.Error(w, `{"detail":"Rate limit exceeded"}`, http.StatusTooManyRequests)
			return
		}
		next.ServeHTTP(w, req)
	})
}
