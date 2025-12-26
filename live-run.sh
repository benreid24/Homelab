#!/bin/bash

sudo ansible-playbook --connection=local --limit localhost -i ansible/inventory/homelab.yml --vault-password-file=./vault_pass.sh ./ansible/playbooks/homelab.yml
