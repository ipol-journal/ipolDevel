FROM registry.ipol.im/ipol-debian

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && rm requirements.txt

# needed since the DR raises exception when this is not defined
# this is probably a bug
ENV VIRTUAL_ENV=

# give all permissions to /home/ipol in case a demo has to use ~/.cache or something else
RUN mkdir -p /home/ipol && chmod -R 777 /home/ipol

# to build:
# DOCKER_BUILDKIT=1 docker build ipol_demo/modules/demorunner -t registry.ipol.im/ipol-debian-demorunner
# docker push
CMD ["/bin/bash", "-c", "uvicorn demorunner:app --host 0.0.0.0 --port 8000"]
