FROM debian:stable

ENV home /home/ipol
ENV ipolDevel ~/ipolDevel
ENV host docker

# ipol user config
RUN useradd -ms /bin/zsh ipol
RUN adduser ipol sudo
RUN echo 'ipol:ipol' | chpasswd

WORKDIR /home/ipol

# Apt and pip packages installation
COPY ./docker/pkglist /home/ipol/pkglist
RUN apt update && apt install -y $(cat pkglist)

COPY ./sysadmin/install_packages/requirements.txt /home/ipol/requirements.txt
RUN pip install -r requirements.txt

COPY ./ipol_webapp/requirements.txt /home/ipol/cp_requirements.txt
RUN pip install -r cp_requirements.txt

COPY ./sysadmin/install_packages/pip3-requirements.txt /home/ipol/pip3-requirements.txt
RUN pip3 install -r pip3-requirements.txt

RUN pip install opencv-python

COPY ./docker/zsh_conf /home/ipol/zsh_conf

# Nginx config file generation
COPY ./sysadmin/configs/nginx/default-local /etc/nginx/sites-available/default
RUN sed -i 's@miguel@ipol@g' /etc/nginx/sites-available/default

# Libtiff bugfix
RUN python -c 'import libtiff'

RUN bash -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    cp /home/ipol/zsh_conf /root/.zshrc

USER ipol
RUN bash -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    cp /home/ipol/zsh_conf ~/.zshrc

COPY ./ipol_demo/modules/config_common/authorized_patterns.conf.sample ~/ipolDevel/modules/config_common/authorized_patterns.conf

RUN ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -q -N ""  && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && chmod og-wx ~/.ssh/authorized_keys
USER root


EXPOSE 80
EXPOSE 22

ENTRYPOINT service ssh start && nginx && zsh