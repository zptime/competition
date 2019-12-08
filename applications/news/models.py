# -*- coding=utf-8 -*-

from django.db import models

from applications.upload_resumable.models import FileObj
from ..user.models import Account
from ..user.models import Area

class NewsType(models.Model):
    area = models.ForeignKey(Area, null=True, blank=True, related_name="news_type_area", on_delete=models.PROTECT,
                             verbose_name=u"相关地区")
    type_name = models.CharField(default="", max_length=32, blank=True, null=True, verbose_name=u"新闻类型名称")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    edit_flag = models.IntegerField(default=1, choices=((1, u"是"), (0, u"否")), verbose_name=u'可否编辑')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = 'news_type'
        verbose_name = u"新闻类型"
        verbose_name_plural = u"新闻类型"

    def __unicode__(self):
        return self.type_name


class News(models.Model):
    news_type = models.ForeignKey(NewsType, null=True, blank=True, related_name="news_type", on_delete=models.PROTECT,
                                  verbose_name=u"新闻类型")
    title = models.CharField(default="", max_length=256, verbose_name=u'标题')
    content = models.TextField(default="", blank=True, verbose_name=u'内容')
    publisher = models.ForeignKey(Account, verbose_name=u'发布人', on_delete=models.PROTECT)
    read = models.IntegerField(default=0, verbose_name=u'阅读次数')
    is_top = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否置顶')
    status = models.IntegerField(default=0, choices=((0, u"草稿"), (1, u"发布")), verbose_name=u"新闻状态")
    public_time = models.DateField(blank=True, null=True, verbose_name=u"发布时间")
    area_id = models.CharField(default="", max_length=256, verbose_name=u'地区编号', null=True, blank=True)
    image = models.ForeignKey(FileObj, verbose_name=u'新闻封面', related_name="news_image", on_delete=models.PROTECT, null=True, blank=True)
    is_home_image_show = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否将图片显示在首页轮播图')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "news"
        verbose_name_plural = u"新闻"
        verbose_name = u"新闻"

    def __unicode__(self):
        return self.title

