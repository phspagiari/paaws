"""
Usage:
    paaws instance detail [ --instance-id=<instance_id> ] [ --name=<app_name> --process=<process> --platform=<platform> --env=<env> ] --region=<region>
    paaws instance list [ --instance-ids=<instance_ids> ] [ --name=<app_name> ] [ --process=<process> ] [ --platform=<platform> ] [ --env=<env> ] --region=<region>
    paaws instance launch --name=<app_name> --process=<process> --platform=<platform> --env=<env> --instance-class=<instance_class> --region=<region> [ --zone=<zone> ] [ --public ]
    paaws instance destroy --name=<app_name> [ --process=<process> --platform=<platform> --env=<env> ] --region=<region>

The most commonly used paaws instance commands are:
    launch
    destroy
    list
    detail
"""
from __future__ import print_function

from paaws.config import Config
from paaws.ec2 import Instance, get_instances_data
from paaws.helpers.parsers import to_table


def instance(args):
    if args['launch']:
        instance = Instance(
            name=args['--name'],
            process=args['--process'],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            instance_class=args['--instance-class'],
            public=args['--public'],
            zone=args['--zone']
        )

        instance = instance.launch()
        instance_id = instance.id

        instance_data = get_instances_data(
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            instance_ids=[ instance_id ],
            list_instances=False,
            name=args['--name'],
            process=args['--process'],
            platform=args['--platform'],
            env=args['--env']
        )
        print(to_table(instance_data))

    elif args['destroy']:
        instance = Instance(
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            name=args['--name'],
            process=args['--process'],
            platform=args['--platform'],
            env=args['--env'],
        )
        print(instance.destroy())

    elif args['detail']:
        instance_data = get_instances_data(
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            instance_ids=[ args['--instance-id'] ] if args['--instance-id'] is not None else [],
            list_instances=False,
            name=args['--name'],
            process=args['--process'],
            platform=args['--platform'],
            env=args['--env']
        )
        print(to_table(instance_data))

    elif args['list']:
        instance_data = get_instances_data(
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            instance_ids=args['--instance-ids'].split(" ") if args['--instance-ids'] is not None else [],
            list_instances=True,
            name=args['--name'],
            process=args['--process'],
            platform=args['--platform'],
            env=args['--env']
        )
        print(to_table(instance_data))
    else:
        pass
