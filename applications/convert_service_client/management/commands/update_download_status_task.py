# coding=utf-8

from django.core.management.base import BaseCommand
from ...agents import update_status_remote_task


class Command(BaseCommand):
    """
        向服务器推送临时文件的下载状态,非实时命令，执行频率可为1天
    """
    help = 'this is a command to trigger convert service automatic'

    def handle(self, *args, **options):
        update_status_remote_task()
