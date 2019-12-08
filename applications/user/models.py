#!/usr/bin/env python
# coding=utf-8

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from utils.public_fun import xor_crypt_string
from utils.utils_db import AdvancedModel
from ..upload_resumable.models import FileObj

LEVEL_NONE = 0
LEVEL_NATION =      0b10000
LEVEL_PROVINCE =    0b01000
LEVEL_CITY =        0b00100
LEVEL_COUNTY =      0b00010
LEVEL_INSTITUTION = 0b00001

LEVEL_MASKS = (
    (LEVEL_NONE, u"无权限"),
    (LEVEL_NATION, u"国家"),
    (LEVEL_PROVINCE, u"省"),
    (LEVEL_PROVINCE | LEVEL_NATION, u"省|国家"),
    (LEVEL_CITY, u"市州"),
    (LEVEL_CITY | LEVEL_NATION, u"市州|国家"),
    (LEVEL_CITY | LEVEL_PROVINCE, u"市州|省"),
    (LEVEL_CITY | LEVEL_PROVINCE | LEVEL_NATION, u"市州|省|国家"),
    (LEVEL_COUNTY, u"区县"),
    (LEVEL_COUNTY | LEVEL_NATION, u"区县|国家"),
    (LEVEL_COUNTY | LEVEL_PROVINCE, u"区县|省"),
    (LEVEL_COUNTY | LEVEL_PROVINCE | LEVEL_NATION, u"区县|省|国家"),
    (LEVEL_COUNTY | LEVEL_CITY, u"区县|市州"),
    (LEVEL_COUNTY | LEVEL_CITY | LEVEL_NATION, u"区县|市州|国家"),
    (LEVEL_COUNTY | LEVEL_CITY | LEVEL_PROVINCE, u"区县|市州|省"),
    (LEVEL_COUNTY | LEVEL_CITY | LEVEL_PROVINCE | LEVEL_NATION, u"区县|市州|省|国家"),
    (LEVEL_INSTITUTION, u"机构"),
    (LEVEL_INSTITUTION | LEVEL_NATION, u"机构|国家"),
    (LEVEL_INSTITUTION | LEVEL_PROVINCE, u"机构|省"),
    (LEVEL_INSTITUTION | LEVEL_PROVINCE | LEVEL_NATION, u"机构|省|国家"),
    (LEVEL_INSTITUTION | LEVEL_CITY, u"机构|市州"),
    (LEVEL_INSTITUTION | LEVEL_CITY | LEVEL_NATION, u"机构|市州|国家"),
    (LEVEL_INSTITUTION | LEVEL_CITY | LEVEL_PROVINCE, u"机构|市州|省"),
    (LEVEL_INSTITUTION | LEVEL_CITY | LEVEL_PROVINCE | LEVEL_NATION, u"机构|市州|省|国家"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY, u"机构|区县"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_NATION, u"机构|区县|国家"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_PROVINCE, u"机构|区县|省"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_PROVINCE | LEVEL_NATION, u"机构|区县|省|国家"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_CITY, u"机构|区县|市州"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_CITY | LEVEL_NATION, u"机构|区县|市州|国家"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_CITY | LEVEL_PROVINCE, u"机构|区县|市州|省"),
    (LEVEL_INSTITUTION | LEVEL_COUNTY | LEVEL_CITY | LEVEL_PROVINCE | LEVEL_NATION, u"机构|区县|市州|省|国家"),
)

EDITOR_RIGHT_NONE = 0
EDITOR_RIGHT_ACTIVITY = [0b1000, u'赛事管理']
EDITOR_RIGHT_NEWS = [0b0100, u'新闻管理']
EDITOR_RIGHT_USERS = [0b0010, u'用户管理']
EDITOR_RIGHT_TEMPLATES = [0b0001, u'模板管理']
EDITOR_RIGHT = (
    (EDITOR_RIGHT_NEWS[0], u"运营权限"),
    (EDITOR_RIGHT_ACTIVITY[0] | EDITOR_RIGHT_NEWS[0] | EDITOR_RIGHT_USERS[0] | EDITOR_RIGHT_TEMPLATES[0], u"所有权限"),
)


class Region(models.Model):
    """
        实际的国家行政地理机构划分，
        由于存在如水果湖小学，地理上属于武昌区，但系统中有时候会归属于武昌区，有时候会归属于省直属，
        此处记录实际的国家行政地理机构划分，系统中的归属记录在Area中。
    """
    region_code = models.CharField(default="", max_length=32, blank=True, null=True, verbose_name=u"行政编码")
    region_level = models.IntegerField(default=0, choices=((LEVEL_NONE, u"无权限"), (LEVEL_INSTITUTION, u"机构/学校"),
                                                           (LEVEL_COUNTY, u"区县"), (LEVEL_CITY, u"市州"),
                                                           (LEVEL_PROVINCE, u"省"), (LEVEL_NATION, u"国家")),
                                       verbose_name=u"区域等级")
    region_name = models.CharField(default="", max_length=32, blank=True, null=True, verbose_name=u"行政名称")
    region_fullname = models.CharField(default="", max_length=200, blank=True, null=True, verbose_name=u"行政全称")

    parent = models.ForeignKey('self', related_name="regionchild", null=True, blank=True, verbose_name=u"上级行政地域")

    # 学校用户下面可以挂普通用户，用于区分之前的机构
    is_school = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否学校')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = 'compe_region'
        verbose_name = u"行政区域"
        verbose_name_plural = u"行政区域"

    def __unicode__(self):
        return self.region_code


class AccountManager(BaseUserManager):
    def create_user(self, username, password=None, **kwargs):
        if not username or not password:
            raise ValueError('UserManager create user param error')
        user = self.model(username=username)
        user.encoded_pwd = xor_crypt_string(data=password, encode=True)
        user.set_password(password)
        if kwargs:
            if kwargs.get('mobile', ""):
                user.mobile = kwargs['mobile']
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        account = self.create_user(username, password)
        account.is_superuser = True
        account.is_admin = True
        account.save(using=self._db)
        return account


class Account(AbstractBaseUser):
    objects = AccountManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=40, unique=True, db_index=True, verbose_name=u"账号")
    encoded_pwd = models.CharField(max_length=128, verbose_name=u"加密密码")
    name = models.CharField(default="", max_length=30, db_index=True, blank=True, verbose_name=u'姓名')
    sex = models.CharField(default=u"未设置", max_length=30, choices=((u"未设置", u"未设置"), (u"男", u"男"),
                                                                      (u"女", u"女")), verbose_name=u'性别')

    # 原为是否网站管理员编辑新闻，新的用途为作为后台管理员的权限控制。0为非后台管理员，
    # 新用途为四位数分别表示赛事管理，新闻管理，用户管理，模板管理是否有权限
    auth = models.IntegerField(default=0, choices=EDITOR_RIGHT, verbose_name=u'是否为网站编辑员')
    is_activity_admin = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")),
                                            verbose_name=u'是否可以创建活动')  # 本字段已废弃
    activity_mask = models.IntegerField(default=0, choices=LEVEL_MASKS, verbose_name=u"创建活动的等级掩码")  # 本字段已废弃

    is_admin = models.BooleanField(default=False, verbose_name=u'是否后台管理员')  # 只有root可以登陆后台admin操作数据库
    is_active = models.BooleanField(default=True, verbose_name=u'有效')
    is_data_confirm = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'用户资料是否经用户本人确认')
    is_self_reg = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否自主注册')
    image = models.ForeignKey(FileObj, related_name=u"image_account", null=True, blank=True, verbose_name=u"用户头像",
                              on_delete=models.PROTECT)

    # 预留字段
    mobile = models.CharField(default="", blank=True, max_length=30, verbose_name=u'手机号')
    code = models.CharField(default="", blank=True, max_length=30, verbose_name=u'学籍号')
    email = models.CharField(default="", blank=True, max_length=30, verbose_name=u'邮箱')

    # 地域表示字段
    # area_level = models.IntegerField(default=0, choices=((LEVEL_NONE, u"个人"), (LEVEL_INSTITUTION, u"机构"),
    #                                                      (LEVEL_COUNTY, u"区县"), (LEVEL_CITY, u"市州"),
    #                                                      (LEVEL_PROVINCE, u"省")), verbose_name=u"地域等级")
    # area_name = models.CharField(default='', max_length=32, verbose_name=u"区域")
    region = models.ForeignKey(Region, related_name=u"accountregion", null=True, blank=True, verbose_name=u"用户学校", on_delete=models.PROTECT)

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    class Meta:
        db_table = "compe_account"
        verbose_name = u"个人表"
        verbose_name_plural = u"个人表"

    def __unicode__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Area(models.Model):
    """
        基础的地区等级表示，用以区分机构
    """
    area_code = models.CharField(default="", max_length=32, blank=True, null=True, verbose_name=u"地区编码")
    area_level = models.IntegerField(default=0, choices=((LEVEL_NONE, u"无权限"), (LEVEL_INSTITUTION, u"机构/学校"),
                                                         (LEVEL_COUNTY, u"区县"), (LEVEL_CITY, u"市州"),
                                                         (LEVEL_PROVINCE, u"省"), (LEVEL_NATION, u"国家")),
                                     verbose_name=u"区域等级")
    area_name = models.CharField(default="", max_length=32, blank=True, null=True, verbose_name=u"地区名称")
    area_fullname = models.CharField(default="", max_length=200, blank=True, null=True, verbose_name=u"地区全称")

    manage_direct = models.IntegerField(default=0, choices=((0, u"非直属"), (1, u"直属")), verbose_name=u"直属标识")
    # 解决市直区域问题
    parent = models.ForeignKey('self', related_name="child", null=True, blank=True, verbose_name=u"上级地域")

    region = models.ForeignKey(Region, related_name="arearegion", null=True, blank=True, verbose_name=u"行政区域")
    # 学校用户下面可以挂普通用户，用于区分之前的机构
    # is_school = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否学校')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = 'compe_area'
        verbose_name = u"地区"
        verbose_name_plural = u"地区"

    def __unicode__(self):
        return self.area_code


class User(models.Model):
    account = models.ForeignKey(Account, related_name="user_account", on_delete=models.PROTECT, verbose_name=u"相关用户")
    area = models.ForeignKey(Area, null=True, blank=True, related_name="user_area", on_delete=models.PROTECT,
                             verbose_name=u"相关地区")

    is_admin = models.IntegerField(default=0, choices=((0, u"普通用户"), (1, u"系统后台root用户")),
                                   verbose_name=u"系统root用户标注")
    name = models.CharField(default="", max_length=30, db_index=True, blank=True, verbose_name=u'姓名')
    sex = models.CharField(default=u"未设置", max_length=30, choices=((u"未设置", u"未设置"), (u"男", u"男"),
                                                                      (u"女", u"女")), verbose_name=u'性别')
    is_show_store = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否在用户库显示')
    parent_account = models.ForeignKey(Account, related_name="user_parentaccount", on_delete=models.PROTECT, verbose_name=u"上级用户", null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = 'compe_user'
        verbose_name = u"用户"
        verbose_name_plural = u"用户"

    def __unicode__(self):
        return self.name


class AccountRight(models.Model):
    """
        帐号创建活动权限
    """
    account = models.ForeignKey(Account, related_name="accountrightaccount", verbose_name=u"帐户")
    area = models.ForeignKey(Area, null=True, blank=True, related_name="accountrightarea", on_delete=models.PROTECT,
                             verbose_name=u"可创建活动的地区")
    area_fullname = models.CharField(default="", max_length=30, blank=True, verbose_name=u'完整地区路径')

    create_count = models.IntegerField(default=0, verbose_name=u"活动创建次数")
    admit_account = models.ForeignKey(Account, default=None, related_name="accountrightadmit", blank=False, null=False, verbose_name=u"添加人")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = 'account_right'
        verbose_name = u"帐号活动创建权限"
        verbose_name_plural = u"帐号活动创建权限"

    def __unicode__(self):
        return self.account.mobile


class VerifyCode(models.Model):
    mobile = models.CharField(default="", max_length=30, blank=True, null=True, verbose_name=u"手机号")
    IMCode_status = models.IntegerField(default=0, choices=((0, u"未验证"), (1, u"已验证")), verbose_name=u"图片验证码状态")
    code = models.CharField(default='', max_length=30, blank=True, null=True, verbose_name=u"短信验证码")
    timestamp = models.CharField(default="", max_length=30, blank=True, null=True, verbose_name=u"短信验证码生成时间戳")
    code_status = models.IntegerField(default=0, choices=((0, u"未验证"), (1, u"已验证")), verbose_name=u"短信验证码验证状态")

    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

    class Meta:
        db_table = "verifycode"
        verbose_name = u'验证码'
        verbose_name_plural = u"验证码"

    def __unicode__(self):
        return self.__class__.__name__


