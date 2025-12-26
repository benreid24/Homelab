#!/bin/bash

sudo ansible-playbook --connection=local --limit vagrant -i ansible/inventory/homelab.yml --vault-password-file=/vagrant/vault_pass.sh ./ansible/playbooks/homelab.yml
