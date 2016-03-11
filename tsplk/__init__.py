import os
import shutil
import click
import keyring
import yaml
from collections import OrderedDict

vagrant_splunk_sub_module = 'vagrant-salty-splunk'
project_root = os.path.join(os.path.expanduser('~'), ".tsplk")
settings_path_template = os.path.join(project_root, '{p}', 'settings.yml')
pillar_path_template = os.path.join(
    project_root, '{p}', "salt", "pillar", '{s}')
file_path = os.path.abspath(os.path.dirname(__file__))

global_stetting_list = OrderedDict({
    'aws_access_key': {
        'prompt_question': 'Please enter AWS access key ID'
    },

    'atlas_token': {
        'prompt_question': 'Please enter atlas token'
    },

    'aws_secret_key': {
        'prompt_question': 'Please enter secret key'
    },

    'rdp_password': {
        'prompt_question': 'Please enter RDP password for windows VM'
    },

    'username': {
        'prompt_question': 'Please enter your user name'
                           '(your employee id is suggested)'
    },

    'key_path': {
        'prompt_question': 'Please enter your ssh key path for linux VM'
    },

    'key_name': {
        'prompt_question': 'Please enter your ssh key name on AWS'
    },

    'hipchat_token': {
        'prompt_question': 'Please enter the token of hipchat room'
    },
})

project_setting = [
    'ubuntu_1404_count',
    'windows_2008_r2_count',
    'windows_2012_r2_count'
]

default_settings = {
    'search-head': 0,
    'indexer': 0,
    'indexer-cluster-master': False,
    'indexer-cluster-peer': 0,
    'indexer-cluster-search-head': 0,
    'search-head-cluster-member': 0,
    'search-head-cluster-deployer': 0,
    'search-head-cluster-first-captain': False,
    'central-license-master': False,
    'central-license-slave': 0,
    'deployment-server': False,
    'deployment-client': 0,
    'windows-universal-forwarder': 0,
    'ubuntu-universal-forwarder': 0,
    'roles_count': []
}

# the name here need to match name under
# salt/file_base/orchestration
splunk_architectures = [
    sls.replace(".sls", "") for sls in os.listdir(
        os.path.join(file_path, "salt", "file_base", "orchestration"))
]


def ch_project_folder(project_name):
    os.chdir(os.path.join(project_root, project_name))


def update_sls(path, options):
    '''
    update sls files
    '''
    with open(path, "r") as f:
        settings = yaml.load(f)
    settings.update(options)

    with open(path, "w") as f:
        yaml.dump(settings, f, default_flow_style=False)


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

    def __init__(self, project_name):
        self.data = dict()
        self.proj_name = project_name
        self.setting_file_path = settings_path_template.format(p=project_name)
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


def _create_project(proj_name):
    project_dir = os.path.join(project_root, proj_name)
    if os.path.isdir(project_dir):
        click.echo(click.style("the project %s exists" % proj_name, fg='red'))
        exit(1)
    else:
        salt_path = os.path.join(file_path, "salt")
        shutil.copytree(salt_path, os.path.join(project_dir, 'salt'))

        tf_path = os.path.join(file_path, "terraform", "splunk.tf")
        shutil.copy(tf_path, project_dir)

        deploy_minion_py = os.path.join(file_path, 'saltminion_deployer.py')
        shutil.copy(deploy_minion_py, project_dir)

        deploy_minion_py = os.path.join(file_path, 'terraform.py')
        shutil.copy(deploy_minion_py, project_dir)


def _get_vagrant_folder():
    _template_folder = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(_template_folder, vagrant_splunk_sub_module)


class State(object):

    def run(self):
        raise NotImplementedError

    def next(self):
        return None

    def dump_settings(self):
        '''
        dump settings to settings.yml
        '''
        settings = os.path.join(
            settings_path_template.format(p=self.data['project_name']))

        for platform in project_setting:
            if self.data['platform'] in platform:
                self.data[platform] = len(self.data['roles_count'])
            else:
                self.data[platform] = 0

            if 'ubuntu' in platform:
                self.data[platform] = self.data[platform] + \
                                      self.data['ubuntu-universal-forwarder']
            elif 'windows_2012' in platform:
                self.data[platform] = self.data[platform] + \
                                      self.data['windows-universal-forwarder']

        for i in range(self.data['ubuntu-universal-forwarder']):
            self.data['roles_count'].append(['ubuntu-universal-forwarder'])
        for i in range(self.data['windows-universal-forwarder']):
            self.data['roles_count'].append(['windows-universal-forwarder'])

        with open(settings, "w") as yml_file:
            yaml.dump(self.data, yml_file, default_flow_style=False)


class StateMachine(object):

    def __init__(self, initial_state):
        self.current_state = initial_state

    def run(self):
        self.current_state.run()

    def run_all(self):
        while True:
            self.current_state.run()
            self.current_state = self.current_state.next()
            if self.current_state is None:
                break


class New(State):

    '''
    State for creating a new project
    '''

    def __init__(self):
        self.data = default_settings

    def run(self):
        prompt = click.style("Please enter the project name", fg='yellow')
        proj_name = click.prompt(prompt)
        _create_project(proj_name)

        self.data['project_name'] = str(proj_name)

    def next(self):
        '''
        '''
        global_setting = GlobalSetting()
        if global_setting.is_setting_missed():
            return SetGlobal(self.data)
        else:
            return SplunkVersion(self.data)


class SetGlobal(State):
    '''
    State for global value settings, get username, aws_access_key....
    '''

    def __init__(self, data):
        self.data = data

    def run(self):
        for key, value in global_stetting_list.items():
            default = keyring.get_password('system', key)
            prompt = value['prompt_question']
            input_value = click.prompt(prompt, default=default)
            GlobalSetting.set_value(key, input_value)

    def next(self):
        return SplunkVersion(self.data)


class SplunkVersion(State):
    '''
    State for splunk version or package url
    '''

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style("Plese enter Splunk version or package url",
                             fg='yellow')
        splunk_version = str(click.prompt(prompt))
        file_path = pillar_path_template.format(
            p=self.data['project_name'], s="splunk.sls")
        update_sls(file_path, {'version': splunk_version})

    def next(self):
        return InstancePlatform(self.data)


class InstancePlatform(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        platform_arr = [p.replace("_count", "") for p in project_setting]
        prompt = click.style("Please select Splunk platform\n", fg='yellow')

        for idx, platform in enumerate(platform_arr):
            prompt = prompt + "  [{d:1d}] {p}\n".format(
                d=platform_arr.index(platform), p=platform)

        prompt += 'default is'

        index = click.prompt(prompt, type=int, default=0)
        platform = platform_arr[index]
        self.data['platform'] = platform

        click.echo(click.style(platform, fg='green') + " is selected")
        click.echo("")

    def next(self):
        return Indexers(self.data)


class Indexers(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "How many indexer do you want?", fg='yellow')
        indexer_count = click.prompt(prompt, type=int, default=2)
        self.data['indexer'] = indexer_count

    def next(self):
        if self.data['indexer'] > 1:
            return IndexerCluster(self.data)
        else:
            return SearchHead(self.data)


class IndexerCluster(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Do you want indexer cluster? (Y/N)", fg='yellow')
        indexer_cluster = click.prompt(prompt, type=bool, default='Y')
        self.data['indexer-cluster-master'] = indexer_cluster

        indexer_count = self.data['indexer']
        if indexer_cluster:
            self.data['roles_count'].append(['indexer-cluster-master'])
            self.data['indexer-cluster-peer'] = indexer_count
            self.data['indexer'] = 0
            for i in range(indexer_count):
                self.data['roles_count'].append(['indexer-cluster-peer'])

            prompt = "Replication factor for indexer cluster:"
            replication_factor = click.prompt(prompt, type=int, default=2)

            prompt = "Search factor for indexer cluster:"
            search_factor = click.prompt(prompt, type=int, default=2)

            sls = pillar_path_template.format(
                p=self.data['project_name'], s="indexer_cluster.sls")
            update_sls(sls, {'replication_factor': replication_factor,
                             'search_factor': search_factor})
        else:
            for i in range(indexer_count):
                self.data['roles_count'].append(['indexer'])

    def next(self):
        return SearchHead(self.data)


class SearchHead(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "How many search head do you want?", fg='yellow')
        search_head_count = click.prompt(prompt, type=int, default=2)
        self.data['search-head'] = search_head_count

    def next(self):
        if self.data['search-head'] > 1:
            return SearchHeadCluster(self.data)
        else:
            return UniversalForwarder(self.data)


class SearchHeadCluster(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Do you want search head cluster? (Y/N)", fg='yellow')
        search_head_cluster = click.prompt(prompt, type=bool, default='Y')
        self.data['search-head-cluster-deployer'] = search_head_cluster

        search_head_count = self.data['search-head']
        if search_head_cluster:
            self.data['roles_count'].append(['search-head-cluster-deployer'])
            self.data['search-head-cluster-first-captain'] = True
            self.data['search-head-cluster-member'] = search_head_count
            self.data['search-head'] = 0

            for i in range(search_head_count):
                # set the first member as captain
                if 0 == i:
                    self.data['roles_count'].append(
                        ['search-head-cluster-member',
                         'search-head-cluster-first-captain'])
                else:
                    self.data['roles_count'].append(
                        ['search-head-cluster-member'])

            prompt = "Replication factor for search head cluster:"
            replication_factor = click.prompt(prompt, type=int, default=2)

            sls = pillar_path_template.format(
                p=self.data['project_name'], s="searchhead_cluster.sls")
            update_sls(sls, {'replication_factor': replication_factor})

        else:
            if self.data['indexer-cluster-master']:
                self.data['search-head'] = 0
                self.data['indexer-cluster-search-head'] = search_head_count
                for i in range(search_head_count):
                    self.data['roles_count'].append(
                        ['indexer-cluster-search-head'])
            else:
                for i in range(search_head_count):
                    self.data['roles_count'].append(['search-head'])

    def next(self):
        return UniversalForwarder(self.data)


class UniversalForwarder(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        # ask ubuntu and windows only
        prompt = click.style(
            "How many ubuntu universal forwarder do you want?",
            fg='yellow')
        ubuntu_uf = click.prompt(prompt, type=int, default=0)
        self.data['ubuntu-universal-forwarder'] = ubuntu_uf

        prompt = click.style(
            "How many windows universal forwarder do you want?",
            fg='yellow')
        windows_uf = click.prompt(prompt, type=int, default=0)
        self.data['windows-universal-forwarder'] = windows_uf

    def next(self):
        if self.data['ubuntu-universal-forwarder'] + \
                self.data['windows-universal-forwarder'] == 0 \
                and self.data['search-head-cluster-deployer'] \
                and self.data['indexer-cluster-master']:
            return LicenseMaster(self.data)
        else:
            return Deployment(self.data)


class Deployment(State):

    '''
    This stats stands for configuring splunk deployment server-client
    '''

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Do you need deployment server? (Y/N)", fg='yellow')
        deployment_server = click.prompt(prompt, type=bool, default='Y')
        self.data['deployment-server'] = deployment_server

        if deployment_server:
            self.data['roles_count'].append(['deployment-server'])

            prompt = click.style(
                "How many deployment client do you want ", fg='yellow')
            deployment_client = click.prompt(prompt, type=int, default=2)
            self.data['deployment-client'] = deployment_client
            for i in range(deployment_client):
                self.data['roles_count'].append(['deployment-client'])

    def next(self):
        return LicenseMaster(self.data)


class LicenseMaster(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Do you need license master? (Y/N)", fg='yellow')
        license_master = click.prompt(prompt, type=bool, default='Y')
        self.data['central-license-master'] = license_master
        if license_master:
            self.data['roles_count'].append(['central-license-master'])
            self.data['roles_count'].append(['central-license-slave'])
            self.data['central-license-slave'] = True

        self.dump_settings()
