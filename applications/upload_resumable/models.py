# -*- coding=utf-8 -*-
from django.db import models


class FilePart(models.Model):
    name = models.CharField(default="", max_length=250, verbose_name=u'文件名称')
    part_num = models.IntegerField(default=0, verbose_name=u'文件块编号')
    status = models.IntegerField(default=1, choices=((1, u"正在进行"), (2, u"已完成")), verbose_name=u'任务状态')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = "file_part"
        unique_together = ("name", "part_num")
        verbose_name_plural = u"文件块"
        verbose_name = u"文件块"

    def __unicode__(self):
        return self.name


class FileObj(models.Model):
    name = models.CharField(default="", max_length=250, verbose_name=u'名称')
    url = models.CharField(default="", max_length=250, verbose_name=u'相对地址')
    size = models.IntegerField(default=0, verbose_name=u'大小')
    type = models.CharField(default="", max_length=30, verbose_name=u'文件类型')
    ext = models.CharField(default="", max_length=30, verbose_name=u'文件扩展名')
    modify_time = models.DateTimeField(null=True, blank=True, verbose_name=u'文件修改时间')
    status = models.IntegerField(default=1, choices=((1, u"已完成"), (0, u"未完成")), verbose_name=u'是否上传完成')
    uploader_id = models.IntegerField(default=0, verbose_name=u'上传者ID')
    activity_id = models.IntegerField(default=0, verbose_name=u'活动ID')
    md5sum = models.CharField(default="", max_length=255, verbose_name=u'文件md5sum')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "file_obj"
        verbose_name_plural = u"文件"
        verbose_name = u"文件"

    def __unicode__(self):
        return self.name
