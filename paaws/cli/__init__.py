# -*- coding: utf-8 -*-
"""
PaAWS - PaaS for AWS
Usage:
    paaws <command> [<args>...]

The most commonly used paaws commands are:
    app         create, scale, cmd, ls, ps, deploy, link an app.
    instance    launch, destroy, ls, detail an instance.
    database    launch, destroy, ls, detail a database.
    cache       launch, destroy, ls detail a cache.
    help        show paaws help.
"""

from __future__ import print_function
import sys

from docopt import docopt


args = docopt(__doc__, version='Titans Web Services 1.0.0', options_first=True)

if args['<command>'] == 'app':
    from . import app
    app_args = docopt(app.__doc__)
    app.app(app_args)
elif args['<command>'] == 'instance':
    from . import instance
    instance_args = docopt(instance.__doc__)
    instance.instance(instance_args)
elif args['<command>'] == 'database':
    from . import database
    database_args = docopt(database.__doc__)
    database.database(database_args)
elif args['<command>'] == 'cache':
    from . import cache
    cache_args = docopt(cache.__doc__)
    cache.cache(cache_args)
elif args['<command>'] == 'help':
    print(__doc__)
else:
    print("Choose an action")
sys.exit(0)
