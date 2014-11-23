# -*- coding: utf-8 -*-
#

from __future__ import print_function

import os

from boto import ec2
from fabric.colors import red
from fabric.api import env, run, task, parallel, sudo, execute
from fabric.contrib.files import sed
from fabric.context_managers import settings


def run_task(func):
    def _run_task(region, autoscaling_group=None, instances_ips=None, *args, **kwargs):
        if autoscaling_group is not None:
            hosts = get_ec2_instances_ips(autoscaling_group, region)
        elif instances_ips is not None:
            hosts = instances_ips
        else:
            raise ValueError("0 instances to run task")
        user = os.environ.get('SSH_USER', os.environ.get('USER'))
        with settings(hosts=hosts, user=user):
            execute(func, *args, **kwargs)
    return _run_task


@run_task
@task
def deploy(revision=None):
    if revision is not None and env.name != 'production':
        sudo('curl -sL 169.254.169.254/latest/user-data | egrep -v \'chef-run|apt-get|pip|opscode.com\' | sudo bash')
        sed('/tmp/node.json', '("revision":)[^\,]*(\,)?', '\\1 "%s"\\2' % revision, use_sudo=True)
        sudo('chef-solo -c /tmp/solo.rb | tee /tmp/chef-run.log')
    else:
        run('curl -sL 169.254.169.254/latest/user-data | egrep -v \'apt-get|pip|opscode.com\' | sudo bash')


@run_task
@task
@parallel
def cmd(command=None, is_sudo=False):
    if is_sudo:
        sudo(command)
    else:
        run(command)


@run_task
@task
@parallel
def logs(appname, grep_value=None):
    """
    Run tail command in all logs
    """
    print(red("You really should be using Splunk at this moment."))
    logs = [
        '/var/log/apps/%s/*.log' % (appname),
        '/var/log/nginx/*.log',
        '/var/log/upstart/%s*.log' % (appname),
    ]
    tailf = 'tail -f %s | grep -vi newrelic' % ' '.join(logs)

    if grep_value is not None:
        tailf += ' | grep "%s"' % grep_value

    sudo(tailf)


# Process management
@run_task
@task
def start():
    sudo('chef-solo -c /tmp/solo.rb -o recipe[python-app::start]')


@run_task
@task
def stop():
    sudo('chef-solo -c /tmp/solo.rb -o recipe[python-app::stop]')


@run_task
@task
def restart():
    sudo('chef-solo -c /tmp/solo.rb -o recipe[python-app::restart]')


def get_ec2_instances_ips(autoscaling_group, region):
    connection = ec2.connect_to_region(region)
    instance_ids = [inst.instance_id for inst in autoscaling_group.instances]
    instances = [instance for r in connection.get_all_instances(instance_ids=instance_ids) for instance in r.instances if instance.state == 'running']

    return [i.private_ip_address for i in sorted(instances, key=lambda i: i.launch_time)]
