# tsplk

It is a command line tool that could let you create a Splunk environment for testing.

The purpose of this tool is that for QA/DEV could get a testable Splunk without knowing
Vagrant, AWS, Salt, Terraform.


# Installation

### Prerequsition
1. _pipsi_ (optional)

> [pipsi](https://github.com/mitsuhiko/pipsi) is a wrapper around virtualenv and pip which installs scripts provided by python packages into separate virtualenvs to shield them from your system and each other. 
> This is a nice to have for user who use python command heavily. 
> However, there are several user report that they can't install it successfully. 
> If you can't install it, you could just skip it.


        curl https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py | python

2. _homebrew_(optional, simplified the installation of terraform)

        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

3. _terraform_

    if you have homebrew installed,

        brew install caskroom/cask/brew-cask
        brew cask install terraform

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

1. ask for AWS access key, secret key and atlas token from admin
1. get your HipChat name
1. run `tsplk config` and input the information

# Upgrade

If you have pipsi installed,

    pipsi upgrade tsplk
     
If you don't have pipsi installed,

    sudo pip install --upgrade tsplk 

# Usage
### How to create a Splunk environment

1. Simply use `tsplk new` and follow the instruction
2. Use `tsplk up` to bring up the project you just create

        tsplk up <project_name>

### Check the status of the VM you defined
run following command under project's folder

    tsplk status <project_name>

to view all the machine you created

### How to access your VM

to access master

    tsplk ssh <project_name>

access the Splunk instance

    tsplk ssh <project_name> <minion_id>

### How to destroy the VM you created

to destroy all the VM you created, run

    tsplk destroy <project_name>

to delete your project from project list, use

    tsplk delete <project_name>

# Examples
### Indexer clustering

1. do `tsplk new`
2. You will be asked to enter a project name. Please type what ever you want. Say, clustering here.
3. You will be asked to enter the splunk version. say 6.3.2 here
4. Choose the platform you want to test
5. Enter 0 for indexer cluster
6. Enter number of slaves, search heads you want
7. Enter the replication factor and search factor you want
8. do `tsplk up clustering`, tsplk will bring your instances up

# How to get involved
### report bug

report bug to project SQA with component = Salt
https://jira.splunk.com/secure/CreateIssueDetails!init.jspa?pid=12521&issuetype=1&components=Salt

### submodule

tsplk is a command line tool depend on several projects

1. salty-packer
2. salty-splunk

### How to release

1. export FURY_URL=`private url, ask ftan`
1. under develope branch
1. create branch release/`version`
1. run `python release.py --release <major, minor, patch>`
1. commit updated version file and changelog
1. merge release version back to master and develope, tag master branch with version