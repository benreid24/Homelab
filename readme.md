# Homelab

Ansible playbooks for provisioning my home server.

## Testing

Testing is done using Vagrant with the guest_ansible plugin. Install with `vagrant plugin install vagrant-guest_ansible`

To provision a VM: `vagrant up`

Run Ansible manually in the VM:
1. `cd /vagrant`
2. `ansible-playbook --connection=local -i ansible/inventory/homelab.yml ./ansible/playbooks/homelab.yml`
