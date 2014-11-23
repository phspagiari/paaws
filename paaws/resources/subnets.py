# -*- coding: utf-8 -*-
from boto import vpc


def get(platform, region, zone=None):
    connection = vpc.connect_to_region(region)

    if zone is not None:
        subnet = [subnet.id for subnet in connection.get_all_subnets(filters={'tag:Platform': platform, 'tag:Zone': zone})]
        if len(subnet) > 0:
            return subnet[0]

    subnets = [subnet.id for subnet in connection.get_all_subnets(filters={'tag:Platform': platform})]
    if len(subnets) > 0:
        return subnets

    return None
