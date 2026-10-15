# Volatility 3 from the local source copy, plus the optional plugin dependencies (YARA, capstone, pycryptodome); cloud and LeechCore extras are skipped.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd -m -u 1000 analyst
COPY . /tmp/volatility3
RUN pip install /tmp/volatility3 "yara-python>=4.5" "capstone>=5" pycryptodome && rm -rf /tmp/volatility3
USER analyst
# Symbol tables downloaded from Microsoft are cached here (a named volume in compose.yml).
RUN mkdir -p /home/analyst/.cache/volatility3
WORKDIR /case
ENTRYPOINT ["vol"]
CMD ["-h"]
