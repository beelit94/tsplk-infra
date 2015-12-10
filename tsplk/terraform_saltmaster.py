from terraform import Terraform
import paramiko
from scp import SCPClient, SCPException
import json
import os
import time
import yaml

minion_roles_map_file = 'minion_roles_map'
minion_info_remote_path = 'terraform.tfstate'
minion_info_local_path = 'remote_state'

# todo use logging instead of print


class TerraformSaltMaster:
    def __init__(self, master_variables, minion_variables):

        self.minion_variables = minion_variables
        self.master_variables = master_variables
        self.master_variables['ubuntu_saltmaster_count'] = 1

        self.tf = Terraform(
            targets=['aws_instance.ubuntu-salt-master'],
            state='salt_master_state',
            variables=self.master_variables
        )

    def is_master_up(self):
        return self.tf.is_any_aws_instance_alive()

    def is_minions_up(self):
        if not self.is_master_up():
            return False

        ssh = self._ssh_connect()

        if os.path.exists(minion_info_local_path):
            return True

        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_path=minion_info_remote_path,
                        local_path=minion_info_local_path)
                scp.get(remote_path=minion_roles_map_file,
                        local_path=minion_roles_map_file)

            return True
        except SCPException:
            return False
        finally:
            ssh.close()

    def up_master(self):
        """
        raise EnvironmentError if up is fail
        :return: nothing
        """
        if self.is_master_up():
            print('master is already up')
            return
        ret_code, out, err = self.tf.apply()
        if ret_code != 0:
            raise EnvironmentError(out + err)

    def up_minion(self):
        if not self.is_master_up():
            return

        vars_string = ''
        for key, value in self.minion_variables:
            vars_string += '-tfvar ' + '%s=%s' % (key, value)

        # use tf var to pass variable value
        cmd_str = 'nohup python terraform_saltminion.py up %s > ' \
                  'tsplk.log 2>&1 &' % vars_string

        ssh = self._ssh_connect()
        stdin, stdout, stderr = ssh.exec_command(cmd_str)
        ret_code = stdout.channel.recv_exit_status()
        ssh.close()
        if ret_code != 0:
            raise EnvironmentError(stdout + stderr)

    def up(self):
        if self.is_minions_up():
            return

        if self.is_master_up() and not self.is_minions_up():
            self.up_minion()
            return

        self.up_master()
        self.up_minion()

    def destroy(self):
        if self.is_master_up():
            return
        self.destroy_minion()
        self.destroy_master()

    def destroy_master(self):
        # don't know why yet, but assign targets here will cause terraform
        # won't teardown master
        self.tf.destroy(targets=[])

    def _ssh_connect(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        k = paramiko.RSAKey.from_private_key_file(self.master_variables['key_path'])
        # todo user name should same as saltmaster username
        # here we hard code first
        ssh.connect(self.get_public_ip(), username='ubuntu', pkey=k)
        return ssh

    # def update_minion_variables(self):
    #     minion_variables = {k: v for k, v in self.variables.items()}
    #     minion_variables['key_path'] = minion_variables['key_name']
    #     minion_variables['ubuntu_saltmaster_count'] = 0
    #     minion_variables['salt_master_ip'] = self.get_private_ip()
    #     minion_variables.pop('roles_count')
    #     minion_variables.pop('splunk_architecture')
    #     return minion_variables

    # def apply_minions(self):
    #     minion_variables = self.update_minion_variables()
    #
    #     with open('minion_terraform_variables', 'w') as f:
    #         json.dump(minion_variables, f)
    #
    #     ssh = self._ssh_connect()
    #
    #     with SCPClient(ssh.get_transport()) as scp:
    #         scp.put('minion_terraform_variables', remote_path='minion_terraform_variables')
    #
    #     cmd_str = 'nohup python terraform_saltminion.py > tsplk.log 2>&1 &'
    #
    #     self.ssh_execute_and_close(cmd_str, ssh)

    def destroy_minion(self):
        if not self.is_master_up():
            return

        if not self.is_minions_up():
            return

        ssh = self._ssh_connect()
        cmd = 'python terraform_saltminion.py destroy'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        ret_code = stdout.channel.recv_exit_status()
        if ret_code != 0:
            raise EnvironmentError()

        if os.path.exists(minion_info_local_path):
            os.remove(minion_info_local_path)

    def get_minions_info(self):
        if not self.is_minions_up():
            return

        if not os.path.exists(minion_info_local_path):
            sshcon = self._ssh_connect()

            try:
                with SCPClient(sshcon.get_transport()) as scp:
                    scp.get(remote_path=minion_info_remote_path,
                            local_path=minion_info_local_path)
            except SCPException:
                print('minions are not ready yet')

            sshcon.close()

        with open(minion_info_local_path) as f:
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
        if not self.is_master_up():
            return None
        public_ip = self.tf.get_output_value('salt-master-public-ip')
        return public_ip

    def _get_private_ip(self):
        private_ip = self.tf.get_output_value('salt-master-private-ip')
        return private_ip
