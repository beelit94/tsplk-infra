# tsplk

It is a command line tool that could let you create Splunk environment for testing.
The purpose of this tool is that for QA/DEV could get a testable Splunk without knowing
Vagrant, AWS, Salt, Terraform.


# Installation

### Prerequsition
1. _pipsi_


        curl https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py | python

2. _homebrew_


        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

3. _terraform_

        brew install caskroom/cask/brew-cask
        brew cask install terraform

4. _edit pip conf file_
edit `~/.pip/pip.conf` and add the following (if it doesn't exist please create one)

        [install]
        extra-index-url = https://pypi.fury.io/m4dy9Unh83NCJdyGHkzY/beelit94/

### Install tsplk command

    pipsi install tsplk


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
