#!/usr/bin/env python
# -*- coding: utf8 -*-

import os

CURR_DIR = os.path.abspath('./')

ENV = os.environ.get('env', 'TEST')

BASECONF = {
    'QUEUE_PARAMS': {
        'host': os.environ.get('QUEUE_HOST', '127.0.0.1'),
         'port': os.environ.get('QUEUE_PORT', 11300),
        'parse_yaml': False},

    "FROM_MAIL_SERVIVE": {
        "user": "",
        "passwd": "",
        "serverName": "smtp.126.com",
        },
}
