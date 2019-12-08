# -*- coding=utf-8 -*-

from django.db import models

from applications.activity.models import Activity, Ranks
from applications.user.models import Area, User


class AreaWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=u'地区名称', on_delete=models.PROTECT)
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "area_work_number"
        verbose_name_plural = u"区域作品数量"
        verbose_name = u"区域作品数量"

    def __unicode__(self):
        return str(self.id)


class LevelWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=u'地区名称', on_delete=models.PROTECT)
    rank = models.ForeignKey(Ranks, verbose_name=u'作品等级', default=None, on_delete=models.PROTECT)
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "level_work_number"
        verbose_name_plural = u"城市和等级分类的作品数量"
        verbose_name = u"城市和等级分类的作品数量"

    def __unicode__(self):
        return str(self.id)


class SubjectWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    subject = models.CharField(default="", max_length=100, verbose_name=u'学科')
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "subject_work_number"
        verbose_name_plural = u"学科分类的作品数量"
        verbose_name = u"学科分类的作品数量"

    def __unicode__(self):
        return str(self.id)


class PhaseWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    phase = models.CharField(default="", blank=True, max_length=30, verbose_name=u'学段')
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "phase_work_number"
        verbose_name_plural = u"学段分类的作品数量"
        verbose_name = u"学段分类的作品数量"

    def __unicode__(self):
        return str(self.id)


class ProjectWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    project = models.CharField(default="", blank=True, max_length=30, verbose_name=u'项目')
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "project_work_number"
        verbose_name_plural = u"项目分类的作品数量"
        verbose_name = u"项目分类的作品数量"

    def __unicode__(self):
        return str(self.id)


class UserWorkNumber(models.Model):
    activity = models.ForeignKey(Activity, verbose_name=u'活动', on_delete=models.PROTECT)
    user = models.ForeignKey(User, verbose_name=u'用户', on_delete=models.PROTECT)
    work_number = models.IntegerField(default=0, verbose_name=u'上传作品数量')
    approve_nubmer = models.IntegerField(default=0, verbose_name=u'已审批数量（含我上传和我审批的）')
    noprove_nubmer = models.IntegerField(default=0, verbose_name=u'未审批作品数量')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "user_work_number"
        verbose_name_plural = u"用户作品数量"
        verbose_name = u"用户作品数量"

    def __unicode__(self):
        return str(self.id)
