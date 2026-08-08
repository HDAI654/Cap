// Package auth verifies Cap access tokens (RS256) at the gateway edge.
package auth

import (
	"crypto/rsa"
	"errors"
	"fmt"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

// Principal is the authenticated caller extracted from a verified access token.
type Principal struct {
	UserID    string
	Role      string
	SessionID string
	Device    string
}

// Validator verifies Bearer access tokens using an RSA public key.
type Validator struct {
	publicKey *rsa.PublicKey
}

// NewValidator parses a PEM-encoded RSA public key.
func NewValidator(publicKeyPEM string) (*Validator, error) {
	if strings.TrimSpace(publicKeyPEM) == "" {
		return nil, errors.New("AUTH_PUBLIC_KEY is empty")
	}
	key, err := jwt.ParseRSAPublicKeyFromPEM([]byte(publicKeyPEM))
	if err != nil {
		return nil, fmt.Errorf("parse public key: %w", err)
	}
	return &Validator{publicKey: key}, nil
}

// ValidateAccessToken verifies the Authorization header value (Bearer …).
func (v *Validator) ValidateAccessToken(authorizationHeader string) (*Principal, error) {
	if authorizationHeader == "" {
		return nil, &AuthError{Status: 401, Message: "Missing Authorization header"}
	}
	if !strings.HasPrefix(authorizationHeader, "Bearer ") {
		return nil, &AuthError{Status: 401, Message: "Invalid Authorization scheme"}
	}
	raw := strings.TrimSpace(strings.TrimPrefix(authorizationHeader, "Bearer "))
	if raw == "" {
		return nil, &AuthError{Status: 401, Message: "Empty bearer token"}
	}

	token, err := jwt.Parse(raw, func(t *jwt.Token) (any, error) {
		if t.Method == nil || t.Method.Alg() != jwt.SigningMethodRS256.Alg() {
			return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
		}
		return v.publicKey, nil
	})
	if err != nil || !token.Valid {
		return nil, &AuthError{Status: 401, Message: "Invalid token"}
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, &AuthError{Status: 401, Message: "Invalid token claims"}
	}

	if typ, _ := claims["type"].(string); typ != "" && typ != "access" {
		return nil, &AuthError{Status: 401, Message: "Access token required"}
	}

	sub, _ := claims["sub"].(string)
	if sub == "" {
		return nil, &AuthError{Status: 401, Message: "Token missing subject"}
	}
	role, _ := claims["role"].(string)
	if role == "" {
		role = "USER"
	}
	role = strings.ToUpper(role)
	sid, _ := claims["sid"].(string)
	dev, _ := claims["dev"].(string)

	return &Principal{
		UserID:    sub,
		Role:      role,
		SessionID: sid,
		Device:    dev,
	}, nil
}

// RequireRoles returns 403 when principal.Role is not in allowed.
func RequireRoles(p *Principal, allowed map[string]struct{}) error {
	if _, ok := allowed[p.Role]; !ok {
		return &AuthError{Status: 403, Message: "Insufficient role"}
	}
	return nil
}

// AuthError is returned for authentication / authorization failures.
type AuthError struct {
	Status  int
	Message string
}

func (e *AuthError) Error() string { return e.Message }
