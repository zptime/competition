#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from applications.work.unzip_task import UnzipTask
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        UnzipTask.execute_loop()
