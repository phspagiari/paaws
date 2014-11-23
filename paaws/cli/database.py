"""
Usage:
    paaws database launch --name=<name> --platform=<platform> --env=<env> --region=<region> --db-instance-class=<db_instance_class> --engine-major-version=<engine_major_version> --storage-size=<storage_size> [ --iops=<iops> ] [ --multi-az ]
    paaws database destroy --name=<name> --platform=<platform> --env=<env> --region=<region>
    paaws database ls --region=<region>
    paaws database detail --name=<name> --platform=<platform> --env=<env> --region=<region>

The most commonly used paaws database commands are:
    launch
    destroy
    ls
    detail
"""
from __future__ import print_function

from paaws.config import Config
from paaws.database import RDS


def database(args):
    if args['launch']:
        database = RDS(
            name=args["--name"],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region'],
            db_instance_class=args["--db-instance-class"],
            engine_major_version=args["--engine-major-version"] if args["--engine-major-version"] is not None else "5.6",
            storage_size=args["--storage-size"],
            iops=args["--iops"],
            multi_az=args["--multi-az"]
        )
        print(database.create())
    elif args['destroy']:
        database = RDS(
            name=args["--name"],
            platform=Config.get_default_config(space='paaws', key='platform') if args['--platform'] is None else args['--platform'],
            env=Config.get_default_config(space='paaws', key='env') if args['--env'] is None else args['--env'],
            region=Config.get_default_config(space='paaws', key='region') if args['--region'] is None else args['--region']
        )
        print(database.destroy())
    elif args['ls']:
        print("Not implemented yet")
    elif args['detail']:
        print("Not implemented yet")
