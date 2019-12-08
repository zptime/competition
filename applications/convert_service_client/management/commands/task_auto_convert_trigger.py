# coding=utf-8

from django.core.management.base import BaseCommand
from ...agents import convert_send_data


class Command(BaseCommand):
    help = 'this is a command to trigger convert service automatic'

    def handle(self, *args, **options):
        convert_send_data()
