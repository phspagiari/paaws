# -*- coding: utf-8 -*-
from boto import iam
from boto.exception import BotoServerError


def get(name, platform, env):
    connection = iam.connect_to_region('universal')
    iam_role_name = "iam-%s-%s-%s" % (name, platform, env)

    try:
        instance_profile = connection.get_instance_profile(iam_role_name)
    except BotoServerError:
         instance_profile = connection.get_instance_profile('default-iam-role')

    return instance_profile['get_instance_profile_response']['get_instance_profile_result']['instance_profile']['instance_profile_name']


def getrole(short, group, platform, environment):
    iamconn = iam.connect_to_region('universal')

    if all([short, group, platform, environment]):
        try:
            instance_profile = iamconn.get_instance_profile(short+group+"-"+platform+"-"+environment+"-role")
            return instance_profile['get_instance_profile_response']['get_instance_profile_result']['instance_profile']['instance_profile_name']
        except BotoServerError:
            instance_profile = iamconn.get_instance_profile('default-iam-role')
            return instance_profile['get_instance_profile_response']['get_instance_profile_result']['instance_profile']['instance_profile_name']

    return None
