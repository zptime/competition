#!/usr/bin/env python
# coding=utf-8

from django.core.management.base import BaseCommand

from applications.activity.models import Rule
from applications.work.models import *
from utils.file_fun import *
from django.conf import settings
import httplib


class Command(BaseCommand):
    def handle(self, *args, **options):
        content = '''
            {"code": "1", "judge_count": "3", "max": "100"}
        '''
        for each in Activity.objects.filter():
            if not Rule.objects.filter(activity=each).exists():
                Rule.objects.create(activity=each, code=REVIEW_RULE_1, content=content)
                logger.info('generate rule for activity %s' % each.id)

