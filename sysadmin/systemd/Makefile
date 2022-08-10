all:
	mkdir -p ${HOME}/.config/systemd/
	rm ${HOME}/.config/systemd/user || true
	ln -s $(shell pwd)/$(shell hostname) ${HOME}/.config/systemd/user
	systemctl --user daemon-reload

restart: all
	systemctl --user restart ipol-'*' --all
