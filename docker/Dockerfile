ARG PYTHON_IMAGE=library/python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/sipre/backend \
    TZ=UTC
WORKDIR /srv/sipre
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock \
    && groupadd --gid 10001 sipre \
    && useradd --uid 10001 --gid sipre --no-create-home sipre
COPY backend/app ./backend/app
COPY database ./database
USER sipre
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM runtime AS test
USER root
COPY requirements-dev.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements-dev.lock
COPY . .
USER sipre
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider", "-q"]
