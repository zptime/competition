#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from applications.work.change_doc_format_task import change_doc_format_service
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        change_doc_format_service()
