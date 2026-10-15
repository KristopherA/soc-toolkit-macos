# Hayabusa: Sigma-based Windows event log (EVTX) triage and timelines. Pinned release, checksum-verified,
# static musl binary on Alpine, non-root. Rules live in a named volume so `update-rules` persists.
FROM alpine:3.20 AS fetch
ARG HAYABUSA_VERSION=4.1.0
ARG SHA256_arm64=385604bf8f9922ded5a2f9dda1c4f0786bb49f1b6ae85c7516bec9a744a27b16
ARG SHA256_amd64=2348a889c1d5dc07880f170e131c61ef68af1c1e1d3cebd5bed8af2d17d42bed
ARG TARGETARCH
RUN apk add --no-cache curl unzip
RUN set -eu; \
    case "$TARGETARCH" in arm64) a=aarch64; sum=$SHA256_arm64 ;; amd64) a=x64; sum=$SHA256_amd64 ;; *) echo "unsupported arch $TARGETARCH"; exit 1 ;; esac; \
    curl -fsSL -o /tmp/h.zip "https://github.com/Yamato-Security/hayabusa/releases/download/v${HAYABUSA_VERSION}/hayabusa-${HAYABUSA_VERSION}-lin-${a}-musl.zip"; \
    echo "$sum  /tmp/h.zip" | sha256sum -c -; \
    mkdir -p /opt/hayabusa && unzip -q /tmp/h.zip -d /opt/hayabusa; \
    mv /opt/hayabusa/hayabusa-${HAYABUSA_VERSION}-lin-${a}-musl /opt/hayabusa/hayabusa; \
    chmod 755 /opt/hayabusa/hayabusa; \
    touch /opt/hayabusa/rules/.shipped-release

FROM alpine:3.20
RUN apk add --no-cache ca-certificates && adduser -D -u 1000 analyst
COPY --from=fetch --chown=analyst:analyst /opt/hayabusa /opt/hayabusa
COPY --chmod=755 entrypoint.sh /usr/local/bin/hayabusa
USER analyst
WORKDIR /case
ENTRYPOINT ["/usr/local/bin/hayabusa"]
CMD ["help"]
