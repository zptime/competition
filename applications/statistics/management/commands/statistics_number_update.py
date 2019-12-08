#!/usr/bin/python
# coding=utf-8

from django.core.management.base import BaseCommand, CommandError
from applications.statistics.agents import *


class Command(BaseCommand):
    help = "annually auto-update the classes in all schools"

    def handle(self, *args, **options):
        statistics_number_update()

