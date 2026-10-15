# sigma-cli with the Elasticsearch/Lucene backend (Graylog uses Lucene syntax) and the Windows/Sysmon
# pipelines, versions pinned. ATT&CK/D3FEND data is cached at build time so it works offline. make is included so a detections repo's Makefile gate runs unchanged.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 1000 analyst
RUN pip install "sigma-cli==3.1.0" "pySigma==1.5.1" "pySigma-backend-elasticsearch==2.1.1" \
                "pySigma-pipeline-windows==2.0.1" "pySigma-pipeline-sysmon==2.0.0"
USER analyst
# The container runs with no network: cache MITRE ATT&CK and D3FEND data now (sigma check's tag validators).
# Rebuild the image to refresh it: ./soc build sigma
RUN python -c "from sigma.data import mitre_attack, mitre_d3fend; mitre_attack._load_mitre_attack_data(); mitre_d3fend._load_mitre_d3fend_data()"
WORKDIR /case
ENTRYPOINT ["sigma"]
CMD ["--help"]
