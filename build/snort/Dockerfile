# Snort 3 for offline PCAP replay and rule testing, built from pinned, checksum-verified source
# (no maintained multi-arch image exists). Build takes roughly 10 minutes. Runs as non-root with no network.
FROM debian:bookworm-slim AS build
ARG LIBDAQ_VERSION=3.0.27
ARG LIBDAQ_SHA256=03fac3da27e3230a7d26262f2480cd65a409cee3596c6758a7f9eacb7f24601c
ARG SNORT_VERSION=3.12.2.0
ARG SNORT_SHA256=43000d6b0e0307bc1a735874d00deb61e8b6a96d074f8cc9b2fe2cde0058720b
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake pkg-config autoconf automake libtool flex libfl-dev bison curl ca-certificates \
      libdumbnet-dev libhwloc-dev libluajit-5.1-dev libssl-dev libpcap-dev libpcre2-dev zlib1g-dev liblzma-dev uuid-dev \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN curl -fsSL -o daq.tgz "https://github.com/snort3/libdaq/archive/refs/tags/v${LIBDAQ_VERSION}.tar.gz" \
 && echo "${LIBDAQ_SHA256}  daq.tgz" | sha256sum -c - \
 && tar xzf daq.tgz && cd libdaq-${LIBDAQ_VERSION} \
 && ./bootstrap && ./configure --prefix=/usr/local && make -j"$(nproc)" && make install && ldconfig
RUN curl -fsSL -o snort.tgz "https://github.com/snort3/snort3/archive/refs/tags/${SNORT_VERSION}.tar.gz" \
 && echo "${SNORT_SHA256}  snort.tgz" | sha256sum -c - \
 && tar xzf snort.tgz && cd snort3-${SNORT_VERSION} \
 && ./configure_cmake.sh --prefix=/usr/local --disable-docs \
 && cd build && make -j"$(nproc)" && make install \
 && rm -rf /usr/local/share/doc /usr/local/include

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      libdumbnet1 libhwloc15 libnuma1 libluajit-5.1-2 libssl3 libpcap0.8 libpcre2-8-0 zlib1g liblzma5 libuuid1 \
 && rm -rf /var/lib/apt/lists/* && useradd -m -u 1000 analyst
COPY --from=build /usr/local /usr/local
COPY snort-replay /usr/local/bin/snort-replay
RUN chmod 755 /usr/local/bin/snort-replay && ldconfig && snort -V
USER analyst
WORKDIR /case
ENTRYPOINT ["snort"]
CMD ["-V"]
