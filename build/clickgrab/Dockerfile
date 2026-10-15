# ClickGrab: CLI analyzer (default entrypoint) and Streamlit web UI (compose overrides the entrypoint).
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd -m -u 1000 app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# The Streamlit app writes temp_reports/ and the gist cache under analysis/ in its working folder.
RUN mkdir -p reports temp_reports analysis && chown -R app:app /app
USER app
EXPOSE 8501
ENTRYPOINT ["python", "clickgrab.py"]
