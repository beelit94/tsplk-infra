# tsplk

It is a command line tool that could let you create Splunk environment for testing.  
The purpose of this tool is that for QA/DEV could get a testable Splunk without knowing  
Vagrant, AWS, Salt, Terraform.


# Installation

### prerequsition
1. _pipsi_  
If you don't use `pipsi`, you're missing out.  
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).  

2. _vagrant_  
download and install from [here](https://www.vagrantup.com/downloads.html)

3. _vagrant plugins_  
    
        vagrant plugin install vagrant-aws
        vagrant plugin install vagrant-winrm-syncedfolders

4. _terraform_

        brew install caskroom/cask/brew-cask
        brew cask install terraform

5. _edit pip conf file_
edit _~/.pip/pip.conf and add the following (if it doesn't exist please create one)
    
        [install]
        extra-index-url = https://pypi.fury.io/m4dy9Unh83NCJdyGHkzY/beelit94/

## how to install tsplk command
### simply run

	pipsi install tsplk

# Usage
## Create a indexer cluster

first, run    
	
	tsplk new

type the info that needed and

    tsplk up <project_name>

this will create a master machine on cloud and
create the rest of the machine through that machine
then, you could use

	tsplk ssh <project_name>

to access splunk web page

## Check the status of the VM you defined
run following command under project's folder

	tsplk status <project_name>

to view all the machine you created

## How to destroy the VM you created

to destroy all the VM you created, run
	
	tsplk destroy <project_name>

