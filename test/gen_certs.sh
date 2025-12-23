#!/bin/bash

CERT_PATH=ansible/playbooks/roles/services/files/services/Nginx/dev-certs

mkcert -install
mkcert homelab.lan "*.homelab.lan"
mkdir $CERT_PATH
mv "homelab.lan+1.pem" $CERT_PATH/fullchain.pem
mv "homelab.lan+1-key.pem" $CERT_PATH/privkey.pem
