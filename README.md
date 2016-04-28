# tsplk

It is a command line tool that could let you create a Splunk environment for testing.

The purpose of this tool is that for QA/DEV could get a testable Splunk ASAP.


# Installation

### Supported platform of cmd tool

Right now we only tested on MAC.

### Prerequsition
1. _pipsi_ (optional)

    > [pipsi](https://github.com/mitsuhiko/pipsi) is a wrapper around virtualenv and pip
    >
    > which installs scripts provided by python packages into separate virtualenvs to shield them from your system and each other.
    >
    > This is a nice to have for user who has multiple python command line tools installed and you need to avoid conflict between requirements.
    >
    > However, several users reported that they couldn't install pipsi successfully.
    >
    > If you can't install it, just skip it.

        curl https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py | python

2. [_homebrew_](http://brew.sh/) (optional, simplified the installation of terraform)

        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

3. [_terraform_](https://www.terraform.io/)

    if you have homebrew installed,

        brew install terraform

    if you don't have homebrew installed, follow [this](https://www.terraform.io/intro/getting-started/install.html)

4. _edit pip conf file_
edit `~/.pip/pip.conf` and add the following (if it doesn't exist please create one)

        [install]
        extra-index-url = https://pypi.fury.io/m4dy9Unh83NCJdyGHkzY/beelit94/

### Install tsplk command
If you have pipsi installed,

    pipsi install tsplk

If you don't have pipsi installed,

    sudo pip install tsplk

### Running tsplk at the very first time

1. Ask for AWS access key and secret key from [admin](emailto:ftan@splunk.com)
1. Go [here](https://hipchat.splunk.com/account/api) to get your HipChat token
with `view group` scope, token label could be anything
1. Enter `tsplk` room in the hipchat, and adjust your room notification to `quiet`
![](https://s3-us-west-2.amazonaws.com/tsplk/StaticResources/hipchat_room_notification.png)
1. Run `tsplk config` and input the information

# Upgrade

If you install tsplk through pipsi,

    pipsi upgrade tsplk
     
If you install tsplk through pip,

    sudo pip install --upgrade tsplk 
    
# Uninstall

If you install tsplk through pipsi,

    pipsi uninstall tsplk
     
If you install tsplk through pip,

    sudo pip uninstall tsplk

# Usage
### How to create a Splunk environment

1. Simply use `tsplk new` and follow the instruction
2. Use `tsplk up` to bring up the project you just create

        tsplk up <project_name>

### Check the status of the VM you defined
run the following command

    tsplk status <project_name>

to view the public-ip, private-ip and name of all the machines you created

### How to access your VM

to access saltmaster

    tsplk ssh <project_name>

to access the Splunk instance

    tsplk ssh <project_name> <minion_id>

### How to destroy the VM you created

to destroy all the VM you created, run

    tsplk destroy <project_name>

to delete your project from project list, use

    tsplk delete <project_name>

# TroubleShooting
### keyring.backends._OS_X_API.Error

If you see this error `keyring.backends._OS_X_API.Error: (-25293, "Can't fetch password from system")`

We're not sure what's the root cause of this

Please try to reinstall tsplk with `pip` instead of `pipsi`

# How to get involved
### Report bug

report bug to project SQA with component = Salt, [report here](https://jira.splunk.com/secure/CreateIssueDetails!init.jspa?pid=12521&issuetype=1&components=Salt)

### Project dependency

tsplk is a command line tool depend on several projects

1. [packer-for-tsplk](https://git.splunk.com/users/ftan/repos/packer-for-tsplk/browse)
2. [salty-splunk](https://git.splunk.com/projects/SUSTAIN/repos/salty-splunk/browse)

### How to release

1. install sphinx: pip install sphinx
1. export FURY_URL=`private url, ask ftan`
1. under develope branch
1. create branch release/`version`
1. run `python release.py --release <major, minor, patch>`
1. commit updated version file and changelog
1. merge release version back to master and develope, tag master branch with version