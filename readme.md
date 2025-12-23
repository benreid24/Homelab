# Homelab

Ansible playbooks for provisioning my home server.

## Development

### Prerequisites

- Vagrant
- Vagrant Hosts Plugin: `vagrant plugin install vagrant-hostsupdater`
  - Need to disable DNS over HTTPS
  - May need to manually edit `/etc/hosts` (or `/c/windows/system32/drivers/etc/hosts`) anyways
- mkcert: https://github.com/FiloSottile/mkcert
  - Setup local CA: `mkcert -install`
  - Create certificates: `mkcert homelab.lan "*.homelab.lan"`

### Vault Editing

To edit the vault: `ansible-vault edit ansible/vars/vault.yml --vault-password-file=vault_pass.sh` (Put the password in `.vault_pass`)

## Testing

To provision a VM: `vagrant up`

Run Ansible manually in the VM:
1. `cd /vagrant`
2. `ansible-playbook --connection=local --limit vagrant -i ansible/inventory/homelab.yml --vault-password-file=/vagrant/vault_pass.sh ./ansible/playbooks/homelab.yml`
