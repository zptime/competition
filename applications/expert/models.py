# -*- coding=utf-8 -*-
from django.db import models
from ..user.models import Account, Area


class Expert(models.Model):
    account = models.ForeignKey(Account, related_name='expert_account', on_delete=models.PROTECT, verbose_name=u"用户")
    area = models.ForeignKey(Area, related_name='expert_area', on_delete=models.PROTECT, verbose_name=u"相关地区")

    name = models.CharField(default="", max_length=30, db_index=True, blank=True, verbose_name=u'姓名')
    sex = models.CharField(u'性别', default=u"未设置", max_length=30, choices=((u"未设置", u"未设置"), (u"男", u"男"), (u"女", u"女")))
    institution = models.CharField(default="", blank=True, null=True, max_length=256, verbose_name=u'机构')
    position = models.CharField(default="", blank=True, null=True,  max_length=256, verbose_name=u'职位')
    introduction = models.CharField(default="", blank=True, null=True, max_length=256, verbose_name=u'简介')
    is_show_homepage = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否显示在首页')
    is_show_store = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否在专家库显示')
    # img_file = models.ForeignKey(FileObj, null=True, blank=True, verbose_name=u'专家图片', on_delete=models.PROTECT)

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "expert"
        verbose_name_plural = u"专家"
        verbose_name = u"专家"

    def __unicode__(self):
        return str(self.id)
