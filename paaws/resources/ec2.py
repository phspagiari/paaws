# -*- coding: utf-8 -*-
from __future__ import print_function
from random import randint

from boto import ec2
from boto.ec2 import networkinterface

from paaws.config import attributes  # WILL BE DEPRECATED
from paaws.vpc import subnets, securitygroups
from paaws.bootstrap import Userdata
from paaws.iam import iam_roles


class Instance(object):
    name = ""
    process = ""
    platform = ""
    env = ""
    region = "sa-east-1"
    zone = None
    instance_class = "t1.micro"
    connection = None
    subnet_id = None
    securitygroup_ids = []
    userdata = None
    destroy_confirmation = True
    instance_ids = []
    instance_tag_filters = {}
    instance_list = False
    public = False

    def __init__(self, name=None, process=None, platform=None, env=None, instance_class=None, region=None, zone=None, instance_ids=[], public=False, instance_list=False):

        self.name = name
        self.process = process
        self.platform = platform
        self.env = env
        self.region = region
        self.zone = zone
        self.instance_class = instance_class
        self.connection = ec2.connect_to_region(self.region)
        self.public = public
        self.instance_ids = instance_ids
        self.instance_list = instance_list

        if instance_list is False and len(instance_ids) > 0:
            pass
        elif instance_list is True:
            pass
        elif instance_list is False and len(instance_ids) == 0:
            if zone is not None:
                self.subnet_id = subnets.get(
                    platform="public" if public else self.platform,
                    region=self.region,
                    zone=self.zone
                )
            else:
                subnet_list = subnets.get(
                    platform="public" if public else self.platform,
                    region=self.region
                )
                list_id = randint(0, len(subnet_list)-1)
                self.subnet_id = subnet_list[list_id]

        self.instance_tag_filters = {
            'tag:Name': self.name,
            'tag:Process': self.process,
            'tag:Environment': self.env,
            'tag:Platform': self.platform,
        }
        #Clear empty tags
        self.instance_tag_filters = {tag: value for (tag, value) in self.instance_tag_filters.iteritems() if value is not None}

    def launch(self):
        userdata = Userdata(name=self.name, app_type=self.process, platform=self.platform, env=self.env, region=self.region)
        self.userdata = userdata.create()

        securitygroup = securitygroups.get_or_create(
            region=self.region,
            name=self.name,
            process=self.process,
            platform=self.platform,
            env=self.env
        )
        self.securitygroup_ids = [securitygroup.id]

        securitygroup = securitygroups.get(
            region=self.region,
            raw_mode=True,
            fullname="general-management-sg"
        )
        self.securitygroup_ids.append(securitygroup.id)

        if self.public:
            interface = networkinterface.NetworkInterfaceSpecification(
                subnet_id=self.subnet_id,
                groups=self.securitygroup_ids,
                associate_public_ip_address=True
            )
            interfaces = networkinterface.NetworkInterfaceCollection(interface)
        else:
            interfaces = None

        reservation = self.connection.run_instances(
            attributes.ami[self.region],
            key_name=attributes.key[self.region],
            instance_type=self.instance_class,
            subnet_id=None if self.public else self.subnet_id,
            user_data=self.userdata,
            instance_profile_name=iam_roles.get(self.name, self.platform, self.env),
            security_group_ids=None if self.public else self.securitygroup_ids,
            block_device_map=attributes.bdm,
            network_interfaces=interfaces
        )

        return reservation.instances[0]

    def get(self):
        if len(self.instance_ids) > 0:
            reservations = self.connection.get_all_instances(
                instance_ids=self.instance_ids
                )
        else:
            reservations = self.connection.get_all_instances(
                filters=self.instance_tag_filters
            )

        instances = [instance for reservation in reservations for instance in reservation.instances]

        if len(instances) > 0:
            if self.instance_list:
                return instances
            else:
                return instances[0]

        return None

    def destroy(self):
        instance = self.get()
        instance_id = instance.id

        if instance_id is not None:
            if self.destroy_confirmation:
                if raw_input('Are you sure to delete %s? [y/N] ' % instance_id) != 'y':
                    return 'Aborted'

            self.connection.terminate_instances(instance_ids=[instance_id], dry_run=False)
            return "Instance %s terminated" % (instance_id)

        return "Instance with id %s not found." % (instance_id)


def get_instances_data(region, instance_ids=[], list_instances=False, name=None, process=None, platform=None, env=None):
    if list_instances:
        if len(instance_ids) > 0:
            instances = Instance(
                instance_list=True,
                instance_ids=instance_ids,
                region=region
            )
            instances = instances.get()

        else:
            instances = Instance(
                instance_list=True,
                name=name,
                process=process,
                platform=platform,
                env=env,
                region=region
            )
            instances = instances.get()

        if (instances is not None) and (len(instances) > 0):
            header = ["ID", "IP", "Name", "Process", "Platform", "Env", "Launch Time", "InstanceType", "State"]
            instance_data = []

            for instance in instances:
                instance_data.append([
                    instance.id,
                    instance.private_ip_address,
                    instance.tags['Name'] if 'Name' in instance.tags else "",
                    instance.tags['Process'] if 'Process' in instance.tags else "",
                    instance.tags['Platform' if 'Platform' in instance.tags else ""],
                    instance.tags['Environment'] if 'Environment' in instance.tags else "",
                    ' - '.join(str(instance.launch_time).split('.')[0].split('T')),
                    instance.instance_type,
                    instance.state
                ])

            instance_data.insert(0, header)
            instance_data = {col[0]: col[1:] for col in zip(*instance_data)}

            return instance_data

        return "0 Instances Found"

    else:
        if len(instance_ids) > 0:
            instance = Instance(
                instance_ids=instance_ids,
                region=region
            )
            instance = instance.get()
        else:
            instance = Instance(
                name=name,
                process=process,
                platform=platform,
                env=env,
                region=region
            )
            instance = instance.get()

        if instance is not None:
            header = [instance.id, "Data"]
            instance_data = []
            instance_data.append(["Name", instance.tags['Name'] if 'Name' in instance.tags else ""])
            instance_data.append(["Private IP", instance.private_ip_address])
            instance_data.append(["State", instance.state])
            instance_data.append(["Type", instance.instance_type])
            instance_data.append(["Region", instance.placement])
            instance_data.append(["AMI", instance.image_id])
            instance_data.append(["Key", instance.key_name])
            instance_data.append(["Subnet ID", instance.subnet_id])
            instance_data.append(["VPC ID", instance.vpc_id])
            instance_data.append(["EBS Optimized", instance.ebs_optimized])
            try:
                instance_data.append(["ARN", instance.instance_profile['arn']])
            except:
                instance_data.append(["ARN", " - "])
            for interface in instance.interfaces:
                instance_data.append(["IPs %s" % interface.id, ' '.join([ str(ip.private_ip_address) for ip in interface.private_ip_addresses])])
            instance_data.append(["Launch Time", ' - '.join(str(instance.launch_time).split('.')[0].split('T'))])
            instance_data.append(["Public IP", instance.ip_address])
            instance_data.append(["Public DNS", instance.public_dns_name])

            instance_data.insert(0, header)
            instance_data = {col[0]: col[1:] for col in zip(*instance_data)}
            return instance_data

    return None
