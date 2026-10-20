FROM golang:1.26-alpine AS build
RUN apk add --no-cache git
ENV CGO_ENABLED=0
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go install -ldflags="-s -w" github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z

FROM alpine:3.23
RUN apk add --no-cache ca-certificates curl && adduser -D -u 10001 minio
COPY --from=build /go/bin/minio /usr/local/bin/minio
RUN mkdir /data && chown minio /data
USER minio
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
