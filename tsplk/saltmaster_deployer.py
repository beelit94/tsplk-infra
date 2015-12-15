from terraform import Terraform
import paramiko
from scp import SCPClient, SCPException
import os
import yaml
import logging
import json

minion_info_remote_path = 'minion_info'
minion_info_local_path = 'remote_state'

log = logging.getLogger()


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
        """
        This function takes time, suggest store the value instead of
        re-calling it if you know your status is still the same
        :return:
        """
        return self.tf.is_any_aws_instance_alive()

    def is_minions_up(self):
        if not self.is_master_up():
            log.debug('master is not up')
            return False

        ssh = self._ssh_connect()

        cmd = 'cat terraform.tfstate'
        stdin, stdout, stderr = \
            ssh.exec_command(cmd)

        out = stdout.read()
        err = stderr.read()
        ret_code = stdout.channel.recv_exit_status()
        data = json.loads(out)
        ssh.close()

        log.debug('cmd: ' + cmd)
        log.debug('out: ' + out)
        if ret_code != 0:
            log.debug('err: ' + err)
            return False

        if data is None:
            log.error('responsed data is not in json format!')
            log.error('data : ' + data)
            return False

        try:
            resources = data['modules'][0]['resources']
            for k, v in resources.iteritems():
                if 'aws_instance' in k:
                    log.debug(k + ' is up')
                    return True
        except KeyError as err:
            log.debug(err)
            return False
        finally:
            ssh.close()

    def up_master(self):
        """
        raise EnvironmentError if up is fail
        :return: nothing
        """
        if self.is_master_up():
            log.debug('master is already up')
            return
        ret_code, out, err = self.tf.apply()
        if ret_code != 0:
            raise EnvironmentError(out + err)

    def up_minion(self):
        if not self.is_master_up():
            return

        self.minion_variables['salt_master_ip'] = self._get_private_ip()

        vars_string = ''
        for key, value in self.minion_variables.items():
            vars_string += '--tfvar' + ' %s=%s ' % (key, value)

        vars_string += ' --hipchat_token=%s' % \
                       self.minion_variables['hipchat_token']

        # use tf var to pass variable value
        cmd_str = 'nohup sudo python saltminion_deployer.py up %s > ' \
                  'tsplk.log 2>&1 &' % vars_string

        ssh = self._ssh_connect()
        stdin, stdout, stderr = ssh.exec_command(cmd_str)
        out = stdout.read()
        err = stderr.read()
        ret_code = stdout.channel.recv_exit_status()
        log.debug(out)
        log.debug(err)
        ssh.close()
        if ret_code != 0:
            raise EnvironmentError(out + err)

    def up(self):
        is_minion_up = self.is_minions_up()
        is_master_up = self.is_master_up()

        if is_minion_up:
            return

        if is_master_up and not is_minion_up:
            self.up_minion()
            return

        self.up_master()
        self.up_minion()

    def destroy(self):
        if not self.is_master_up():
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

    def destroy_minion(self):
        if not self.is_master_up():
            return

        if not self.is_minions_up():
            return

        ssh = self._ssh_connect()

        vars_string = ''
        for key, value in self.minion_variables.items():
            vars_string += '--tfvar' + ' %s=%s ' % (key, value)
        cmd = 'sudo python saltminion_deployer.py destroy %s' % vars_string
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read()
        err = stderr.read()

        log.debug('cmd: ' + cmd)
        log.debug('out: ' + out)

        ret_code = stdout.channel.recv_exit_status()
        ssh.close()

        if ret_code != 0:
            log.debug('err: ' + err)
            raise EnvironmentError(err)

        if os.path.exists(minion_info_local_path):
            os.remove(minion_info_local_path)

    def get_minions_info(self):
        """

        :return: in dict
        """
        if not self.is_minions_up():
            return None

        ssh = self._ssh_connect()
        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_path=minion_info_remote_path,
                        local_path=minion_info_local_path)
        except SCPException:
            # todo logging
            print('minions are not ready yet')
            return None
        finally:
            ssh.close()

        with open(minion_info_local_path) as f:
            instances = yaml.load(f)

        return instances

    def get_public_ip(self):
        if not self.is_master_up():
            return None
        public_ip = self.tf.get_output_value('salt-master-public-ip')
        return public_ip

    def _get_private_ip(self):
        private_ip = self.tf.get_output_value('salt-master-private-ip')
        return private_ip
