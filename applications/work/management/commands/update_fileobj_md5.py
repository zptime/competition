#!/usr/bin/python
# -*- coding=utf-8 -*-
import os
from django.core.management.base import BaseCommand, CommandError
import logging
from django.conf import settings

from applications.upload_resumable.models import FileObj
from utils.const_def import MD5_COMPUTE_STATUS_COMPUTING
from utils.utils_os import is_proc_over_load

if settings.DATA_STORAGE_USE_S3:
    from applications.upload_resumable.files_s3 import get_file_md5
    file_dir = ''
else:
    from applications.upload_resumable.files import get_file_md5
    file_dir = os.path.join(settings.BASE_DIR, settings.FILE_STORAGE_DIR_NAME)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not is_proc_over_load(proc_name_list=["manage.py", __name__.split('.')[-1]]):
            update_fileobj_md5()


def update_fileobj_md5():
    """
    更新无md5字段文件的md5
    :return:
    """
    # 获取待处理的数据
    fileobjs_nomd5 = FileObj.objects.filter(md5sum="")[:100]

    for each_fileobj in fileobjs_nomd5:
        # 由于处理时间可能会很长，所以这里还是要判断一下。以免数据此时已经发生变化。
        if not each_fileobj.md5sum:
            each_fileobj.md5sum = MD5_COMPUTE_STATUS_COMPUTING
            each_fileobj.save()
        else:
            continue

        file_path = os.path.join(file_dir, each_fileobj.url)
        md5 = get_file_md5(file_path)
        each_fileobj.md5sum = md5
        each_fileobj.save()

