#!/usr/bin/env python
# coding=utf-8

from django.core.management.base import BaseCommand
from applications.work.models import *
from utils.file_fun import *
from django.conf import settings
import httplib


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--activity_id', nargs='+', type=int)

    def handle(self, *args, **options):
        activity_id = options['activity_id'][0]
        activity_id = int(activity_id)
        work_list = Work.objects.filter(activity_id=activity_id, del_flag=FLAG_NO).values("no", "rar_file__url")
        count = 0
        for work_info in work_list:
            no = work_info["no"]
            url = work_info["rar_file__url"]
            if not url:
                continue
            else:
                url = get_image_url(url)
            conn = httplib.HTTPConnection(host=settings.AWS_S3_HOST, port=settings.AWS_S3_PORT)
            conn.request("GET", url, headers={'Range': 'bytes=0-0'})
            resp = conn.getresponse()
            count += 1
            if resp.status >= 300:
                msg = "error download [%s] url=%s code=%d" % (no, url, resp.status)
                print msg
        print count
