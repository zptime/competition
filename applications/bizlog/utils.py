# -*- coding: utf-8 -*-

import logging
import time
import datetime
import re

logger = logging.getLogger(__name__)


def today():
    return datetime.datetime.strptime(
            time.strftime('%Y-%m-%d', time.localtime(time.time())),
            '%Y-%m-%d')


def tomorrow():
    return datetime.datetime.strptime(
            time.strftime('%Y-%m-%d', time.localtime(time.time() + 24 * 60 * 60)),
            '%Y-%m-%d')


def yesterday():
    return datetime.datetime.strptime(
        time.strftime('%Y-%m-%d', time.localtime(time.time() - 24 * 60 * 60)),
        '%Y-%m-%d')


def yesterday_str():
    return time.strftime('%Y-%m-%d', time.localtime(time.time() - 24 * 60 * 60))


def datetime2str(datetime_para, format='%Y-%m-%d %H:%M:%S'):
    return datetime_para.strftime(format) if datetime_para else ''


def is_qualify(path, include, exclude):
    qualify = False
    if '*' in include:
        qualify = True
    else:
        for each in include:
            if re.match(each, path):
                qualify = True
    if qualify:
        if '*' in exclude:
            qualify = False
        else:
            for each in exclude:
                if re.match(each, path):
                    qualify = False
    return qualify
