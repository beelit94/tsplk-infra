import subprocess
import json
import yaml
import pycurl
import time
import click
import re
from terraform import Terraform
import salt.client
import logging
import sys

log = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

# todo solution for this after push to other team
hipchat_user_map = {
    'ftan': 'FreddyTan',
    'swang': 'SunnyWanYingWang',
    'clin': 'WytheLin',
    'hou': 'HenryOu',
    'chuang': 'CamilleHuang'
}

try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

minion_info_path = 'terraform.tfstate'
project_setting_file = 'settings.yml'
terraform_variables = 'minion_terraform_variables'
minion_info_file = 'minion_info'


class TerraformSaltMinion(Terraform):
    def generate_minion_info(self):
        pass

    @staticmethod
    def retry_minion(local, minion, command, args):
        retry_count = 5
        for i in range(0, retry_count):
            result = local.cmd(minion, command, args)
            if result:
                return result
            time.sleep(1)
            log.debug('%s is not ready, retry...' % minion)

        raise EnvironmentError("Can't connect to %s" % minion)

    def assign_roles(self, roles):
        '''
        :param roles: ex. roles = {'role1': count1, 'role2': count2}
        :param instances:
        :return:
        '''
        instances = self.get_aws_instances()
        instances_list = []
        for name, info in instances.items():
            instances_list.append({'name': name,
                                   'info': info['primary']['attributes']})

        total = 0
        for role, count in roles.iteritems():
            total += count

        assert total == len(instances), 'instance is not fully up, ' \
                                        'check tsplk.log'

        minion_info = []
        for role, count in roles.iteritems():
            ready_to_assign = instances_list[:count]
            instances_list = instances_list[count:]

            for minion in ready_to_assign:
                minion_id = minion['info']['tags.Name']
                local = salt.client.LocalClient()
                result = self.retry_minion(
                    local, minion_id, 'grains.get', ['host'])

                host = result[minion_id]

                local.cmd(minion_id, 'grains.append', ['role', role])

                minion_info.append({'host': host,
                                    'role': role,
                                    'minion_id': str(minion_id),
                                    'ip': str(minion['info']['public_ip']),
                                    })

        with open(minion_info_file, 'w') as f:
            yaml.dump(minion_info, f, default_flow_style=False)

    def run_orchestration(self, splunk_architecture):
        local = salt.client.LocalClient()
        local.cmd('*', 'saltutil.sync_all', [])
        subprocess.call("sudo salt-run state.orch orchestration.%s"
                        % splunk_architecture, shell=True)

    def notify_when_finished(self, user, project_name, token):
        room = '1957'
        c = pycurl.Curl()
        c.setopt(c.URL,
                 'https://hipchat.splunk.com/v2/room/%s/notification?'
                 'auth_token=%s' % (room, token))

        try:
            hipchat_user = hipchat_user_map[user]
        except KeyError:
            hipchat_user = user

        post_data = {'color': 'random',
                     'message_format': 'text',
                     'message': '@%s, project %s is ready' %
                                (hipchat_user, project_name),
                     'notify': True
                     }

        postfields = urlencode(post_data)
        c.setopt(c.POSTFIELDS, postfields)
        c.perform()
        c.close()


def read_project_setting_data():
    with open(project_setting_file) as f:
        data = yaml.load(f)

    return data


def read_terraform_variables():
    with open(terraform_variables) as f:
        gs = json.load(f)
    return gs


@click.command()
@click.option('--tfvar', '-t', multiple=True)
@click.option('--hipchat_token', '-h')
def up(tfvar, hipchat_token):
    minion_tf_variables = dict()
    for v in tfvar:
        rex = r'^(?P<key>.*)=(?P<value>.*)$'
        result = re.match(rex, v)
        minion_tf_variables.update({result.group('key'): result.group('value')})

    tf = TerraformSaltMinion(variables=minion_tf_variables)
    ret_code, out, err = tf.apply()
    log.debug(out)
    log.debug(err)
    if ret_code != 0:
        exit(1)

    prj_settings = read_project_setting_data()
    tf.assign_roles(prj_settings['roles_count'])

    tf.run_orchestration(prj_settings['splunk_architecture'])

    tf.notify_when_finished(
        minion_tf_variables['username'],
        prj_settings['project_name'], hipchat_token)


@click.command()
@click.option('--tfvar', '-t', multiple=True)
def destroy(tfvar):
    minion_tf_variables = dict()
    for v in tfvar:
        rex = r'^(?P<key>.*)=(?P<value>.*)$'
        result = re.match(rex, v)
        minion_tf_variables.update({result.group('key'): result.group('value')})

    tf = TerraformSaltMinion(variables=minion_tf_variables)
    ret_code, out, err = tf.destroy()
    log.debug(out)
    log.debug(err)
    if ret_code != 0:
        exit(1)


@click.command()
def is_up():
    minion = TerraformSaltMinion()
    minion.read_state()
    click.echo(str(minion.is_any_aws_instance_alive()))


@click.group()
def main():
    pass

main.add_command(up)
main.add_command(destroy)
main.add_command(is_up)

if __name__ == '__main__':
    main()


