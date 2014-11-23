# -*- coding: utf-8 -*-

from __future__ import print_function

from boto import ec2, iam
from boto.ec2 import elb
from boto.exception import BotoServerError

from paaws.vpc import subnets, securitygroups


class ElasticLoadBalancer(object):
    def __init__(self, name, process, platform, env, region, domain=None, public=False):
        self.name = name
        self.process = process
        self.platform = platform
        self.env = env
        self.loadbalancer_name = "%s-%s-%s-%s" % (self.process, self.name, self.platform, self.env)
        self.region = region
        self.connection = elb.connect_to_region(self.region)
        self.interval = 10
        self.healthy_threshold = 3
        self.unhealthy_threshold = 5
        self.target = 'HTTP:80/'
        self.listeners = {
            '80': [(80, 80, 'http')],
            '443': [(80, 80, 'http'), (443, 80, 'https')]
        }
        self.domain = domain
        self.listener = self.listeners['80']
        self.public = public

    def _put_certificates_into_listener(self):
        iam_connection = iam.connect_to_region('universal')
        certificates = iam_connection.get_all_server_certs()['list_server_certificates_response']['list_server_certificates_result']['server_certificate_metadata_list']
        for certificate in certificates:
            if certificate['server_certificate_name'] == self.domain:
                listener = self.listeners['443']
                listener_ssl = listener[1]
                listener_ssl = listener_ssl + (certificate['arn'],)
                listener.pop()
                listener.append(listener_ssl)
                self.listener = listener
                return True
        return False

    def create_health_check(self):
        health_check = elb.healthcheck.HealthCheck(
            access_point=self.loadbalancer_name,
            interval=self.interval,
            healthy_threshold=self.healthy_threshold,
            unhealthy_threshold=self.unhealthy_threshold,
            target=self.target
        )

        return health_check

    def create(self):
        if self.domain is not None:
            response = self._put_certificates_into_listener()
            if not response:
                raise Exception("You specified a domain for SSL but you net to upload first into IAM")

        securitygroup = securitygroups.get_or_create(
            region=self.region,
            name=self.name,
            process="%s-%s" % ("elb", self.process),
            platform=self.platform,
            env=self.env
        )
        securitygroup_ids = [securitygroup.id]

        if self.public:
            subnet_ids = [subnet for subnet in subnets.get(platform="public", region=self.region)]
        else:
            subnet_ids = [subnet for subnet in subnets.get(platform=self.platform, region=self.region)]

        loadbalancer = self.connection.create_load_balancer(
            name=self.loadbalancer_name,
            zones=None,
            listeners=self.listener,
            subnets=subnet_ids,
            security_groups=securitygroup_ids,
            scheme=None if self.public else "internal"
        )

        hc = self.create_health_check()
        loadbalancer.configure_health_check(hc)
        return loadbalancer

    def get(self):
        try:
            loadbalancers = self.connection.get_all_load_balancers(
                load_balancer_names=[self.loadbalancer_name]
            )
            if len(loadbalancers) > 0:
                return loadbalancers[0]
            return None

        except BotoServerError as err:
            if "Cannot find" in err.message:
                return None

    def get_or_create(self):
        loadbalancer = self.get()

        if loadbalancer is not None:
            return loadbalancer

        loadbalancer = self.create()
        return loadbalancer

    def delete(self):
        loadbalancer = self.get()
        if loadbalancer is not None:
            if len(loadbalancer.instances) == 0:
                loadbalancer.delete()
                return "Loadbalancer %s deleted" % self.loadbalancer_name
            else:
                return "You have %s instances into this loadbalancer (%s) and its not will be deleted." % (
                    len(loadbalancer.instances), ", ".join([str(instance.id) for instance in loadbalancer.instances])
                )
        return "Loadbalancer not found"

    def add_instance(self, instance_id):
        loadbalancer = self.get()
        if loadbalancer is not None:
            instances = self.connection.register_instances(
                load_balancer_name=self.loadbalancer_name,
                instances=[instance_id]
            )
            return "Added %s" % instance_id if instance_id in instances else "Instance %s not added" % instance_id
        return "Provide a valid loadbalancer"

    def remove_instance(self, instance_id):
        loadbalancer = self.get()
        if loadbalancer is not None:
            instances = self.connection.deregister_instances(
                load_balancer_name=self.loadbalancer_name,
                instances=[instance_id]
            )
            return "Removed %s" % instance_id if instance_id not in instances else "Instance %s not removed" % instance_id
        return "Provide a valid loadbalancer"
