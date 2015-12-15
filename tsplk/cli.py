import click
from . import New, StateMachine, GlobalSetting, ProjectSetting, \
    ch_project_folder, project_root, global_stetting_list
import os
import shutil
from saltmaster_deployer import TerraformSaltMaster
import subprocess
import keyring
import logging
import tabulate

log = logging.getLogger()
projects = [name for name in os.listdir(project_root)
            if os.path.isdir(os.path.join(project_root, name))]


class ClickStream(object):
    def write(self, string):
        click.echo(string, err=True, nl=False)


ch = logging.StreamHandler(ClickStream())
# ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
log.setLevel(logging.ERROR)

if 'TSPLK_LOG' in os.environ:
    log.setLevel(logging.DEBUG)


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
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.option("--only-minion", "-m", is_flag=True,
              help='if the master is up, only bring up the minions on master'
                   'this is useful when you want to '
                   'customized your salt files')
def up(project, only_minion):
    '''
    bring up the machines of the given project
    '''

    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)
    # get value here since it takes time
    is_master_up = salt_master.is_master_up()

    def wait_for_minions_msg():
        click.echo('Minions is deploying by salt-master')
        click.echo("We'll send a message to Hipchat room tsplk when it's ready")

    if only_minion and not is_master_up:
        click.secho("You can't only up minion when master is not up",
                    fg='red')
        return

    if only_minion:
        salt_master.up_minion()
        wait_for_minions_msg()
        return

    click.echo('Starting master...(this could take few minutes)')
    try:
        salt_master.up()
    except EnvironmentError as err:
        click.secho('Salt master fail to start', fg='green')
        click.echo(err)
        return

    click.echo('Salt master started successfully!',
               color='green')
    wait_for_minions_msg()


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def status(project):
    '''
    Show the status of the machines of the given project
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    print_info = ['host', 'minion_id', 'role', 'ip']
    print_arr = []
    print_arr.append(print_info)

    if salt_master.is_master_up():
        master = [
            '', 'salt-master', 'salt-master', salt_master.get_public_ip()
        ]
        print_arr.append(master)
    else:
        click.echo('master is not up yet')

    if not salt_master.is_minions_up():
        click.echo('minion is not ready yet')

    info = salt_master.get_minions_info()
    info = [] if info is None else info
    for instance in info:
        row = []
        for title in print_info:
            row.append(instance[title])
        print_arr.append(row)

    table = tabulate.tabulate(print_arr)
    click.echo(table)


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.option("--only-minion", "-m", is_flag=True,
              help='only destroy the salt minions'
                   'this is useful when you want to '
                   'debug salt files')
def destroy(project, only_minion):
    '''
    Destroy the machines of the give project
    '''
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
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.argument("minion", nargs=-1)
def browse(project, minion):
    '''
    '''
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    if len(minion) == 1:
        minion_to_be_connected = minion[0]
        info = salt_master.get_minions_info()
        for i in info:

            if i['minion_id'] == minion_to_be_connected:
                subprocess.call(["open", "http://%s:8000" % i['ip']])
                return
        click.echo('minion not exist')
    elif len(minion) == 0:
        click.echo('give at least one minion')
    else:
        click.echo('you could only connect to one minion at a time')



@click.command()
def version():
    p = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'VERSION')
    with open(p) as f:
        ver = f.read().strip()
        click.echo('current version: %s' % ver)


@click.command()
def list():
    click.echo(projects)


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def delete(project):
    '''
    Destroy the machines and delete the given project
    '''
    project_path = os.path.join(project_root, project)
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)
    salt_master.destroy()

    shutil.rmtree(project_path)
    click.echo("{p} has been deleted".format(p=project))


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.argument("minion", nargs=-1)
def ssh(project, minion):
    ch_project_folder(project)
    ps = ProjectSetting(project)

    master_var = create_master_variables(project, ps)
    minion_var = create_minion_variables(project, ps)
    salt_master = TerraformSaltMaster(master_var, minion_var)

    if len(minion) == 0:
        subprocess.call(['ssh', '-i', GlobalSetting.get_value('key_path'),
                         '-o', 'StrictHostKeyChecking=no',
                         'ubuntu@%s' % salt_master.get_public_ip()])
    elif len(minion) == 1:
        minion_to_be_connected = minion[0]
        info = salt_master.get_minions_info()
        for i in info:

            if i['minion_id'] == minion_to_be_connected:
                subprocess.call(
                    ['ssh', '-i', GlobalSetting.get_value('key_path'),
                     '-o', 'StrictHostKeyChecking=no',
                     'ubuntu@%s' % i['ip']])
                return
        click.echo('minion not exist')
    else:
        click.echo('you could only connect to one minion at a time')


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
