#!/usr/bin/env python
# coding=utf-8

from django.core.management.base import BaseCommand
from applications.work.video_convert_task import VideoConverterTask


class Command(BaseCommand):
    help = "this ia a command to convert video from other format to mp4 (except flv or svf)"

    def handle(self, *args, **options):
        VideoConverterTask.execute_loop()
