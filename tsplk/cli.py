import click
from . import New, StateMachine, GlobalSetting, ProjectSetting, \
    ch_project_folder, project_root, global_stetting_list
import os
import shutil
from saltmaster_deployer import TerraformSaltMaster
import subprocess
import keyring
import logging
import sys

log = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

@click.group()
def main():
    """This tool is to create splunk ready environment."""
    pass


@click.command()
def config():
    '''
    config global settings for tsplk
    '''
    for key, value in global_stetting_list.items():
        default = keyring.get_password('system', key)
        prompt = value['prompt_question']
        input_value = click.prompt(prompt, default=default)
        GlobalSetting.set_value(key, input_value)


@click.command()
def new():
    '''
    command for creating a new project
    '''
    state = New()
    machine = StateMachine(state)
    machine.run_all()


def check_project_exist(project):
    if not os.path.exists(os.path.join(project_root, project)):
        click.secho('Project %s is not exist.' % project, fg='red')
        click.echo('the available projects are:')
        projects = [name for name in os.listdir(project_root)
                    if os.path.isdir(os.path.join(project_root, name))]
        projects_str = ', '.join(projects)
        click.secho(projects_str, fg='yellow')
        exit(1)


@click.command()
@click.argument("project", nargs=1)
@click.option("--only-minion", "-m", is_flag=True,
              help='if the master is up, only bring up the minions on master'
                   'this is useful when you want to '
                   'customized your salt files')
def up(project, only_minion):
    '''
    bring up the machines of the given project
    '''
    check_project_exist(project)

    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    def wait_for_minions_msg():
        click.echo('minion instances is still in process')
        click.echo("we'll send a message to Hipchat room tsplk when it ready")

    if only_minion and not salt_master.is_master_up():
        click.secho("You can't only up minion when master is not up",
                    fg='red')
        return

    if only_minion:
        salt_master.up_minion()
        wait_for_minions_msg()
        return

    click.echo('start master...(this could take few minutes)')
    try:
        salt_master.up()
    except EnvironmentError as err:
        click.secho('Salt master fail to start', fg='green')
        click.echo(err)
    click.echo('Salt master started successfully!',
               color='green')
    wait_for_minions_msg()


@click.command()
@click.argument("project", nargs=1)
def status(project):
    '''
    Show the status of the machines of the given project
    '''
    check_project_exist(project)
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    if not salt_master.is_master_up():
        click.echo('the project is not up')
    info = salt_master.get_minions_info()
    click.echo(info)


@click.command()
@click.argument("project")
@click.option("--only-minion", "-m", is_flag=True,
              help='only destroy the salt minions'
                   'this is useful when you want to '
                   'debug salt files')
def destroy(project, only_minion):
    '''
    Destroy the machines of the give project
    '''
    check_project_exist(project)
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    if not salt_master.is_master_up():
        click.echo('Done.')
        return

    click.echo('destroying minions...')
    salt_master.destroy_minion()

    if only_minion:
        return

    click.echo('destroying master...')
    salt_master.destroy_master()
    click.echo('Done.')


@click.command()
@click.argument("project")
def browse(project):
    '''
    '''
    get_environment_ready(project)
    os.chdir(os.path.join(project_root, project))
    v = vagrant.Vagrant(env=os.environ)
    host = v.hostname()
    subprocess.call(["open", "http://%s:8000" % host])


@click.command()
def version():
    p = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'VERSION')
    with open(p) as f:
        ver = f.read().strip()
        click.echo('current version: %s' % ver)


@click.command()
def list():
    projects = [name for name in os.listdir(project_root)
                if os.path.isdir(os.path.join(project_root, name))]
    click.echo(projects)


@click.command()
@click.argument("project")
def delete(project):
    '''
    Destroy the machines and delete the given project
    '''

    project_path = os.path.join(project_root, project)
    if not os.path.isdir(project_path):
        click.echo("{p} does not exist".format(p=project))

    destroy(project)
    shutil.rmtree(project_path)
    click.echo("{p} has been deleted".format(p=project))


@click.command()
@click.argument("project")
def ssh(project):
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    t = TerraformSaltMaster(master_var, minion_var)
    subprocess.call(['ssh', '-i', GlobalSetting.get_value('key_path'),
                     '-o', 'StrictHostKeyChecking=no',
                     'ubuntu@%s' % t.get_public_ip()])


def create_master_variables(project, ps):
    variables = dict()
    variables.update(GlobalSetting.read_data())
    variables.update(ps.read_data())
    variables.update({'project_name': project})
    variables.pop('roles_count')
    return variables


def create_minion_variables(project, ps):
    variables = dict()
    variables.update(GlobalSetting.read_data())
    variables.update(ps.read_data())
    variables.update({'project_name': project})

    variables['key_path'] = variables['key_name']
    variables['ubuntu_saltmaster_count'] = 0
    variables['salt_master_ip'] = None
    variables.update({'project_name': project})
    variables.pop('roles_count')
    variables.pop('splunk_architecture')

    return variables


main.add_command(up)
main.add_command(browse)
main.add_command(new)
main.add_command(status)
main.add_command(destroy)
main.add_command(version)
main.add_command(list)
main.add_command(delete)
main.add_command(ssh)
main.add_command(config)
