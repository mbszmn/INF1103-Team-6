# syntax=docker/dockerfile:1

# python and the app packages, shared by the two stages below
FROM python:3.13-slim AS python-deps
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

# test image: adds pytest and the other dev tools, then runs every test file
FROM python-deps AS test
COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
CMD ["python", "-m", "pytest"]

# app image (default target): runs as a normal user, tickets live in a volume
FROM python-deps AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="AI SIT Helpdesk Ticket Triage System" \
      org.opencontainers.image.description="INF1103 Team 6 helpdesk ticket triage app" \
      org.opencontainers.image.source="https://github.com/mbszmn/INF1103-Team-6" \
      org.opencontainers.image.version="${APP_VERSION}"
ENV APP_VERSION=${APP_VERSION} \
    HELPDESK_DATA_DIR=/app/data
RUN useradd --create-home --uid 10001 helpdesk
COPY . .
# the data folder must be writable, a read only folder on the build machine (OneDrive does this)
# would otherwise stop tickets and the log from being saved
RUN mkdir -p /app/data && chown -R helpdesk:helpdesk /app/data && chmod -R u+rwX /app/data
USER helpdesk
VOLUME ["/app/data"]
CMD ["python", "main.py"]
