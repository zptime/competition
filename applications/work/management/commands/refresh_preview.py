#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from applications.work.task import *
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        task_refresh_preview_status()
