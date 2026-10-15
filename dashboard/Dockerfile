FROM python:3.13-alpine
WORKDIR /app
COPY server.py /app/server.py
COPY static /app/static
# Readable by the unprivileged runtime user regardless of host checkout permissions.
RUN chmod -R a+rX /app
USER 65534:65534
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "/app/server.py"]
