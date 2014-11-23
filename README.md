PaAWS - PaaS for AWS
===================

VERSION: 0.1.0
==============

INSTALATION
===========
```shell
$: mkvirtualenv paaws
$: workon paaws
$: python setup.py develop
```

REQUIREMENTS
============
 - boto>=2.32.0
 - fabric
 - prettypable
 - docopt

USAGE
=====
```shell
$: paaws help
Titans Web Services.
Usage:
    paaws <command> [<args>...]

The most commonly used paaws commands are:
    app         create, scale, cmd, ls, ps, deploy, link an app.
    database    launch, destroy, ls, detail a database.
    cache       launch, destroy, ls detail a cache.
    link	link resources with apps.
    help        show paaws help.
```
