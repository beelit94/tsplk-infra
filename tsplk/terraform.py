import subprocess
import os
import json
import paramiko
import time

import yaml
from scp import SCPClient, SCPException

minion_roles_map_file = 'minion_roles_map'


class Terraform:
    def __init__(self):
        pass

    def apply(self, targets, variables, state):
        parameters = []
        parameters += self.generate_targes(targets)
        parameters += self.generate_var_string(variables)
        parameters = ['terraform', 'apply', '-state=%s' % state] + parameters
        subprocess.call(parameters)

    def destroy(self, targets, variables, state):
        parameters = []
        parameters += self.generate_targes(targets)
        parameters += self.generate_var_string(variables)
        parameters = ['terraform', 'destroy', '-force', '-state=%s' % state] + parameters
        subprocess.call(parameters)

    def read_tfstate(self, f_path):
        if os.path.exists(f_path):
            with open(f_path) as f:
                json_data = json.load(f)
            return json_data

        return None

    def generate_var_string(self, d):
        str_t = []
        for k, v in d.iteritems():
            str_t += ['-var'] + ["%s=%s" % (k, v)]

        return str_t

    def generate_targes(self, targets):
        str_t = []
        for t in targets:
            str_t += ['-target=%s' % t]
        return str_t


class TerraformSaltMaster:
    def __init__(self, variables):

        self.variables = variables
        self.variables['ubuntu_saltmaster_count'] = 1
        self.targets = ['aws_instance.ubuntu-salt-master']
        self.terraform = Terraform()
        self.master_state_file = 'salt_master_state'
        self.data = self.terraform.read_tfstate(self.master_state_file)
        self.minion_info_remote_path = 'terraform.tfstate'
        self.minion_info_local_path = 'remote_state'

    def up(self):
        self.terraform.apply(self.targets, self.variables, self.master_state_file)
        self._read_master_status()

    def destroy(self):
        self.destroy_minion()
        time.sleep(3)
        self.terraform.destroy([], self.variables, self.master_state_file)
        if os.path.exists(self.minion_info_local_path):
            os.remove(self.minion_info_local_path)
        self._read_master_status()

    def ssh_connect(self):
        ssh = paramiko.SSHClient()
        # no known_hosts error
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # no passwd needed
        k = paramiko.RSAKey.from_private_key_file(self.variables['key_path'])
        ssh.connect(self.get_public_ip(), username='ubuntu', pkey=k)
        return ssh

    def plan_minions(self):
        ssh = self.ssh_connect()

        new_dict = self.update_minion_variables()
        gen_list = self.terraform.generate_var_string(new_dict)
        cmd_str = './terraform/terraform plan ' + ' '.join(gen_list)

        self.ssh_execute_and_close(cmd_str, ssh)

    def ssh_execute_and_close(self, cmd_str, ssh):
        stdin, stdout, stderr = ssh.exec_command(cmd_str)
        out = stdout.read()
        err = stderr.read()
        print(out)
        print(err)
        ssh.close()
        return out, err

    def update_minion_variables(self):
        minion_variables = {k: v for k, v in self.variables.items()}
        minion_variables['key_path'] = minion_variables['key_name']
        minion_variables['ubuntu_saltmaster_count'] = 0
        minion_variables['salt_master_ip'] = self.get_private_ip()
        minion_variables.pop('roles_count')
        minion_variables.pop('splunk_architecture')
        return minion_variables

    def apply_minions(self):
        minion_variables = self.update_minion_variables()

        with open('minion_terraform_variables', 'w') as f:
            json.dump(minion_variables, f)

        ssh = self.ssh_connect()

        with SCPClient(ssh.get_transport()) as scp:
            scp.put('minion_terraform_variables', remote_path='minion_terraform_variables')

        cmd_str = 'nohup python deploy_minion.py > tsplk.log 2>&1 &'

        self.ssh_execute_and_close(cmd_str, ssh)

    def destroy_minion(self):
        ssh = self.ssh_connect()
        new_dict = self.update_minion_variables()
        gen_list = self.terraform.generate_var_string(new_dict)
        cmd_str = './terraform/terraform destroy --force ' + ' '.join(gen_list)
        self.ssh_execute_and_close(cmd_str, ssh)

    def get_minions_info(self):
        if not os.path.exists(self.minion_info_local_path):
            sshcon = self.ssh_connect()

            try:
                with SCPClient(sshcon.get_transport()) as scp:
                    scp.get(remote_path=self.minion_info_remote_path,
                            local_path=self.minion_info_local_path)
                    scp.get(remote_path=minion_roles_map_file,
                            local_path=minion_roles_map_file)
            except SCPException:
                print('minions are not ready yet')

            sshcon.close()

        with open(self.minion_info_local_path) as f:
            remote_data = json.load(f)

        with open(minion_roles_map_file) as f:
            minion_roles_map = yaml.load(f)

        instances = []
        for k, v in remote_data['modules'][0]['resources'].iteritems():
            if 'aws_instance' in k:
                instances.append({'name': k,
                                  'info': v['primary']['attributes'],
                                  'role': minion_roles_map[k]})

        return instances

    def get_public_ip(self):
        public_ip = self.data['modules'][0]['outputs']['salt-master-public-ip']
        return public_ip

    def get_private_ip(self):
        private_ip = self.data['modules'][0]['outputs']['salt-master-private-ip']
        return private_ip

    def _read_master_status(self):
        self.data = self.terraform.read_tfstate(self.master_state_file)
