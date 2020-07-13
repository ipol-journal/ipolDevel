FROM debian:latest

# ipol user config
RUN useradd -ms /bin/zsh ipol
RUN adduser ipol sudo
RUN echo 'ipol:ipol' | chpasswd

WORKDIR /home/ipol

# Apt and pip packages installation
COPY ./docker/pkglist /home/ipol/pkglist
RUN apt update && apt install -y $(cat pkglist)

RUN pip install virtualenv && pip3 install requests virtualenv ipython

COPY ./docker/zsh_conf /home/ipol/zsh_conf

# Nginx config file generation
COPY ./sysadmin/configs/nginx/default-local /etc/nginx/sites-available/default
RUN sed -i 's@miguel@ipol@g' /etc/nginx/sites-available/default

USER ipol
RUN bash -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    cp /home/ipol/zsh_conf ~/.zshrc

COPY ./ipol_demo/modules/config_common/authorized_patterns.conf.sample ~/ipolDevel/modules/config_common/authorized_patterns.conf

RUN ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -q -N ""  && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && chmod og-wx ~/.ssh/authorized_keys
USER root

EXPOSE 80

ENTRYPOINT service ssh start && service bind9 start && nginx && zsh