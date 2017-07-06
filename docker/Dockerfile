FROM ubuntu:16.04

ENV home /home/ipol
ENV ipolDevel ~/ipolDevel
ENV host docker

# ipol user config
RUN useradd -ms /bin/bash ipol
RUN adduser ipol sudo
RUN echo 'ipol:ipol' | chpasswd

WORKDIR /home/ipol

# Apt and pip packages installation
COPY ./docker/pkglist /home/ipol/pkglist
COPY ./sysadmin/install_packages/requirements.txt /home/ipol/requirements.txt

RUN apt update && apt install -y $(cat pkglist)
RUN pip install -r requirements.txt

# Nginx config file generation
COPY ./sysadmin/configs/nginx/default-local /etc/nginx/sites-available/default
COPY ./docker/nginx_clientApp_location /home/ipol/nginx_clientApp_location
RUN sed -i 's@miguel@ipol@g' /etc/nginx/sites-available/default && sed -i '/ipol;/r nginx_clientApp_location' /etc/nginx/sites-available/default

# Libtiff bugfix
RUN python -c 'import libtiff'

USER ipol
RUN ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -q -N ""  && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && chmod og-wx ~/.ssh/authorized_keys
USER root


EXPOSE 80
EXPOSE 22

ENTRYPOINT service ssh start && bash
