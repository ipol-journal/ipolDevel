FROM debian:bullseye

COPY . /w
RUN cd /w && bash install_dist_packages.sh && rm -rf /var/lib/apt/lists/* && cd && rm -r /w

# to build:
# DOCKER_BUILDKIT=1 docker build sysadmin/install_packages/ -t registry.ipol.im/ipol-debian
# docker push
