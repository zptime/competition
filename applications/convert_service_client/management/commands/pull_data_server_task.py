# coding=utf-8

from django.core.management.base import BaseCommand
from ...agents import pull_data_from_server


class Command(BaseCommand):
    """
        从服务器拉取转码数据，执行频率要求高
    """
    help = 'this is a command to trigger convert service automatic'

    def handle(self, *args, **options):
        pull_data_from_server()
