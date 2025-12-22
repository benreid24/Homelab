Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"

  config.vm.hostname = "ansible-test"

  # Private network so Ansible can SSH
  config.vm.network "private_network", ip: "192.168.56.10"

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
