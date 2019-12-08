# coding=utf-8

from django.core.management.base import BaseCommand, CommandError

from ...report import daily_report

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Command(BaseCommand):
    def handle(self, *args, **options):
        daily_report()
