"""
Usage:
    paaws app create [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] --instance-class=<instance_class> --desired-capacity=<desired_capacity> --region=<region> [ --min=<minimum> ] [ --max=<maximum> ] [ --elb [ --domain=<domain> ] --public ] [ --public-instances ]
    paaws app scale [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] --desired-capacity=<desired_capacity> --region=<region>
    paaws app update [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] [ --instance-class=<instance_class> ] [ --ami-id=<ami_id> ] --region=<region>
    paaws app cmd <command> [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] [ --sudo ] --region=<region>
    paaws app ls --region=<region>
    paaws app ps [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] [ --region=<region> ] [ --more ]
    paaws app deploy [ --scale-name=<scale_name> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] --region=<region> [ --revision=<revision> ]
    paaws app link --resource-connection=<resource_connection>  --name=<app_name> --platform=<platform> --env=<env> --region=<region>
Formats:
    --resource-connection: TARGET:ORIGIN:PORT
        Examples:
            From API to DB  on port 3006 => db:api:3306
            From ELB to API on port 80   => api:elb-api:80
"""

from __future__ import print_function
import sys

from fabric.colors import red

from paaws.config import Config
from paaws.autoscale import Scale, describe_group, describe_group_instances, list_all_groups
from paaws.loadbalancer import ElasticLoadBalancer
from paaws.management import deploy, cmd
from paaws.link.resource import link_app_resources
from paaws.ec2 import get_instances_data
from paaws.helpers.parsers import to_table


def app(args):
    if args['create']:
        name = args['--name']
        process = args['--process']
        platform = Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform']
        env = Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env']
        instance_class = Config.get_default_config(space='autoscale', key='instance-class') if args['--instance-class'] is None else args['--instance-class']
        desired_capacity = Config.get_default_config(space='autoscale', key='desired-capacity') if args['--desired-capacity'] is None else args['--desired-capacity']
        region = Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region']

        if args['--scale-name'] is not None:
            asg = Scale(
                old_method=True,
                scale_name=args['--scale-name'],
                instance_class=instance_class,
                desired_capacity=desired_capacity,
                region=region,
                minimum=0 if args['--min'] is None else args['--min'],
                maximum=2 if args['--min'] is None else args['--max'],
                elb=args['--elb'],
            )
            print(asg.create())
        else:
            if args['--elb']:
                loadbalancer = ElasticLoadBalancer(
                    name=name,
                    process=process,
                    platform=platform,
                    env=env,
                    region=region,
                    domain=args['--domain'] if args['--domain'] is not None else None,
                    public=args['--public']
                )
                loadbalancer = loadbalancer.get_or_create()
                loadbalancer_name = loadbalancer.name
            else:
                loadbalancer_name = None

            asg = Scale(
                name=name,
                process=process,
                platform=platform,
                env=env,
                region=region,
                instance_class=instance_class,
                desired_capacity=desired_capacity,
                minimum=0 if args['--min'] is None else args['--min'],
                maximum=4 if args['--min'] is None else args['--max'],
                elb=loadbalancer_name,
                public=args['--public-instances']
            )
            autoscaling_group = asg.create()
            autoscaling_data = {
                "Name": [name],
                "Process": [process],
                "Platform": [platform],
                "Region": [region],
                "Endpoint": [loadbalancer.dns_name] if args['--elb'] else [" -- "],
                "Instance Class": [instance_class],
                "Desired Capacity": [desired_capacity]
            }
            print(to_table(autoscaling_data))

    elif args['scale']:
        if args['--scale-name'] is not None:
            asg = Scale(
                old_method=True,
                autoscale_update=True,
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                scale_name=args['--scale-name'],
                desired_capacity=args['--desired-capacity'],
            )
            print(asg.update())
        else:
            asg = Scale(
                name=args['--name'],
                process=args['--process'],
                platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
                env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                autoscale_update=True,
                desired_capacity=args['--desired-capacity'],
            )
            print(asg.update())

    elif args['update']:
        if args['--scale-name'] is not None:

            kwargs = {
                'old_method': True,
                'launchconfig_update': True,
                'scale_name': args['--scale-name'],
                'region': Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                'instance_class': args['--instance-class'],
                'ami_id': args['--ami-id'],
            }
            kwargs = {key: value for (key, value) in kwargs.iteritems() if value is not None}

            asg = Scale(**kwargs)
            print(asg.update())
        else:
            kwargs = {
                'name': args['--name'],
                'process': args['--process'],
                'platform': Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
                'env': Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
                'region': Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                'launchconfig_update': True,
                'instance_class': args['--instance-class'],
                'ami_id': args['--ami-id'],
            }
            kwargs = {key: value for (key, value) in kwargs.iteritems() if value is not None}

            asg = Scale(**kwargs)
            print(asg.update())

    elif args['deploy']:
        if args['--scale-name'] is not None:
            asg = Scale(
                old_method=True,
                scale_name=args['--scale-name'],
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            )

            autoscaling_group = asg.get_scale()

            deploy(
                autoscaling_group=autoscaling_group,
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                revision=args['--revision']
            )

        else:
            instance_ips = []
            if args['--process'] is None:
                if raw_input(red("You are running without specifying a process (including LB), are you sure? [y/N] ")) != 'y':
                    sys.exit(0)
                else:
                    instance_data = get_instances_data(
                        region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                        instance_ids=[],
                        list_instances=True,
                        name=args['--name'],
                        platform=args['--platform'],
                        env=args['--env']
                    )
                    for ip in instance_data['IP']:
                        instance_ips.append(ip)
            else:
                processes = args['--process'].split(", ")
                for process in processes:
                    instance_data = get_instances_data(
                        region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                        instance_ids=[],
                        list_instances=True,
                        name=args['--name'],
                        process=process,
                        platform=args['--platform'],
                        env=args['--env']
                    )
                    for ip in instance_data['IP']:
                        instance_ips.append(ip)

            deploy(
                instances_ips=instance_ips,
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                revision=args['--revision']
            )

    elif args['cmd']:
        if args['--scale-name'] is not None:
            asg = Scale(
                old_method=True,
                scale_name=args['--scale-name'],
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            )

            autoscaling_group = asg.get_scale()
            cmd(
                    autoscaling_group=autoscaling_group,
                    region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                    is_sudo=args['--sudo'], command=args['<command>']
            )
        else:
            instance_ips = []
            if args['--process'] is None:
                if raw_input(red("You are running without specifying a process (including LB), are you sure? [y/N] ")) != 'y':
                    sys.exit(0)
                else:
                    instance_data = get_instances_data(
                        region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                        instance_ids=[],
                        list_instances=True,
                        name=args['--name'],
                        platform=args['--platform'],
                        env=args['--env']
                    )
                    for ip in instance_data['IP']:
                        instance_ips.append(ip)
            else:
                processes = args['--process'].split(", ")
                for process in processes:
                    instance_data = get_instances_data(
                        region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                        instance_ids=[],
                        list_instances=True,
                        name=args['--name'],
                        process=process,
                        platform=args['--platform'],
                        env=args['--env']
                    )
                    for ip in instance_data['IP']:
                        instance_ips.append(ip)

            cmd(
                instances_ips=instance_ips,
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                is_sudo=args['--sudo'], command=args['<command>']
            )

    elif args['ps']:
        if args['--scale-name'] is not None:
            print(to_table(describe_group(name=args['--scale-name'], old_method=True)))

            if args['--more']:
                instances = describe_group_instances(name=args['--scale-name'])
                instance_data = get_instances_data(
                    region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                    instance_ids=instances,
                    list_instances=True,
                )
                print(to_table(instance_data))
        else:
            asg = Scale(
                name=args['--name'],
                process=args['--process'],
                platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
                env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
                region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            )

            autoscaling_group = asg.get_scale()
            print(to_table(describe_group(name=autoscaling_group.name)))

            if args['--more']:
                instance_data = get_instances_data(
                    region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
                    instance_ids=[],
                    list_instances=True,
                    name=args['--name'],
                    process=args['--process'],
                    platform=args['--platform'],
                    env=args['--env']
                )
                print(to_table(instance_data))

    elif args['ls']:
        print(to_table(list_all_groups(region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'])))

    elif args['link']:
        link = link_app_resources(
            resource_connection=args['--resource-connection'],
            name=args['--name'],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region']
        )
        print(link)

    else:
        pass
