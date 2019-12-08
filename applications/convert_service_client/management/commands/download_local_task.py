# coding=utf-8

from django.core.management.base import BaseCommand
from ...agents import download_task


class Command(BaseCommand):
    """
        从服务器下载转换的临时文件，执行频率要求高
    """
    help = 'this is a command to trigger convert service automatic'

    def handle(self, *args, **options):
        download_task()
