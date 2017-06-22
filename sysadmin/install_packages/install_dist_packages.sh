#!/bin/bash

apt-get update

while IFS='' read -r line || [[ -n "$line" ]]; do
    # Remove commented lines
    [[ "$line" =~ ^#.*$ ]] && continue
    # Remove lines with spaces
    [[ "$line" =~ ^' '*$ ]] && continue
    # Remove empty lines
    [[ "$line" == '' ]] && continue
    sudo apt-get -y install "$line"
done < "apt-get_requirements.txt"
