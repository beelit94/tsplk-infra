import subprocess
import json
import yaml
import pycurl
import time
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

minion_info_path = 'terraform.tfstate'
project_setting_file = 'settings.yml'
terraform_variables = 'minion_terraform_variables'
minion_roles_map_file = 'minion_roles_map'


def read_project_setting_data():
    with open(project_setting_file) as f:
        data = yaml.load(f)

    return data


def get_minions_info():
    with open(minion_info_path) as f:
        remote_data = json.load(f)

    instances = []
    for k, v in remote_data['modules'][0]['resources'].iteritems():
        if 'aws_instance' in k:
            instances.append({'name': k, 'info': v['primary']['attributes']})

    return instances


def read_terraform_variables():
    with open(terraform_variables) as f:
        gs = json.load(f)
    return gs


def gen_roles_salt_command(roles):
    '''
    :param roles: ex. roles = {'role1': count1, 'role2': count2}
    :param instances:
    :return:
    '''
    instances = get_minions_info()

    total = 0
    for role, count in roles.iteritems():
        total += count

    assert total == len(instances)

    commands = []
    roles_mapping = dict()
    for role, count in roles.iteritems():
        ready_to_assign = instances[:count]
        instances = instances[count:]

        for minion in ready_to_assign:
            minion_id = minion['info']['tags.Name']
            commands.append("sudo salt %s grains.append role %s" % (minion_id, role))
            roles_mapping[str(minion['name'])] = str(role)

    with open(minion_roles_map_file, 'w') as f:
        yaml.dump(roles_mapping, f, default_flow_style=False)

    return commands


def gen_provision_commands(splunk_architecture):
    cmds = [
        "sudo salt '*' saltutil.sync_all",
        "sudo salt-run state.orch orchestration.%s" % splunk_architecture
    ]

    return cmds


def notify_when_finished(user, project_name, token):
    room = '1957'
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://hipchat.splunk.com/v2/room/%s/notification?auth_token=%s' % (room, token))

    post_data = {'color': 'red', 'message_format': 'text', 'message': '@%s %s is ready' % (user, project_name)}
    # Form data must be provided already urlencoded.
    postfields = urlencode(post_data)
    # Sets request method to POST,
    # Content-Type header to application/x-www-form-urlencoded
    # and data to send in request body.
    c.setopt(c.POSTFIELDS, postfields)

    c.perform()
    c.close()


def main():
    """

    :rtype: object
    """

    tf_vars = read_terraform_variables()
    hipchat_token = tf_vars['hipchat_token']
    tf_vars.pop('hipchat_token')
    prj_settings = read_project_setting_data()

    str_t = []
    for k, v in tf_vars.iteritems():
        str_t += ['-var'] + ["%s=%s" % (k, v)]

    subprocess.call(['./terraform/terraform', 'apply'] + str_t)
    cmds = gen_roles_salt_command(prj_settings['roles_count'])

    for cmd in cmds:
        subprocess.call(cmd, shell=True)

    cmds = gen_provision_commands(prj_settings['splunk_architecture'])

    time.sleep(30)
    for cmd in cmds:
        subprocess.call(cmd, shell=True)

    notify_when_finished(tf_vars['username'], prj_settings['project_name'], hipchat_token)


if __name__ == '__main__':
    main()
