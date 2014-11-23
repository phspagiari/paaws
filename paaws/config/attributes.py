# -*- coding: utf-8 -*-
import re

from boto import ec2

account_id = "464526076120"
regions = [region for region in ec2.regions() if re.match('(us|sa)(-east-1)', region.name)]
ami = {regions[1].name: 'ami-a4fb5eb9', regions[0].name: 'ami-e7582d8e'}
key = {regions[1].name: '464526076120', regions[0].name: '464526076120-us'}
uszones = [regions[1].name+'b', regions[1].name+'c']
sazones = [regions[0].name+'a', regions[0].name+'b']

hostname = 'set.the.hostname.amateur'
short = hostname.split('.')[0]
platform = hostname.split('.')[1]
datacenter = hostname.split('.')[2]
environment = hostname.split('.')[3]

knownshorts = ['api', 'web', 'worker', 'scheduler', 'reports', 'mq', 'search']
knownplatforms = ['billing', 'listing', 'messaging', 'learning', 'security', 'cloud', 'common', 'ops', 'corp']
knownenvironments = ['prod', 'qa', 'uat', 'stg', 'dev']
knowndatacenters = ['aws1', 'aws2']
knownregionidentifiers = ['1', '2']

############# DYNAMIC ATTRIBUTES ######################
regions = [region for region in ec2.regions() if re.match('(us|sa)(-east-1)', region.name)]
availability_zones = {'us-east-1': ['us-east-1b', 'us-east-1c'], 'sa-east-1': ['sa-east-1a', 'sa-east-1b']}

ami = {regions[1].name: 'ami-a4fb5eb9', regions[0].name: 'ami-e7582d8e'}
key = {regions[1].name: '464526076120', regions[0].name: '464526076120-us'}
iamroles = {'default': 'default-iam-role'}

dev_sda1 = ec2.blockdevicemapping.EBSBlockDeviceType(delete_on_termination=True)
dev_sda1.size = 60
bdm = ec2.blockdevicemapping.BlockDeviceMapping()
bdm['/dev/sda1'] = dev_sda1
