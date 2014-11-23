# -*- coding: utf-8 -*-

from boto import ec2, vpc


def create(region, name=None, process=None, platform=None, env=None, raw_mode=False, fullname=None):
    """
    """
    vpc_connection = vpc.connect_to_region(region)
    ec2_connection = ec2.connect_to_region(region)
    main_vpcs = vpc_connection.get_all_vpcs(filters={'tag:Name': 'main'})

    if len(main_vpcs) > 0:
        main_vpc = main_vpcs[0]

    else:
        raise ValueError("Not found any VPC into region %s with tag Name: main" % (region))
    vpc_id = main_vpc.id

    if raw_mode:
        if fullname is not None:
            securitygroup_name = fullname
            securitygroup_desc = securitygroup_name
    else:
        securitygroup_name = "%s-%s-%s-%s-sg" % (process, name, platform, env)
        securitygroup_desc = securitygroup_name

    securitygroup = ec2_connection.create_security_group(securitygroup_name, securitygroup_desc, vpc_id=vpc_id)  
    securitygroup.add_tag("Name", securitygroup_name)

    return securitygroup


def authorize(securitygroup, protocol, port_range, authorization_cidr=None, authorization_sg=None):
    """
    """

    if (authorization_cidr is None and authorization_sg is None) or (authorization_cidr is not None and authorization_sg is not None):
        raise ValueError("You must provide a valid authorization_cidr or authorization_sg")
    securitygroup.authorize(
        ip_protocol=protocol,
        from_port=port_range[0],
        to_port=port_range[1],
        cidr_ip=authorization_cidr,
        src_group=authorization_sg
    )
    return True


def get(region, name=None, process=None, platform=None, env=None, raw_mode=False, fullname=None):
    """
    """
    ec2_connection = ec2.connect_to_region(region)
    if raw_mode:
        if fullname is not None:
            securitygroup = ec2_connection.get_all_security_groups(filters={'tag:Name': fullname})
            if len(securitygroup) > 0:
                return securitygroup[0]
    if all([name, process, platform, env]):
        securitygroup_name = "%s-%s-%s-%s-sg" % (process, name, platform, env)
        securitygroup = ec2_connection.get_all_security_groups(filters={'tag:Name': securitygroup_name})
        if len(securitygroup) > 0:
            return securitygroup[0]

    return None


def get_or_create(region, name=None, process=None, platform=None, env=None, raw_mode=False, fullname=None):
    if raw_mode:
        if fullname is not None:
            securitygroup = get(raw_mode=True, fullname=fullname, region=region)
            if securitygroup is not None:
                return securitygroup

            securitygroup = create(raw_mode=True, fullname=fullname, region=region)
            return securitygroup

    securitygroup = get(name=name, process=process, platform=platform, env=env, region=region)
    if securitygroup is not None:
        return securitygroup

    securitygroup = create(name=name, process=process, platform=platform, env=env, region=region)
    return securitygroup
