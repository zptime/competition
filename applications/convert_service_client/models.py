#!/usr/bin/env python
# coding=utf-8

from django.conf import settings
from django.db import models

if settings.DATA_STORAGE_USE_S3:
    pass
else:
    # 任务状态
    TASK_STATUS_NOT_PROCESS = (0, u"未处理")
    TASK_STATUS_PROCESSING = (1, u"正在处理")
    TASK_STATUS_PROCESSED_SUCCESS = (2, u"处理完成")
    TASK_STATUS_CHOICE = (TASK_STATUS_NOT_PROCESS, TASK_STATUS_PROCESSING, TASK_STATUS_PROCESSED_SUCCESS)

    # 文件传输状态
    TRANSFER_STATUS_INIT = (0, u"传输初始化")
    TRANSFER_STATUS_SUCCESS = (1, u"传输回送成功")
    TRANSFER_STATUS_FAILED = (2, u"传输回送失败")
    TRANSFER_STATUS_CHOICE = (TRANSFER_STATUS_INIT, TRANSFER_STATUS_SUCCESS, TRANSFER_STATUS_FAILED)

    class TmpStorage(models.Model):
        src_url = models.CharField(default="", blank=True, max_length=256, verbose_name=u"源文件内网绝对url")

        des_url = models.CharField(default='', blank=True, max_length=256, verbose_name=u"转换文件url")
        img_url = models.CharField(default="", blank=True, max_length=256, verbose_name=u"缩略图url")

        download_status = models.IntegerField(default=0, choices=TASK_STATUS_CHOICE, verbose_name=u'下载任务状态')
        download_output = models.CharField(default="", blank=True,  max_length=512, verbose_name=u'下载任务处理输出')

        transfer_status = models.IntegerField(default=0, choices=TRANSFER_STATUS_CHOICE, verbose_name=u"传输回送状态")
        transfer_output = models.CharField(default="", blank=True, max_length=512, verbose_name=u"传输回送输出")

        create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
        update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
        del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

        class Meta:
            db_table = "convert_tmp_storage"
            verbose_name = u"转换数据暂存"
            verbose_name_plural = u"转换数据暂存"

        def __unicode__(self):
            return self.src_url
