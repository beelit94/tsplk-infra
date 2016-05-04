import logging
import os
import shutil
import subprocess
import click
import tabulate
from saltmaster_deployer import TerraformSaltMaster
from . import ProjectCreation, StateMachine, GlobalSetting, ProjectSetting, \
    ch_project_folder, project_root

log = logging.getLogger()
if not os.path.isdir(project_root):
    os.mkdir(project_root)

projects = [name for name in os.listdir(project_root)
            if os.path.isdir(os.path.join(project_root, name))]




class ClickStream(object):
    def write(self, string):
        click.echo(string, err=True, nl=False)


ch = logging.StreamHandler(ClickStream())
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
log.setLevel(logging.ERROR)

if 'TSPLK_LOG' in os.environ:
    log.setLevel(logging.DEBUG)


@click.group()
def main():
    """This tool is to create a splunk ready environment."""
    pass


@click.command()
def config():
    '''
    config global settings for tsplk
    '''
    GlobalSetting.get_input_from_user()


@click.command()
def new():
    '''
    wizard of creating a new project
    '''
    default_settings = {
        'instance_count': 0,
        'roles_count': [],
        'is_indexer_cluster_enable': False,
        'is_search_head_cluster_enable': False,
    }
    state = ProjectCreation(default_settings)
    machine = StateMachine(state)
    machine.run_all()


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def up(project):
    '''
    bring up and provision the machines within the project created by new command
    :param project: name of project
    '''
    import time
    t0 = time.time()

    ch_project_folder(project)
    master_var = create_master_variables(project)
    salt_master = TerraformSaltMaster(master_var)

    click.echo('Starting master...(this could take few minutes)')
    try:
        salt_master.up()
    except EnvironmentError as err:
        click.secho('Salt master fail to start', fg='green')
        click.echo(err)
        return

    t1 = time.time()

    click.echo('Salt master started successfully! ',
               color='green')
    log.debug('take time: %.2f' % (t1-t0))
    click.echo('Minions is deploying by salt-master')
    click.echo("We'll send a message to Hipchat room tsplk when it's ready")


@click.command()
@click.argument("project", nargs=-1, type=click.Choice(projects))
def status(project):
    '''
    Show the status of the machines of the given project
    :param project: name of project, if it's not provided, show status of all projects
    '''
    projects_to_show = project if len(project) > 0 else projects

    for project in projects_to_show:
        msg = click.style('Project: %s' % project, fg='green')
        click.echo(msg)
        ch_project_folder(project)
        master_var = create_master_variables(project)

        salt_master = TerraformSaltMaster(master_var)

        print_info = ['minion_id', 'roles', 'public_ip', 'private_ip', 'instance_type']
        print_arr = []

        if salt_master.is_master_up():
            master = [
                '', 'salt-master', salt_master.get_public_ip(), '', ''
            ]
            print_arr.append(master)
        else:
            click.echo('master is not up yet')
            continue

        info = salt_master.get_minions_info()
        if not info:
            click.echo('minion is not ready yet')
            continue

        for key in info:
            row = [key]
            for title in print_info[1:]:
                if title in info[key]:
                    cell = info[key][title]
                else:
                    cell = ''
                row.append(cell)

            print_arr.append(row)

        table = tabulate.tabulate(print_arr,
                                  headers=print_info,
                                  tablefmt="fancy_grid")
        click.echo(table)


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def destroy(project):
    '''
    Destroy the machines of the give project
    '''
    ch_project_folder(project)
    master_var = create_master_variables(project)
    salt_master = TerraformSaltMaster(master_var)

    if not salt_master.is_master_up():
        click.echo('Done.')
        return

    click.echo('destroying minions...')
    salt_master.destroy_minion()

    click.echo('destroying master...')
    salt_master.destroy_master()
    click.echo('Done.')


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.argument("minion", nargs=1)
def browse(project, minion):
    '''
    open splunk page by given project and minion name
    '''
    ch_project_folder(project)
    master_var = create_master_variables(project)
    salt_master = TerraformSaltMaster(master_var)

    info = salt_master.get_minions_info()
    for i in info:
        if i == minion:
            subprocess.call(
                ["open", "http://%s:8000" % info[minion]['public_ip']]
            )
            return
    click.echo('minion not exist')


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def rdp(project):
    '''
    Return RDP password of the project
    '''
    ch_project_folder(project)
    ps = ProjectSetting()

    if 'rdp_password' in ps.data['terraform']:
        msg = 'rdp password for windows machine in this project is :'
        click.echo(msg + ps.data['terraform']['rdp_password'])
    else:
        click.echo('no rdp password for this project')

@click.command()
def version():
    '''
    Show current tsplk version
    '''
    p = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'VERSION')
    with open(p) as f:
        ver = f.read().strip()
        click.echo('current version: %s' % ver)


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
def delete(project):
    '''
    Destroy the machines and delete the given project
    '''
    project_path = os.path.join(project_root, project)
    ch_project_folder(project)

    master_var = create_master_variables(project)
    salt_master = TerraformSaltMaster(master_var)
    salt_master.destroy()

    shutil.rmtree(project_path)
    click.echo("{p} has been deleted".format(p=project))


@click.command()
@click.argument("project", nargs=1, type=click.Choice(projects))
@click.argument("minion", nargs=-1)
def ssh(project, minion):
    '''
    ssh to salt-master or a minion
    :param project: name of the project
    :param minion: name of linux minion, if minion name is not specified, ssh to salt-master
    '''
    ch_project_folder(project)
    master_var = create_master_variables(project)
    salt_master = TerraformSaltMaster(master_var)
    ssh_key = os.path.join(project_root, project, 'id_rsa')

    if len(minion) == 0:
        subprocess.call(['ssh', '-i', ssh_key,
                         '-o', 'StrictHostKeyChecking=no',
                         'ubuntu@%s' % salt_master.get_public_ip()])
    elif len(minion) == 1:
        minion_to_be_connected = minion[0]
        info = salt_master.get_minions_info()
        try:
            subprocess.call(
                ['ssh', '-i', ssh_key,
                 '-o', 'StrictHostKeyChecking=no',
                 'ubuntu@%s' % info[minion_to_be_connected]['public_ip']])
        except KeyError:
            click.echo('minion not exist')
    else:
        click.echo('you could only connect to one minion at a time')


@click.command()
def show():
    '''
    show created project list
    '''
    click.echo(projects)


@click.command()
def saltdoc():
    '''
    salt doc
    '''
    doc_path = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(doc_path, 'salt', 'docs', 'build', 'html', 'splunk.html')
    cmd = 'open %s' % doc_path
    subprocess.call(cmd, shell=True)


def create_master_variables(project):
    variables = dict()
    variables.update(GlobalSetting.read_data())
    variables.update({'project_name': project})
    return variables


main.add_command(up)
main.add_command(browse)
main.add_command(new)
main.add_command(status)
main.add_command(destroy)
main.add_command(version)
main.add_command(delete)
main.add_command(ssh)
main.add_command(config)
main.add_command(rdp)
main.add_command(show)
main.add_command(saltdoc)
