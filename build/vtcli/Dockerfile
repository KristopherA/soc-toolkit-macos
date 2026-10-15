# VirusTotal CLI: static Go binary in a distroless, non-root image (no shell).
FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o /vt ./vt/main.go

FROM gcr.io/distroless/static:nonroot
COPY --from=build /vt /vt
ENTRYPOINT ["/vt"]
