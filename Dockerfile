# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3

########################################################################
# Base stage -- update pip
########################################################################
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Update pip
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip

########################################################################
# Build stage -- build FORD wheels for installation in install stage
########################################################################
FROM base as build
WORKDIR /build

# FORD installation requires git in order to get version info
RUN apt-get update && apt-get --no-install-recommends install -y git

# Copy FORD source in
COPY . .

# Build FORD wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip wheel --wheel-dir=/wheels .


########################################################################
# Install stage -- install FORD from wheels
########################################################################
FROM base as install

# Download dependencies as separate steps to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.

# Install graphviz
RUN apt-get update && apt-get --no-install-recommends install -y graphviz

# Install FORD dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,from=build,source=/wheels,target=/wheels \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --find-links=/wheels -r requirements.txt

# Install FORD from wheels built in build stage
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,from=build,source=/wheels,target=/wheels \
    python -m pip install --no-index --find-links=/wheels ford

# Run the application.
CMD ["/usr/local/bin/ford"]
