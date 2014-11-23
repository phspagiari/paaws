# -*- coding: utf-8 -*-
from boto import s3


class Userdata(object):
    bucket_name = "tg-infra-automation"
    s3keycheck = "c662c317a9017146fbd86334fd33a8cf"
    s3host = "https://tg-infra-automation.s3.amazonaws.com"
    domain = "titansgroup.net"
    chef_install = "curl -sL http://opscode.com/chef/install.sh | bash"
    get_bootstrap = "curl -sH'Referer: %s' %s/scripts/tgbootstrap.py > /usr/local/bin/tgbootstrap.py" % (s3keycheck, s3host)
    get_databag_key = "curl -sH'Referer: %s' %s/chef/data_bags/data_bag_key > /tmp/data_bag_key" % (s3keycheck, s3host)
    get_chef_solo_conf = "curl -sH'Referer: %s' %s/chef/solo/solo.rb > /tmp/solo.rb" %  (s3keycheck, s3host)
    get_databag_package = "curl -sH'Referer: %s' %s/chef/data_bags/data_bags.tgz > /tmp/data_bags.tgz" % (s3keycheck, s3host)
    get_chef_cookbooks_package = "curl -sH'Referer: %s' %s/chef/cookbooks/cookbooks_master.tgz > /tmp/cookbooks.tgz" % (s3keycheck, s3host)
    get_chef_node = None
    connection = None
    bucket = None
    name = None
    app_type = None
    platform = None
    env = None
    generic_hostname = None
    specific_node = None
    node_name = None
    node = None
    region = "sa-east-1"
    old_method = False

    def __init__(self, region, name=None, app_type=None, platform=None, env=None, old_method=False):
        self.old_method = old_method
        self.name = name
        self.app_type = app_type
        self.platform = platform
        self.env = env
        self.region = region
        self.connection = s3.connect_to_region(region)
        self.bucket = self.connection.get_bucket(self.bucket_name)

        if self.old_method:
            dc = "aws1" if self.region == "sa-east-1" else "aws2"
            self.generic_hostname = "%sn.%s.%sn.%s" % (self.name, self.platform, dc, self.env)
            self.get_bootstrap = "curl -H'Referer: %s' %s/scripts/tgbootstrap-old.py > /usr/local/bin/tgbootstrap.py" % (self.s3keycheck, self.s3host)

        else:
            self.generic_hostname = "%s.%s.%s.%s.%s" %  (self.app_type, self.name, self.platform, self.env, self.region)

        self.node_name = "%s.titansgroup.net.json" % (self.generic_hostname)
        self.node = self.bucket.get_key("chef/nodes/%s" % self.node_name)

        if self.node is not None:
            self.get_chef_node = "curl -H'Referer: %s' %s/chef/nodes/%s > /tmp/node.json" % (self.s3keycheck, self.s3host, self.node_name)
        else:
            raise ValueError("The node (%s) was not found on S3, upload it." % self.node_name)

    def create(self):
        initscript = """#!/bin/bash
#host:{0}
#domain:{1}
###############################
## INIT BOOTSTRAP TITANSGROUP #
###############################

## TGBOOTSTRAP SCRIPT
apt-get install -y --force-yes python-pip
pip install boto --upgrade
{2}

cat > '/etc/init/tgbootstrap.conf' <<EOF
description "TGBOOTSTRAP - Startup script for TitansGroup Instances"
author "Pedro H. Spagiari - infra@titansgroup.com.br"

start on runlevel [2345]
stop on starting rc RUNLEVEL=[016]

setuid root
setgid root

console log
exec python /usr/local/bin/tgbootstrap.py
EOF

CHECK=$(echo -n $(file -i /usr/local/bin/tgbootstrap.py| cut -d":" -f2|cut -d ";" -f1))
[[ $CHECK == "text/x-python" ]] && start tgbootstrap

## CHEF
{3}
{4}
{5}
{6}
{7}
{8}
tar -xvf /tmp/data_bags.tgz -C /tmp/
chef-solo -c /tmp/solo.rb |tee /tmp/chef-run.log
rm -f /tmp/data_bag_key""".format(
            self.generic_hostname,
            self.domain,
            self.get_bootstrap,
            self.chef_install,
            self.get_chef_solo_conf,
            self.get_chef_node,
            self.get_databag_package,
            self.get_chef_cookbooks_package,
            self.get_databag_key
        )
        return initscript
