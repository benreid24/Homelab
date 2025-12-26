# Homelab

Ansible playbooks for provisioning my home server.

## Development

### Prerequisites

- Vagrant
- Vagrant Hosts Plugin: `vagrant plugin install vagrant-hostsupdater`
  - Need to disable DNS over HTTPS
  - May need to manually edit `/etc/hosts` (or `/c/windows/system32/drivers/etc/hosts`) anyways

### Vault Editing

To edit the vault: `ansible-vault edit ansible/vars/vault.yml --vault-password-file=vault_pass.sh` (Put the password in `.vault_pass`)

## Testing

To provision a VM: `vagrant up`

Run Ansible manually in the VM:
1. `cd /vagrant`
2. `sudo ansible-playbook --connection=local --limit vagrant -i ansible/inventory/homelab.yml --vault-password-file=/vagrant/vault_pass.sh ./ansible/playbooks/homelab.yml`

## Running

On the target machine:
1. Install Ansible: `sudo apt install -y ansible`
2. Place the vault password in `.vault_pass` with permission 600
3. Run Ansible: `sudo ansible-playbook --connection=local --limit localhost -i ansible/inventory/homelab.yml --vault-password-file=./vault_pass.sh ./ansible/playbooks/homelab.yml`
