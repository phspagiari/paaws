# -*- coding: utf-8 -*-
from __future__ import print_function

import ConfigParser
import os


class Config(object):
    config_file = None
    region = None
    platform = None
    env = None
    account_id = "464526076120"
    ami = {'sa-east-1': 'ami-a4fb5eb9', 'us-east-1': 'ami-e7582d8e'}
    key = {'sa-east-1': '464526076120', 'us-east-1': '464526076120-us'}

    @classmethod
    def get_default_config(self, space, key):
        if 'TWS_SETTINGS' not in os.environ:
            print("The environment variable 'TWS_SETTINGS' must be set")
        else:
            self.config_file = os.environ['TWS_SETTINGS']
            config = ConfigParser.RawConfigParser()
            config.read(self.config_file)

            try:
                return config.get(space, key)
            except ConfigParser.NoOptionError:
                return None
