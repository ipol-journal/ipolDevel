FROM registry.ipol.im/ipol-debian

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && rm requirements.txt

# needed since the DR raises exception when this is not defined
# this is probably a bug
ENV VIRTUAL_ENV=

# to build:
# DOCKER_BUILDKIT=1 docker build ipol_demo/modules/demorunner -t registry.ipol.im/ipol-debian-demorunner
# docker push
