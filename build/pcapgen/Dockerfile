# pcapgen: build small, known-content test PCAPs with Scapy (full TCP handshakes, so Snort stream
# reassembly and flow:established rules behave as on the wire). No network access needed.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install "scapy==2.7.0" && useradd -m -u 1000 analyst
COPY pcapgen.py /usr/local/bin/pcapgen
RUN chmod 755 /usr/local/bin/pcapgen
USER analyst
WORKDIR /case
ENTRYPOINT ["pcapgen"]
CMD ["--help"]
