FROM registry.ipol.im/ipol-debian

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --locked

# needed since the DR raises exception when this is not defined
# this is probably a bug
ENV VIRTUAL_ENV=

# give all permissions to /home/ipol in case a demo has to use ~/.cache or something else
RUN mkdir -p /home/ipol && chmod -R 777 /home/ipol

# to build:
# DOCKER_BUILDKIT=1 docker build ipol_demo/modules/demorunner -t registry.ipol.im/ipol-debian-demorunner
# docker push
