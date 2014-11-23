# -*- coding: utf-8 -*-

from getpass import getpass

from boto import rds2 as rds
from boto import exception

from paaws import subnets
from paaws import securitygroups


class RDS(object):
    name = ""
    process = "db"
    platform = ""
    env = ""
    region = ""
    zone = None
    db_instance_class = ""
    connection = None
    db_subnet_group = None
    securitygroup_ids = None
    parameter_group = None
    engine_major_version = None
    engine_version = None
    storage_size = 10
    iops = None
    destroy_confirmation = True
    db_instance_name = None
    multi_az = False
    db_name = None
    engine = "MySQL"
    username = "tginfra"
    user_password = None
    preferred_maintenance_window = 'Tue:05:00-Tue:06:00'
    preferred_backup_window = '06:00-06:30'
    backup_retention_period = 30
    port = 3306
    auto_minor_version_upgrade = True
    publicly_accessible = False
    license_model = "general-public-license"
    tags = []

    def __init__(self, name, platform, env, region, db_instance_class=None, engine_major_version="5.6", storage_size=10, iops=None, multi_az=False, destroy_confirmation=True):
        self.name = name
        self.platform = platform
        self.env = env
        self.db_instance_name = "%s-%s-%s" % (self.name, self.platform, self.env)
        self.region = region
        self.db_instance_class = db_instance_class
        self.connection = rds.connect_to_region(self.region)
        self.engine_major_version = engine_major_version
        self.storage_size = storage_size
        self.iops = iops
        self.engine_version = "5.6.13"
        self.multi_az = multi_az
        if self.env == "prod":
            self.multi_az = True
        self.db_name = "tmp"
        self.tags=[
            ( "Name", self.name ),
            ( "Platform", self.platform ),
            ( "Environment", self.env )
        ]


    def create_db_subnet_group(self):
        try:
            db_subnet_group = self.connection.create_db_subnet_group(
                db_subnet_group_name = "subnetgroup.%s" % self.platform,
                db_subnet_group_description = "RDS SubnetGroup of %s" % self.platform,
                subnet_ids = subnets.get(platform=self.platform, region=self.region),
                tags = [ ("Platform", self.platform) ]
            )
            return db_subnet_group['CreateDBSubnetGroupResponse']['CreateDBSubnetGroupResult']['DBSubnetGroup']['DBSubnetGroupName']

        except exception.JSONResponseError as err:
            raise ValueError(err.body['Error']['Message'])


    def get_db_subnet_group(self):
        try:
            return self.connection.describe_db_subnet_groups(db_subnet_group_name="subnetgroup.%s" % self.platform)['DescribeDBSubnetGroupsResponse']['DescribeDBSubnetGroupsResult']['DBSubnetGroups'][0]['DBSubnetGroupName']

        except exception.JSONResponseError as err:
            return None


    def get_or_create_db_subnet_group(self):
        db_subnet_group = self.get_db_subnet_group()

        if db_subnet_group is not None:
            return db_subnet_group

        db_subnet_group = self.create_db_subnet_group()
        return db_subnet_group


    def create_db_parameter_group(self):
        try:
            parameter_group = self.connection.create_db_parameter_group(
                db_parameter_group_name = "%s-%s-%s" % (self.name, self.platform, self.env),
                db_parameter_group_family = "mysql%s" % self.engine_major_version,
                description = "RDS ParameterGroup of database %s running on environment %s and platform %s" % (self.name, self.platform, self.env),
                tags = [
                    ("Name", self.name),
                    ("Platform", self.platform),
                    ("Environment", self.env)
                ]
            )
            return parameter_group['CreateDBParameterGroupResponse']['CreateDBParameterGroupResult']['DBParameterGroup']['DBParameterGroupName']

        except exception.JSONResponseError as err:
            raise ValueError(err.body['Error']['Message'])


    def get_db_parameter_group(self):
        try:
            return self.connection.describe_db_parameter_groups(db_parameter_group_name="%s-%s-%s" % (self.name, self.platform, self.env))['DescribeDBParameterGroupsResponse']['DescribeDBParameterGroupsResult']['DBParameterGroups'][0]['DBParameterGroupName']
        except exception.JSONResponseError as err:
            return None


    def get_or_create_db_parameter_group(self):
        db_parameter_group = self.get_db_parameter_group()

        if db_parameter_group is not None:
            return db_parameter_group

        db_parameter_group = self.create_db_parameter_group()
        return db_parameter_group


    def create(self):
        master_password = getpass("Master Database Password: ")

        subnet_group = self.get_or_create_db_subnet_group()
        parameter_group = self.get_or_create_db_parameter_group()

        securitygroup = securitygroups.get_or_create(
            region=self.region,
            name=self.name,
            process=self.process,
            platform=self.platform,
            env=self.env
        )
        securitygroup_ids = [securitygroup.id]

        database = self.connection.create_db_instance(
            db_instance_identifier = self.db_instance_name,
            db_name = self.db_name,
            allocated_storage = self.storage_size,
            db_instance_class = self.db_instance_class,
            engine = self.engine,
            master_username = self.username,
            master_user_password = master_password,
            vpc_security_group_ids = securitygroup_ids,
            availability_zone = None,
            multi_az = self.multi_az,
            db_subnet_group_name = subnet_group,
            db_parameter_group_name = parameter_group,
            preferred_maintenance_window = self.preferred_maintenance_window,
            preferred_backup_window = self.preferred_backup_window,
            backup_retention_period = self.backup_retention_period,
            port = self.port,
            engine_version = self.engine_version,
            auto_minor_version_upgrade = self.auto_minor_version_upgrade,
            license_model = self.license_model,
            iops = self.iops,
            publicly_accessible = self.publicly_accessible,
            tags=self.tags
        )

        return "Database %s created. User: %s and Password: %s. Keep this information" % (self.db_instance_name, self.username, master_password)

    def get(self):
        try:
            database = self.connection.describe_db_instances(db_instance_identifier = self.db_instance_name)
            return database['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances'][0]['DBInstanceIdentifier']
        except rds.exceptions.DBInstanceNotFound:
            return None

    def destroy(self):
        database = self.get()

        if database is not None:
            if self.destroy_confirmation:
                if raw_input('Are you sure to delete %s? [y/N] ' % database) != 'y':
                    return 'Aborted'

            self.connection.delete_db_instance(
                db_instance_identifier = self.db_instance_name,
                skip_final_snapshot = False,
                final_db_snapshot_identifier = "%s-final-snapshot" % self.db_instance_name
            )
            return "DB Instance %s will be deleted with a safe final snapshot" % self.db_instance_name

        else:
            return "DB Instance %s not found." % self.db_instance_name



    
