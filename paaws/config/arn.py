# -*- coding: utf-8 -*-
from paaws.config import attributes

def arn_constructor(service, name, account_id=attributes.account_id, resourcetype=None, region=None):

    if service in [ "ec2", "glacier", "elasticbeanstalk", "storagegateway"]:
        #arn:aws:ec2:region:account:instance/instance-id
        arn = "arn:aws:{service}:{region}:{account_id}:{resourcetype}/{name}".format(service=service, region=region, account_id=account_id, resourcetype=resourcetype, name=name)

    elif service in ["rds", "redshift"]:
        #arn:aws:service:region:account:db:databasename
        arn = "arn:aws:{service}:{region}:{account_id}:{resourcetype}:{name}".format(service=service, region=region, account_id=account_id, resourcetype=resourcetype, name=name)

    elif service in ["s3", "route53"]:
        #arn:aws:route53:::hostedzone/zoneid
        arn = "arn:aws:{service}:::{resourcetype}/{name}".format(service=service, resourcetype=resourcetype, name=name)

    elif service in ["autoscaling"]:
        #arn:aws:autoscaling:region:account:autoScalingGroup:groupid:autoScalingGroupName/groupfriendlyname
        arn = "arn:aws:{service}:{region}:{account_id}:autoScalingGroup:{resourcetype}:autoScalingGroupName/{name}".format(service=service, region=region, account_id=account_id, resourcetype=resourcetype, name=name)

    elif service in ["iam"]:
        #arn:aws:iam::account:user/username
        arn = "arn:aws:{service}::{account_id}:{resourcetype}/{name}".format(service=service, account_id=account_id, resourcetype=resourcetype, name=name)

    elif service in ["sqs", "sns"]:
        #arn:aws:sqs:region:account:queuename
        arn = "arn:aws:{service}:{region}:{account_id}:{name}".format(service=service, region=region, account_id=account_id, name=name)

    else:
        raise ValueError("You must provide a valid service like ec2, rds, s3, route53. Not %s" % service)

    return arn
