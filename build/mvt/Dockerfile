# Mobile Verification Toolkit without the USB/libimobiledevice toolchain (Docker Desktop
# on a Mac cannot pass USB devices through). Works from iOS backups and AndroidQF dumps.
# pyahocorasick has no ARM64 wheel, so it is compiled in a builder stage.
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/mvt
COPY . /tmp/mvt
RUN /opt/mvt/bin/pip install /tmp/mvt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/mvt/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends libusb-1.0-0 sqlite3 \
 && rm -rf /var/lib/apt/lists/* && useradd -m -u 1000 analyst
COPY --from=build /opt/mvt /opt/mvt
USER analyst
# Downloaded IOC files are kept here (a named volume in compose.yml).
RUN mkdir -p /home/analyst/.local/share/mvt
WORKDIR /case
CMD ["mvt-ios", "--help"]
