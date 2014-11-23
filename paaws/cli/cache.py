"""
Usage:
    paaws cache launch --name=<name> --platform=<platform> --env=<env> --region=<region> --cache-instance-class=<cache_instance_class> [ --nodes=<nodes> ]
    paaws cache destroy --name=<name> --platform=<platform> --env=<env> --region=<region>
    paaws cache ls --region=<region>
    paaws cache detail --name=<name> --platform=<platform> --env=<env> --region=<region>

The most commonly used paaws cache commands are:
    launch
    destroy
    ls
    detail
"""
from __future__ import print_function

from paaws.config import Config
from paaws.cache import ElasticCache


def cache(args):
    if args['launch']:
        cache = ElasticCache(
            name=args["--name"],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            cache_instance_class=args["--cache-instance-class"],
            nodes=args["--nodes"] if args["--nodes"] is not None else 1
        )
        print(cache.create())

    elif args['destroy']:
        cache = ElasticCache(
            name=args["--name"],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region']
        )
        print(cache.destroy())
    elif args['ls']:
        print("Not implemented yet")
    elif args['detail']:
        print("Not implemented yet")
