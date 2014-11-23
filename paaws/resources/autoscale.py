#!/usr/bin/env python
from __future__ import print_function
from time import sleep

from boto.ec2 import autoscale
from boto import exception

from paaws.config import Config, attributes
from paaws.bootstrap import Userdata
from paaws.iam import iam_roles
from paaws.vpc import subnets, securitygroups
from paaws.sns import get_sns_topic_arn


class Scale(object):
    old_method = False
    scale_name = None
    name = None
    process = None
    platform = None
    env = None
    region = None
    availability_zones = []
    instance_class = None
    desired_capacity = None
    minimum = None
    maximum = None
    connection = None
    elb = None
    destroy_confirmation = True
    launch_config_list = []
    userdata = None
    autoscale_update = False
    launchconfig_update = False

    def __init__(
        self, old_method=False, destroy_confirmation=True, autoscale_update=False,
        launchconfig_update=False, scale_name=None, name=None, process=None, platform=None,
        env=None, region=None, minimum=None, maximum=None, instance_class=None, desired_capacity=None,
        elb=None, ami_id=None, public=False
    ):

        config = Config()

        self.old_method = old_method
        self.autoscale_update = autoscale_update
        self.launchconfig_update = launchconfig_update
        self.name = name
        self.process = process
        self.platform = platform
        self.env = env
        self.region = region
        self.instance_class = instance_class
        self.desired_capacity = desired_capacity
        self.minimum = minimum
        self.maximum = maximum
        self.connection = autoscale.connect_to_region(self.region)
        self.availability_zones = attributes.availability_zones[self.region]
        self.ami_id = ami_id if ami_id is not None else config.ami[self.region]
        self.public = public

        if scale_name is not None:
            self.scale_name = "asg-%s" % scale_name
            hostname = self.scale_name.replace("asg-", "").split("-")
            self.name = hostname[0]
            self.platform = hostname[1]
            self.env = hostname[3]

            for lc in self.get_all_launch_configs():
                if scale_name in lc.name:
                    self.launch_config_list.append(lc)

            if len(self.launch_config_list) > 0:
                self.launch_config_name = sorted(self.launch_config_list, key=lambda lc: lc.created_time)[-1].name
            else:
                self.launch_config_name = "alc1-%s" % scale_name

        else:
            for lc in self.get_all_launch_configs():
                if "%s-%s-%s-%s" % (self.process, self.name, self.platform, self.env) in lc.name:
                    self.launch_config_list.append(lc)

                if len(self.launch_config_list) == 0:
                    lc_number = 1
                elif len(self.launch_config_list) > 0:
                    lc_number = len(self.launch_config_list)

            self.launch_config_name = "config%s-%s-%s-%s-%s" % (
                lc_number, self.process, self.name, self.platform, self.env
            )
            self.scale_name = "scale-%s-%s-%s-%s" % (self.process, self.name, self.platform, self.env)
            self.elb = elb

    def get_all_launch_configs(self, token=None):
        alc = self.connection.get_all_launch_configurations(next_token=token)
        if alc.next_token is None:
            return alc
        else:
            return alc + self.get_all_launch_configs(token=alc.next_token)

    def get_launch_config(self):
        launch_configs = self.connection.get_all_launch_configurations(names=[self.launch_config_name])

        if len(launch_configs) > 0:
            return launch_configs[0]

        return None

    def create_launch_config(self):

        config = Config()

        if self.old_method:
            userdata = Userdata(
                old_method=self.old_method, name=self.name, platform=self.platform, env=self.env, region=self.region
            )
            securitygroup = securitygroups.get_or_create(
                region=self.region,
                raw_mode=True,
                fullname="%s-%s-%s-sg" % (self.name, self.platform, self.env)
            )
            securitygroup_ids = [securitygroup.id]

        else:
            userdata = Userdata(
                name=self.name, app_type=self.process, platform=self.platform, env=self.env, region=self.region
            )
            securitygroup = securitygroups.get_or_create(
                region=self.region,
                name=self.name,
                process=self.process,
                platform=self.platform,
                env=self.env
            )
            securitygroup_ids = [securitygroup.id]

        self.userdata = userdata.create()

        securitygroup = securitygroups.get(
            region=self.region,
            raw_mode=True,
            fullname="general-management-sg"
        )
        securitygroup_ids.append(securitygroup.id)

        launch_config = autoscale.LaunchConfiguration(
            name=self.launch_config_name,
            image_id=self.ami_id,
            key_name=config.key[self.region],
            instance_type=self.instance_class,
            security_groups=securitygroup_ids,
            instance_profile_name=iam_roles.get(self.name, self.platform, self.env),
            user_data=self.userdata,
            block_device_mappings=[attributes.bdm],
            associate_public_ip_address=self.public
        )
        self.connection.create_launch_configuration(launch_config)

        return launch_config

    def get_or_create_launch_config(self):
        launch_config = self.get_launch_config()
        if launch_config is not None:
            return launch_config

        launch_config = self.create_launch_config()
        return launch_config

    def create_notifications(self):
        sns_topics = get_sns_topic_arn(platform=self.platform, region=self.region)
        for sns_topic in sns_topics:
            self.connection.put_notification_configuration(
                autoscale_group=self.scale_name,
                topic=sns_topic,
                notification_types=[
                    'autoscaling:EC2_INSTANCE_LAUNCH',
                    'autoscaling:EC2_INSTANCE_LAUNCH_ERROR',
                    'autoscaling:EC2_INSTANCE_TERMINATE',
                    'autoscaling:EC2_INSTANCE_TERMINATE_ERROR',
                    'autoscaling:TEST_NOTIFICATION',
                ]
            )
        return True

    def create(self):
        launch_config = self.get_or_create_launch_config()
        subnet_ids = [subnet for subnet in subnets.get(platform="public" if self.public else self.platform, region=self.region)]
        if self.public:
            try:
                subnet_ids.remove('subnet-0c9eea65')  # RIDICULOUS HARDCODED FIX (3 SUBNETS PUBLIC)
            except ValueError:
                pass

        autoscale_group = autoscale.AutoScalingGroup(
            name=self.scale_name,
            launch_config=launch_config,
            availability_zones=self.availability_zones,
            desired_capacity=self.desired_capacity,
            min_size=self.minimum,
            max_size=self.maximum,
            termination_policies=['OldestInstance'],
            load_balancers=[self.elb],
            vpc_zone_identifier=','.join(subnet_ids),
            connection=self.connection
        )

        self.connection.create_auto_scaling_group(autoscale_group)
        self.create_notifications()

        return autoscale_group

    def get_scale(self):
        autoscale_group = self.connection.get_all_groups(names=[self.scale_name])

        if len(autoscale_group) > 0:
            return autoscale_group[0]

        return None

    def destroy(self):
        autoscale_group = self.get_scale()

        if autoscale_group is not None:
            if self.destroy_confirmation:
                if raw_input('Are you sure to delete %s group? [y/N] ' % self.scale_name) != 'y':
                    return 'Aborted'

            autoscale_group.delete(force_delete=True)

            if len(self.launch_config_list) > 0:
                for launch_config in self.launch_config_list:
                    launch_config.delete()

            return "Deleted the %s group and %s Launch Configurations. [ %s ]" % (
                self.scale_name, self.launch_config_name, ', '.join(self.launch_config_list)
            )

        return "The specified group %s dont exist." % self.scale_name

    def update(self):
        if self.autoscale_update:
            autoscale_group = self.get_scale()
            if autoscale_group is not None:
                autoscale_group.desired_capacity = self.desired_capacity
                autoscale_group.update()
                return "Updated the desired capacity to %s for group %s." % (
                    str(self.desired_capacity), self.scale_name
                )
            return "Autoscale not found"

        elif self.launchconfig_update:
            launch_config = self.get_launch_config()
            if self.instance_class is None:
                self.instance_class = launch_config.instance_type

            if launch_config is not None:
                lc_number = len(self.launch_config_list)+1

                if "alc" in launch_config.name:
                    self.launch_config_name = "alc%s-%s" % (lc_number, self.scale_name.replace("asg-", ""))
                elif "config"in launch_config.name:
                    self.launch_config_name = "config%s-%s-%s-%s-%s" % (
                        lc_number, self.process, self.name, self.platform, self.env
                    )

                new_launch_config = self.create_launch_config()

                autoscale_group = self.get_scale()
                autoscale_group.launch_config_name = new_launch_config.name
                autoscale_group.update()
                return "Updated the launch config %s of %s." % (self.launch_config_name, self.scale_name)
            return "Launchconfig not found"
        return "Nothing updated, autoscale or launchconfig must be True"


def list_all_groups(region):
    header = ["Name", "LaunchConfig", "Instances", "Instance Class", "Desired", "Min", "Max", "Region"]
    asg_data = []
    asconn = autoscale.connect_to_region(region)
    autoscaling_groups = [asg for asg in asconn.get_all_groups()]
    for asg in autoscaling_groups:
        try:
            asg_instance_class = asconn.get_all_launch_configurations(names=[asg.launch_config_name])[0].instance_type
        except exception.BotoServerError as err:
            if err.message == "Rate exceeded":
                sleep(3)
                asg_instance_class = asconn.get_all_launch_configurations(names=[asg.launch_config_name])
                asg_instance_class = asg_instance_class[0].instance_type
        asg_name = asg.name.replace("asg-", "")
        asg_lc = asg.launch_config_name
        asg_instances = len(asg.instances)
        asg_desired = asg.desired_capacity
        asg_min = asg.min_size
        asg_max = asg.max_size
        asg_region = region
        asg_data.append([
            asg_name,
            asg_lc,
            asg_instances,
            asg_instance_class,
            asg_desired,
            asg_min,
            asg_max,
            asg_region
        ])
    asg_data.insert(0, header)
    asg_data = {col[0]: col[1:] for col in zip(*asg_data)}
    return asg_data


def describe_group(name, old_method=False):
    if old_method:
        asg_name = "asg-%s" % name
    else:
        asg_name = name

    for region in [region.name for region in attributes.regions]:
        asconn = autoscale.connect_to_region(region)
        asg = asconn.get_all_groups(names=[asg_name])
        if len(asg) > 0:
            if asg[0].name == asg_name:
                break
    try:
        autoscaling_group = asg[0]
        header = [autoscaling_group.name, "Information"]
        asg_data = []
    except IndexError as e:
        raise ValueError("Invalid autoscaling group name %s. Error: %s" % (asg_name, e))

    instances = ["%s - %s" % (instance.instance_id, instance.health_status) for instance in autoscaling_group.instances]

    asg_data.append(["ARN", autoscaling_group.autoscaling_group_arn])
    asg_data.append(["Desired Capacity", autoscaling_group.desired_capacity])
    asg_data.append(["LaunchConfig", autoscaling_group.launch_config_name])
    asg_data.append(["Min Size", autoscaling_group.min_size])
    asg_data.append(["Max Size", autoscaling_group.max_size])
    asg_data.append(["Termination Policy", str(autoscaling_group.termination_policies[0])])
    asg_data.append(["Instances", ', '.join(instances)])
    asg_data.insert(0, header)
    asg_data = {col[0]: col[1:] for col in zip(*asg_data)}
    return asg_data


def describe_group_instances(name):
    asg_name = "asg-%s" % name

    for region in [region.name for region in attributes.regions]:
        asconn = autoscale.connect_to_region(region)
        asg = asconn.get_all_groups(names=[asg_name])
        if len(asg) > 0:
            if asg[0].name == asg_name:
                break
    try:
        autoscaling_group = asg[0]
    except IndexError as e:
        raise ValueError("Invalid autoscaling group name %s. Error: %s" % (asg_name, e))

    instances = [instance.instance_id for instance in autoscaling_group.instances]

    return instances
