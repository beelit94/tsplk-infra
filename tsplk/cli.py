import click
from . import New, StateMachine, GlobalSetting, ProjectSetting,\
    ch_project_folder, project_root, global_stetting_list
import os
import shutil
from terraform_saltmaster import TerraformSaltMaster
import subprocess
import keyring


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


@click.command()
@click.argument("project")
@click.option("--onlyminion", "-m", is_flag=True)
def up(project, onlyminion):
    '''
    bring up the machines of the given project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    t = TerraformSaltMaster(master_var, minion_var)

    if onlyminion:
        if t.is_master_up():
            t.up_minion()
            click.echo('we will send msg to Hipchat room tsplk when it ready')
            return
        else:
            click.echo("master is not up, plz up the project first")
            return

    click.echo('start master...(this could take few minutes)')
    try:
        t.up()
    except EnvironmentError as err:
        click.echo('something wrong...')
        click.echo(err)
    click.echo('master is started, the rest machine will start by master')
    click.echo('we will send msg to Hipchat room tsplk when it ready')


@click.command()
@click.argument("project")
def status(project):
    '''
    Show the status of the machines of the given project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    variables = create_master_variables(project, ps)

    tr = TerraformSaltMaster(variables)
    instances = tr.get_minions_info()
    for instance in instances:
        click.echo(instance['name'] + ' ' + instance['role'] + ' ' + instance['info']['public_ip'])


@click.command()
@click.argument("project")
def destroy(project):
    '''
    Destroy the machines of the give project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    t = TerraformSaltMaster(master_var, minion_var)

    t.destroy()


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
    projects = [ name for name in os.listdir(project_root)
                 if os.path.isdir(os.path.join(project_root, name)) ]
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
