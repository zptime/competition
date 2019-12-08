#!/usr/bin/env python
# coding=utf-8

from django.core.management.base import BaseCommand

from applications.activity.guess import GuessArea


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--string')

    def handle(self, *args, **options):
        string = options['string']
        result, area, insi = GuessArea().guess(string)
        print result
        print area.area_name if area else ''
        print insi



