# Homelab

Ansible playbooks for provisioning my home server.

## Development

To edit the vault: `ansible-vault edit ansible/vars/vault.yml --vault-password-file=vault_pass.sh` (Put the password in `.vault_pass`)

## Testing

Testing is done using Vagrant with the guest_ansible plugin. Install with `vagrant plugin install vagrant-guest_ansible`

To provision a VM: `vagrant up`

Run Ansible manually in the VM:
1. `cd /vagrant`
2. `ansible-playbook --connection=local --limit vagrant -i ansible/inventory/homelab.yml --vault-password-file=/vagrant/vault_pass.sh ./ansible/playbooks/homelab.yml`
