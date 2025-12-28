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

Required vault contents:
```
admin_email: {your email}

redbot_discord_token: {Discord API token}

seafile_db_password: {something secure}
seafile_admin_password: {something secure}
seafile_docker_password: {something secure}

immich_db_password: {something secure}
immich_admin_password: {something secure}

cloudflare_ddns_api_token: {token with DNS edit scope}
cloudflare_dns_api_token: {token with DNS edit & zone edit scope}
cloudflare_zone_ids: {list of ids of the domain zones to manage}

smb_username: {username for SMB NAS}
smb_password: {password for SMB NAS}

borg_backup_passphrase: {something secure}
restic_backup_passphrase: {something secure}

spotify_username: {your username}
spotify_password: {base64 encoded API token, run the librespot container interactively to acquire via oauth}

adguard_password_hash: {hash for existing admin user. go through first time setup to acquire}

komo_db_password: {something secure}
komodo_passkey: {something secure}

fuse_music_path: {path to your music folder in seafile-fuse}
```

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

### TP-Link Omada

If device adoption or migration fails you may need to set the network mode to host (or do a better job determining which ports adoption uses) until the devices are properly linked.
