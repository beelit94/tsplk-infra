import click
from . import New, StateMachine, GlobalSetting, ProjectSetting,\
    ch_project_folder, project_root, global_stetting_list
import os
import shutil
from terraform import TerraformSaltMaster
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
def up(project):
    '''
    bring up the machines of the given project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    variables = create_terraform_variables(project, ps)

    tr = TerraformSaltMaster(variables)
    tr.up()
    tr.apply_minions()


@click.command()
@click.argument("project")
def status(project):
    '''
    Show the status of the machines of the given project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    variables = create_terraform_variables(project, ps)

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

    variables = create_terraform_variables(project, ps)

    tr = TerraformSaltMaster(variables)
    tr.destroy()


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

    variables = create_terraform_variables(project, ps)
    t = TerraformSaltMaster(variables)
    subprocess.call(['ssh', '-i', GlobalSetting.get_value('key_path'),
                     '-o', 'StrictHostKeyChecking=no',
                     'ubuntu@%s' % t.get_public_ip()])


def create_terraform_variables(project, ps):
    variables = dict()
    variables.update(GlobalSetting.read_data())
    variables.update(ps.read_data())
    variables.update({'project_name': project})
    variables['roles_count'] = ''
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
