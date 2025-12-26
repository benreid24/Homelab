Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.disk :disk, size: "150GB", primary: true

  config.vm.hostname = "localdev.benanna.club"
  config.hostsupdater.aliases = [
    "immich.localdev.benanna.club",
    "seafile.localdev.benanna.club",
    "ha.localdev.benanna.club",
    "omada.localdev.benanna.club",
    "dns.localdev.benanna.club",
    "code.localdev.benanna.club",
    "kuma.localdev.benanna.club",
    "snapcast.localdev.benanna.club"
  ]

  # Private network so Ansible can SSH
  config.vm.network "private_network", ip: "192.168.56.10"

  # Public network (bridged) with static IP - makes VM accessible on your LAN
  config.vm.network "public_network", ip: "192.168.0.250", bridge: "Default Switch"

  
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 8192
    vb.cpus = 4
  end

  # Run Ansible after VM is up
  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "ansible/playbooks/homelab.yml"
    ansible.inventory_path = "ansible/inventory/homelab.yml"
    ansible.limit = "vagrant"
    ansible.vault_password_file = "vault_pass.sh"
    ansible.become = true
  end

end
