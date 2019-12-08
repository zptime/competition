#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from applications.work.task import clean_task_files
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        clean_task_files()