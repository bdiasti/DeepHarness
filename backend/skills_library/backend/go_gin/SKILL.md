---
name: go_gin
description: Go backend with Gin framework, hexagonal architecture, error handling
---

# Go + Gin

Go HTTP API with Gin, organized using hexagonal (ports & adapters) architecture and idiomatic error handling.

## Project Layout

```
/cmd/api/main.go         # entry point
/internal/domain         # entities, ports (interfaces)
/internal/app            # use cases / services
/internal/adapter/http   # gin handlers
/internal/adapter/repo   # db implementations
```

## Domain (Port)

```go
// internal/domain/user.go
package domain

import "context"

type User struct {
    ID    int64
    Email string
    Name  string
}

type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, u *User) error
}
```

## Use Case

```go
// internal/app/user_service.go
package app

import (
    "context"
    "errors"
    "example.com/internal/domain"
)

var ErrNotFound = errors.New("user not found")

type UserService struct{ Repo domain.UserRepository }

func (s *UserService) Get(ctx context.Context, id int64) (*domain.User, error) {
    u, err := s.Repo.FindByID(ctx, id)
    if err != nil { return nil, err }
    if u == nil { return nil, ErrNotFound }
    return u, nil
}
```

## Gin Handler

```go
// internal/adapter/http/user_handler.go
package httpadapter

import (
    "errors"
    "net/http"
    "strconv"
    "github.com/gin-gonic/gin"
    "example.com/internal/app"
)

type UserHandler struct{ Svc *app.UserService }

func (h *UserHandler) Register(r *gin.Engine) {
    r.GET("/users/:id", h.get)
    r.POST("/users", h.create)
}

func (h *UserHandler) get(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil { c.JSON(400, gin.H{"error": "bad id"}); return }
    u, err := h.Svc.Get(c.Request.Context(), id)
    switch {
    case errors.Is(err, app.ErrNotFound):
        c.JSON(http.StatusNotFound, gin.H{"error": "not found"})
    case err != nil:
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
    default:
        c.JSON(http.StatusOK, u)
    }
}

type createReq struct {
    Email string `json:"email" binding:"required,email"`
    Name  string `json:"name"  binding:"required"`
}

func (h *UserHandler) create(c *gin.Context) {
    var req createReq
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()}); return
    }
    c.JSON(201, gin.H{"ok": true})
}
```

## Main

```go
// cmd/api/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "example.com/internal/app"
    httpadapter "example.com/internal/adapter/http"
    "example.com/internal/adapter/repo"
)

func main() {
    r := gin.Default()
    svc := &app.UserService{Repo: repo.NewPostgresUserRepo(/* db */)}
    (&httpadapter.UserHandler{Svc: svc}).Register(r)
    r.Run(":8080")
}
```

## Tips
- Wrap errors with `fmt.Errorf("ctx: %w", err)`; unwrap via `errors.Is`/`errors.As`.
- Pass `context.Context` through all layers; honor cancellation.
- Keep handlers thin: parse, call service, map errors to HTTP.
- Use `gin.Recovery()` and structured logging middleware (zerolog/zap).
