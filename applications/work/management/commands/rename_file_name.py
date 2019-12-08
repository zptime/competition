#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from applications.work.task import *
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # 不再需要改名逻辑了, 已通过下载时，添加http头的方式指定文件名。
        return
        rename_work_rar_file()
