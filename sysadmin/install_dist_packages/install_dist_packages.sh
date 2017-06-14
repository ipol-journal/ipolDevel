#!/bin/bash
while IFS='' read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^#.*$ ]] && continue
    echo "$line"
    sudo apt-get -y install "$line"
done < "apt-get_requirements.txt"