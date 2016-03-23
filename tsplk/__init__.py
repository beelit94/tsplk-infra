import os
import shutil
import string

import click
import keyring
import yaml
from collections import OrderedDict
import requests
import logging
from requests.exceptions import MissingSchema
from Crypto.PublicKey import RSA
import random

log = logging.getLogger()
working_folder_name = ".tsplk"
project_root = os.path.join(os.path.expanduser('~'), working_folder_name)
setting_filename = 'settings.yml'
ssh_private_key_name = 'id_rsa'
sync_folder = 'sync_to_file_base'

global_stetting_list = OrderedDict({
    'aws_access_key': {
        'prompt_question': 'Please enter AWS access key ID'
    },

    'aws_secret_key': {
        'prompt_question': 'Please enter secret key'
    },

    'username': {
        'prompt_question': 'Please enter your employee account'
                           '(make sure you get it right, hipchat will use '
                           'this account to inform you when your environment ready)'
    }
})

platform_count = [
    'ubuntu_1404_count',
    'windows_2008_r2_count',
    'windows_2012_r2_count'
]


def ch_project_folder(project_name):
    os.chdir(os.path.join(project_root, project_name))


class GlobalSetting:
    def __init__(self):
        pass

    @staticmethod
    def get_value(key):
        return keyring.get_password('system', key)

    @staticmethod
    def set_value(key, value):
        return keyring.set_password('system', key, value)

    @staticmethod
    def read_data():
        data = dict()
        for key in global_stetting_list:
            value = keyring.get_password('system', key)
            data.update({key: value})

        return data

    @staticmethod
    def is_setting_missed():
        for key in global_stetting_list:
            if keyring.get_password('system', key) is None:
                return True
        return False


class ProjectSetting:
    def __init__(self):
        self.data = dict()
        # self.proj_name = project_name
        self.setting_file_path = setting_filename
        if os.path.exists(self.setting_file_path):
            with open(self.setting_file_path) as f:
                self.data = yaml.load(f)

    def get_value(self, key):
        return self.data[key]

    def set_value(self, key, value):
        self.data[key] = value

    def write_back(self):
        with open(self.setting_file_path) as f:
            yaml.dump(self.data, f, default_flow_style=False)

    def read_data(self):
        return self.data


class State(object):
    def __init__(self, data):
        self.data = data

    def run(self):
        raise NotImplementedError

    def get_next_state(self):
        raise NotImplementedError


class StateMachine(object):
    def __init__(self, initial_state):
        self.current_state = initial_state

    def run_all(self):
        while True:
            self.current_state.run()
            self.current_state = self.current_state.get_next_state()
            if not self.current_state:
                break


class ProjectCreation(State):
    '''
    State for creating a new project
    '''
    def run(self):

        while True:
            prompt = click.style("Please enter the project name", fg='yellow')
            proj_name = click.prompt(prompt)
            project_dir = os.path.join(project_root, proj_name)
            if os.path.isdir(project_dir):
                msg = click.style("the project %s exists" % proj_name, fg='red')
                click.echo(msg)
            else:
                self.data['project_name'] = str(proj_name)
                break

    def get_next_state(self):
        '''
        '''
        global_setting = GlobalSetting()
        if global_setting.is_setting_missed():
            return GlobalConfiguration(self.data)
        else:
            return SplunkVersion(self.data)


class GlobalConfiguration(State):
    '''
    State for global value settings, get username, aws_access_key....
    '''

    def run(self):
        click.echo('Missing global setting values, '
                   'please answer the following question')

        for key, value in global_stetting_list.items():
            default = keyring.get_password('system', key)
            prompt = value['prompt_question']
            input_value = click.prompt(prompt, default=default)
            GlobalSetting.set_value(key, input_value)

    def get_next_state(self):
        return SplunkVersion(self.data)


class SplunkVersion(State):
    '''
    State for splunk version or package url
    '''
    def url_exists(self, path):
        try:
            r = requests.head(path)
            return r.status_code == requests.codes.ok
        except MissingSchema as err:
            log.error(err)
            return False

    def run(self):
        # take no splunk here
        splunk_version = ""
        while True:
            question = "Please enter package url(or empty for no splunk)"
            prompt = click.style(question, fg='yellow')
            splunk_version = click.prompt(prompt, default="", show_default=False)
            if not splunk_version:
                break

            if self.url_exists(splunk_version):
                break

            msg = 'the url you enter is not valid or reachable, ' \
                  'please try again'
            click.echo(msg)

        self.data['splunk_version'] = str(splunk_version).strip()

    def get_next_state(self):
        return OperatingSystem(self.data)


class MachineOnly(State):
    def run(self):
        question = 'How many instances do you want?'
        instance_num = click.prompt(question, default=1)
        self.data['instance_count'] = instance_num

    def get_next_state(self):
        return OutputSettings(self.data)


class OperatingSystem(State):
    def run(self):
        platform_arr = [p.replace("_count", "") for p in platform_count]
        prompt = click.style("Please select an operating system\n", fg='yellow')

        for idx, platform in enumerate(platform_arr):
            prompt += "  [{d:1d}] {p}\n".format(
                d=platform_arr.index(platform), p=platform)

        prompt += 'default is'

        while True:
            index = click.prompt(prompt, type=int, default=0)
            if index >= len(platform_arr) or index < 0:
                click.echo('Wrong value, try again...')
                continue

            platform = platform_arr[index]
            self.data.update({'operating_system': platform})
            click.echo(click.style(platform, fg='green') + " is selected")
            click.echo("")
            break

    def get_next_state(self):
        if self.data['splunk_version']:
            return Indexers(self.data)
        else:
            return MachineOnly(self.data)


class Indexers(State):
    def run(self):
        prompt = click.style(
            "How many indexers do you want?", fg='yellow')
        indexer_count = click.prompt(prompt, type=int, default=1)
        self.data['indexer_count'] = indexer_count
        self.data['instance_count'] += indexer_count
        self.data['roles_count'].extend(
            [['indexer'] for x in range(indexer_count)])

    def get_next_state(self):
        if self.data['indexer_count'] > 1:
            return IndexerCluster(self.data)
        else:
            return SearchHead(self.data)


class IndexerCluster(State):
    def run(self):
        prompt = click.style(
            "Do you want indexer cluster?", fg='yellow')
        is_indexer_cluster = click.confirm(prompt, default=True)

        self.data.update({'is_indexer_cluster_enabled': is_indexer_cluster})

        if not is_indexer_cluster:
            return

        self.data['roles_count'].append(['indexer-cluster-master'])

        for roles in self.data['roles_count']:
            if 'indexer' in roles:
                roles.append('indexer-cluster-peer')

        prompt = "Replication factor for indexer cluster:"
        replication_factor = click.prompt(prompt, type=int, default=2)
        obj = {'indexer_cluster': {'replication_factor': replication_factor}}
        self.data.update(obj)

        prompt = "Search factor for indexer cluster:"
        search_factor = click.prompt(prompt, type=int, default=2)
        self.data['indexer_cluster']['search_factor'] = search_factor

    def get_next_state(self):
        return SearchHead(self.data)


class SearchHead(State):
    def run(self):
        prompt = click.style("How many search head do you want?", fg='yellow')
        search_head_count = click.prompt(prompt, type=int, default=1)
        self.data.update({'search_head_count': search_head_count})
        role_arrays = [['search-head'] for x in range(search_head_count)]
        self.data['roles_count'].extend(role_arrays)

    def get_next_state(self):
        if self.data['search_head_count'] > 1:
            return SearchHeadCluster(self.data)
        else:
            return UniversalForwarder(self.data)


class SearchHeadCluster(State):
    def run(self):
        prompt = click.style("Do you want search head cluster?", fg='yellow')
        is_search_head_cluster = click.confirm(prompt, default=True)
        self.data.update(
            {'is_search_head_cluster_enabled': is_search_head_cluster})

        if not is_search_head_cluster:
            return

        self.data['roles_count'].append(['search-head-cluster-deployer'])
        is_captain_created = False
        for roles in self.data['roles_count']:
            if 'search-head' in roles:
                roles.append('search-head-cluster-member')
                if not is_captain_created:
                    roles.append('search-head-cluster-first-captain')
                    is_captain_created = True

        prompt = "Replication factor for search head cluster:"
        replication_factor = click.prompt(prompt, type=int, default=2)
        self.data.update({
            'search_head_cluster':
                {'replication_factor': replication_factor}
        })

    def get_next_state(self):
        return UniversalForwarder(self.data)


class UniversalForwarder(State):
    def run(self):
        # ask ubuntu and windows only
        prompt = click.style("How many universal forwarders do you want?",
                             fg='yellow')
        uf_count = click.prompt(prompt, type=int, default=0)
        self.data['roles_count'].extend(
            [['universal-forwarder'] for x in range(uf_count)])

        self.data.update({'universal_forwarder_count': uf_count})

    def get_next_state(self):
        cluster_enabled = self.data['is_indexer_cluster_enabled'] and self.data[
            'is_search_head_cluster_enabled']

        if cluster_enabled and self.data['universal_forwarder_count'] == 0:
            return LicenseMaster(self.data)
        else:
            return Deployment(self.data)


class Deployment(State):
    '''
    This stats stands for configuring splunk deployment server-client
    '''

    def run(self):
        prompt = click.style("Do you need a deployment server?", fg='yellow')
        deployment_server = click.confirm(prompt, default=False)
        self.data['deployment-server'] = deployment_server

        if not deployment_server:
            return

        self.data['roles_count'].append(['deployment-server'])

        for roles in self.data['roles_count']:
            if 'indexer' in roles and 'indexer-cluster-peer' not in roles:
                roles.append('deployment-client')
            elif 'search-head' in roles and 'search-head-cluster-member' not in roles:
                roles.append('deployment-client')
            elif 'universal-forwarder' in roles:
                roles.append('deployment-client')

    def get_next_state(self):
        return LicenseMaster(self.data)


class LicenseMaster(State):
    def get_next_state(self):
        return OutputSettings(self.data)

    def run(self):
        prompt = click.style("Do you need a central license master?", fg='yellow')
        license_master = click.confirm(prompt, default=True)

        if not license_master:
            return

        while True:
            prompt = "where's the license file you want to upload?"
            license_path = click.prompt(prompt)
            if os.path.exists(license_path):
                self.data.update({'license_path': license_path})
                break
            else:
                msg = click.style('the file path is not valid', fg='red')
                click.echo(msg)

        # right now we use a independent license master
        self.data['roles_count'].append(['central-license-master'])
        for roles in self.data['roles_count']:
            if 'search-head' in roles or 'indexer' in roles:
                roles.append('central-license-slave')


class OutputSettings(State):
    def _create_project(self, proj_name):
        project_dir = os.path.join(project_root, proj_name)
        os.mkdir(project_dir)
        file_path = os.path.abspath(os.path.dirname(__file__))

        # copy tf file
        tf_path = os.path.join(file_path, "terraform", "splunk.tf")
        shutil.copy(tf_path, project_dir)

        # create ssh key for project
        key = RSA.generate(2048)
        public_key_name = ssh_private_key_name + '.pub'
        private_key_path = os.path.join(project_dir, ssh_private_key_name)
        ssh_public_key_path = os.path.join(project_dir, public_key_name)
        with open(private_key_path, 'w') as content_file:
            os.chmod(private_key_path, 0600)
            content_file.write(key.exportKey('PEM'))
        pubkey = key.publickey()

        with open(ssh_public_key_path, 'w') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))

        # create sync folder
        sync_folder_path = os.path.join(project_dir, sync_folder)
        os.mkdir(sync_folder_path)
        # copy ssh key to be synced
        shutil.copy(private_key_path, sync_folder_path)


    def run(self):
        log.debug(self.data)

        project_name_ = self.data['project_name']
        self._create_project(project_name_)

        formatted_data = dict()
        # change pillar data
        # splunk version
        # splunk SH/IDX cluster replication factor
        # license path

        splunk_sls = dict()
        splunk_sls.update({'splunk_version': self.data['splunk_version']})
        if 'indexer_cluster' in self.data:
            splunk_sls.update({'indexer_cluster': self.data['indexer_cluster']})

        if 'search_head_cluster' in self.data:
            splunk_sls.update({'search_head_cluster': self.data['search_head_cluster']})

        # copy license file
        if 'license_path' in self.data:
            shutil.copy(self.data['license_path'], os.path.join(project_root, project_name_, sync_folder))
            self.data['license_path'] = \
                'salt://' + os.path.basename(self.data['license_path'])
            splunk_sls.update({'license_path': self.data['license_path']})

        formatted_data.update({'pillar': {'splunk.sls': splunk_sls}})

        formatted_data.update({'roles_count': self.data['roles_count']})

        # master terraform variable
        # dump data for remote terraform
        terraform_obj = dict()
        instance_count = self.data['instance_count'] if (len(self.data['roles_count']) == 0) else len(self.data['roles_count'])
        os_count_obj = {self.data['operating_system'] + '_count': instance_count}
        rdp_password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        terraform_obj['terraform'] = os_count_obj
        terraform_obj['terraform'].update({'rdp_password': rdp_password})
        terraform_obj['terraform']['access_key'] = keyring.get_password('system', 'aws_access_key')
        terraform_obj['terraform']['secret_key'] = keyring.get_password('system', 'aws_secret_key')
        terraform_obj['terraform']['username'] = keyring.get_password('system', 'username')
        terraform_obj['terraform']['project_name'] = project_name_

        formatted_data.update(terraform_obj)

        hipchat_obj = {
            'hipchat':
                {'hipchat_token': keyring.get_password('system', 'hipchat_token'),
                 'username': keyring.get_password('system', 'username'),
                 'project_name': project_name_
                 }
        }

        formatted_data.update(hipchat_obj)

        # salt master
        salt_master_obj = {
            'salt_master': {'instance_count': instance_count}
        }

        formatted_data.update(salt_master_obj)

        setting_path = os.path.join(project_root, project_name_, setting_filename)

        with open(setting_path, "w") as f:
            yaml.safe_dump(formatted_data, f, default_flow_style=False)

    def get_next_state(self):
        return None
