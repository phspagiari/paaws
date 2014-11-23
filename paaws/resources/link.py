# -*- coding: utf-8 -*-
from paaws.vpc import securitygroups

def link_app_resources(resource_connection, name, platform, env, region):
    try:
        source, target, port = resource_connection.split(":")
    except IndexError:
        return "You must provide a valid resource connection like web:db:3306"

    source_sg = securitygroups.get(
        region=region,
        name=name,
        process=source,
        platform=platform,
        env=env
    )
    if source_sg is None:
        return "Unable to find security group of specified resource %s" % source

    target_sg = securitygroups.get(
        region=region,
        name=name,
        process=target,
        platform=platform,
        env=env
    )
    if target_sg is None:
        return "Unable to find security group of specified resource %s" % target

    authorization = securitygroups.authorize(
        securitygroup=source_sg,
        protocol="tcp",
        port_range=(port, port),
        authorization_sg=target_sg
    )

    return authorization
