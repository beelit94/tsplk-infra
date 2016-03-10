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
        click.echo("the project %s exists" % proj_name)
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
        # write into settings.yml
        settings = os.path.join(
            settings_path_template.format(p=self.data['project_name']))
        for platform in project_setting:
            if self.data['platform'] in platform:
                self.data[platform] = len(self.data['roles_count'])
            else:
                self.data[platform] = 0

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
        self.data = dict()

    def run(self):
        proj_name = click.prompt("Please Enter the project name")
        _create_project(proj_name)

        self.data['project_name'] = str(proj_name)

    def next(self):
        '''
        '''
        global_setting = GlobalSetting()
        if global_setting.is_setting_missed():
            return SetGlobal(self.data)
        else:
            return SplunkCommonSettingState(self.data)


class SetGlobal(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        for key, value in global_stetting_list.items():
            default = keyring.get_password('system', key)
            prompt = value['prompt_question']
            input_value = click.prompt(prompt, default=default)
            GlobalSetting.set_value(key, input_value)

    def next(self):
        return SplunkCommonSettingState(self.data)


class SplunkCommonSettingState(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = ("Plese enter the Splunk version you want, "
            "or the url to download the Splunk package")
        splunk_version = str(click.prompt(prompt))
        file_path = pillar_path_template.format(
            p=self.data['project_name'], s="splunk.sls")
        update_sls(file_path, {'version': splunk_version})

    def next(self):
        return Platform(self.data)


class Platform(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        platform_arr = [p.replace("_count", "") for p in project_setting]
        prompt = click.style("Please select the platform you want to use\n",
                             fg='yellow')

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
        return Timeout(self.data)


class Timeout(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Please set timeout for your environment (hours)\n", fg='yellow')

        prompt += 'default is'
        timeout = click.prompt(prompt, type=int, default=8)
        click.echo(click.style(
            "Your machines will be destroyed after {h} hours".format(
                h=timeout), fg='red'))
        self.data['timeout'] = timeout
        click.echo("")

    def next(self):
        return SplunkArchState(self.data)


class SplunkArchState(State):

    def __init__(self, data):
        self.data = data

    def run(self):
        prompt = click.style(
            "Please select the architecture you want to build\n",
            fg='yellow')
        for arch in splunk_architectures:
            prompt = prompt + "  [{d:1d}] {p}\n".format(
                d=splunk_architectures.index(arch), p=arch)

        prompt += 'default is'
        index = click.prompt(prompt, type=int, default=0)
        arch = splunk_architectures[index]
        self.data['splunk_architecture'] = arch

        click.echo(click.style(arch, fg='green') + " is selected")
        click.echo("")

    def next(self):
        arch = self.data['splunk_architecture']
        if "indexer_cluster" == arch:
            return IndexerCluster(self.data)
        elif "single_indexer" == arch:
            return SingleIndexer(self.data)
        elif "searchhead_cluster" == arch:
            return SearchHeadCluster(self.data)
        elif "searchhead_and_indexer_cluster" == arch:
            return SearchHeadAndIndexerCluster(self.data)
        elif "indexers_with_deployment_server" == arch:
            return Deployment(self.data)


class SingleIndexer(State):

    '''
    This state stands for configuring a single instance Splunk
    '''

    def __init__(self, data):
        '''
        '''
        self.data = data
        self.number = 0
        self.data['roles_count'] = []

    def dump_settings(self):
        '''
        dump settings to settings.yml
        '''
        # write into settings.yml
        settings = os.path.join(
            settings_path_template.format(p=self.data['project_name']))
        for platform in project_setting:
            if self.data['platform'] in platform:
                self.data[platform] = self.number
            else:
                self.data[platform] = 0

        with open(settings, "w") as yml_file:
            yaml.dump(self.data, yml_file, default_flow_style=False)

    def run(self):
        '''
        '''
        prompt = "How many instances do you want?"
        self.number = click.prompt(prompt, type=int, default=1)
        for i in range(self.number):
            self.data['roles_count'].append(['splunk-single-indexer'])
        self.dump_settings()


class IndexerCluster(State):

    '''
    This stats stands for configuring a splunk indexer cluster
    '''

    def __init__(self, data):
        '''
        '''
        self.data = data
        self.data['roles_count'] = []
        self.data['roles_count'].append(['splunk-cluster-master'])

    def run(self):
        prompt = "How many slaves do you want?"
        number_of_slaves = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_slaves):
            self.data['roles_count'].append(['splunk-cluster-slave'])

        prompt = "How many search heads do you want?"
        number_of_searhheads = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_searhheads):
            self.data['roles_count'].append(['splunk-cluster-searchhead'])

        # write into settings.yml
        self.dump_settings()

        prompt = "Replication factor:"
        replication_factor = click.prompt(prompt, type=int, default=2)

        prompt = "Search factor:"
        search_factor = click.prompt(prompt, type=int, default=2)

        sls = pillar_path_template.format(
            p=self.data['project_name'], s="indexer_cluster.sls")
        update_sls(sls, {'replication_factor': replication_factor,
                         'search_factor': search_factor})


class SearchHeadCluster(State):

    '''
    This stats stands for configuring a splunk searchhead cluster
    '''

    def __init__(self, data):
        '''
        '''
        self.data = data
        self.data['roles_count'] = []
        self.data['roles_count'].append(['splunk-shcluster-deployer'])

    def run(self):
        prompt = "How many members do you want?"
        number_of_members = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_members):
            # set the first member as captain
            if 0 == i:
                self.data['roles_count'].append(
                    ['splunk-shcluster-member', 'splunk-shcluster-captain'])
            else:
                self.data['roles_count'].append(['splunk-shcluster-member'])

        prompt = "How many indexers do you want?"
        number_of_indexers = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_indexers):
            self.data['roles_count'].append(['splunk-shcluster-indexer'])

        # write into settings.yml
        self.dump_settings()

        prompt = "Replication factor:"
        replication_factor = click.prompt(prompt, type=int, default=2)

        sls = pillar_path_template.format(
            p=self.data['project_name'], s="searchhead_cluster.sls")
        update_sls(sls, {'replication_factor': replication_factor})


class SearchHeadAndIndexerCluster(State):

    '''
    This stats stands for configuring splunk IDC and SHC
    '''

    def __init__(self, data):
        self.data = data
        self.data['roles_count'] = []
        self.data['roles_count'].append(['splunk-cluster-master'])
        self.data['roles_count'].append(['splunk-shcluster-deployer'])

    def run(self):
        prompt = "How many slaves for indexer cluster do you want?"
        number_of_slaves = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_slaves):
            self.data['roles_count'].append(['splunk-cluster-slave'])

        prompt = "How many members for search head cluster do you want?"
        number_of_members = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_members):
            # set the first member as captain
            if 0 == i:
                self.data['roles_count'].append(
                    ['splunk-shcluster-member', 'splunk-shcluster-captain'])
            else:
                self.data['roles_count'].append(['splunk-shcluster-member'])

        # write into settings.yml
        self.dump_settings()

        prompt = "Replication factor for indexer cluster:"
        replication_factor = click.prompt(prompt, type=int, default=2)

        prompt = "Search factor for indexer cluster:"
        search_factor = click.prompt(prompt, type=int, default=2)

        sls = pillar_path_template.format(
            p=self.data['project_name'], s="indexer_cluster.sls")
        update_sls(sls, {'replication_factor': replication_factor,
                         'search_factor': search_factor})

        prompt = "Replication factor for search head cluster:"
        replication_factor = click.prompt(prompt, type=int, default=2)

        sls = pillar_path_template.format(
            p=self.data['project_name'], s="searchhead_cluster.sls")
        update_sls(sls, {'replication_factor': replication_factor})


class Deployment(State):

    '''
    This stats stands for configuring splunk deployment server-client
    '''

    def __init__(self, data):
        self.data = data
        self.data['roles_count'] = []
        self.data['roles_count'].append(['splunk-deployment-server'])

    def run(self):
        prompt = "How many clients do you want?"
        number_of_clients = click.prompt(prompt, type=int, default=2)
        for i in range(number_of_clients):
            self.data['roles_count'].append(['splunk-deployment-client'])

        # write into settings.yml
        self.dump_settings()
