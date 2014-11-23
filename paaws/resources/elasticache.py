# -*- coding: utf-8 -*-

from boto import elasticache
from boto import exception

from paaws.vpc import subnets, securitygroups
from paaws.sns import get_sns_topic_arn


class ElasticCache(object):
    name = None
    platform = None
    process = "cache"
    env = None
    region = None
    zone = None
    cache_instance_class = None
    cache_name = None
    connection = None
    subnet_group = None
    securitygroup_ids = None
    parameter_group = None
    nodes = 1
    destroy_confirmation = True

    def __init__(self, name, platform, env, region, cache_instance_class=None, nodes=1, destroy_confirmation=True):
        self.name = name
        self.platform = platform
        self.env = env
        self.cache_name = "%s-%s" % (self.name, self.env)
        if len(self.cache_name) > 20:
            raise ValueError("The cache cluster name must have less than 20 characters")
        self.region = region
        self.cache_instance_class = cache_instance_class
        self.connection = elasticache.connect_to_region(self.region)
        self.nodes = 1

    def create_cache_parameter_group(self):
        cache_parameter_group = self.connection.create_cache_parameter_group(
            cache_parameter_group_name=self.cache_name,
            cache_parameter_group_family="memcached1.4",
            description=self.cache_name
        )
        return cache_parameter_group['CreateCacheParameterGroupResponse']['CreateCacheParameterGroupResult']['CacheParameterGroup']['CacheParameterGroupName']

    def get_cache_parameter_group(self):
        try:
            return self.connection.describe_cache_parameter_groups(cache_parameter_group_name=self.cache_name)['DescribeCacheParameterGroupsResponse']['DescribeCacheParameterGroupsResult']['CacheParameterGroups'][0]['CacheParameterGroupName']

        except exception.BotoServerError as err:
            if err.code != "CacheParameterGroupNotFound":
                raise Exception(err.code)

        return None

    def get_or_create_cache_parameter_group(self):
        cache_parameter_group = self.get_cache_parameter_group()

        if cache_parameter_group is not None:
            return cache_parameter_group

        cache_parameter_group = self.create_cache_parameter_group()
        return cache_parameter_group

    def create_cache_subnet_group(self):
        cache_subnet_group = self.connection.create_cache_subnet_group(
            cache_subnet_group_name="subnetgroup-%s" % self.platform,
            cache_subnet_group_description="ElastiCache SubnetGroup of %s" % self.platform,
            subnet_ids=subnets.get(self.platform, self.region)
        )
        return cache_subnet_group['CreateCacheSubnetGroupResponse']['CreateCacheSubnetGroupResult']['CacheSubnetGroup']['CacheSubnetGroupName']

    def get_cache_subnet_group(self):
        try:
            return self.connection.describe_cache_subnet_groups(cache_subnet_group_name="subnetgroup-%s" % self.platform)['DescribeCacheSubnetGroupsResponse']['DescribeCacheSubnetGroupsResult']['CacheSubnetGroups'][0]['CacheSubnetGroupName']
        except exception.BotoServerError as err:
            if err.code == "CacheSubnetGroupNotFound":
                return None

        return None

    def get_or_create_cache_subnet_group(self):
        cache_subnet_group = self.get_cache_subnet_group()

        if cache_subnet_group is not None:
            return cache_subnet_group

        cache_subnet_group = self.create_cache_subnet_group()
        return cache_subnet_group

    def create(self):
        securitygroup = securitygroups.get_or_create(
            region=self.region,
            name=self.name,
            process=self.process,
            platform=self.platform,
            env=self.env
        )
        securitygroup_ids = [securitygroup.id]

        notification_topic_arn = [sns_topic for sns_topic in get_sns_topic_arn(region="sa-east-1", platform="cloud") if "infra" in sns_topic][0]

        cache = self.connection.create_cache_cluster(
            cache_cluster_id=self.cache_name,
            num_cache_nodes=self.nodes,
            cache_node_type=self.cache_instance_class,
            engine="memcached",
            engine_version="1.4.14",
            cache_parameter_group_name=self.get_or_create_cache_parameter_group(),
            cache_subnet_group_name=self.get_or_create_cache_subnet_group(),
            security_group_ids=securitygroup_ids,
            preferred_maintenance_window='Tue:05:00-Tue:06:00',
            port=11211,
            notification_topic_arn=notification_topic_arn,
            auto_minor_version_upgrade=True
        )
        return cache

    def get(self):
        try:
            return self.connection.describe_cache_clusters(cache_cluster_id = self.cache_name)['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]['CacheClusterId']
        except exception.BotoServerError as err:
            if err.code == "CacheClusterNotFound":
                return None

        return None

    def destroy(self):
        cache = self.get()

        if cache is not None:
            if self.destroy_confirmation:
                if raw_input('Are you sure to delete %s? [y/N] ' % self.cache_name) != 'y':
                    return 'Aborted'

            self.connection.delete_cache_cluster(cache_cluster_id=self.cache_name)

            return "Cache cluster %s deleted." % self.cache_name
        else:
            return "Cache cluster %s not found." % self.cache_name
