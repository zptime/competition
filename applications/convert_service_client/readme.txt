# coding=utf-8

模块： convert_service_client
名称： 转码服务客户端
功能： 提供资源的格式转换，包含图片格式，视频格式（不含swf）转MP4，文档格式转pdf,音频转MP3

说明：
        @conf.py : 配置文件，包含以下配置参数

            # 配置当前需要转码服务的应用url,当应用不在用户中心时或者本机测试时可以使用,本地回送地址
            CONVERT_SERVICE_CLIENT_APP_URL_CONF = "http://127.0.0.1"

            # 配置转码服务的url,远端服务器地址
            CONVERT_SERVICE_SERVER_URL_CONF = "http://10.1.3.58"

            # 配置导入的转码资源模块路径形如“teacher_source.apps.resource.models”
            CONVERT_SERVICE_CLIENT_RESOURCE_PATH = "teacher_source.apps.resource.models"
            # 配置导入的转码资源表名称 形如“Resource”
            CONVERT_SERVICE_CLIENT_RESOURCE_NAME = "Resource"


            # convert_service api :
            # 转码服务的服务端接口以及名称
            API_CONVERT_SERVICE_INIT_SERVICE = "/api/init/service"
            SERVICE_CONVERT_SERVICE = "convert_service"

            资源文件的表项按照一下格式定义，转码需要的固定字段如下：
            class Resource(models.Model):
                src_file = models.ForeignKey(FileObj, verbose_name=u'原始文件', related_name="src_file", on_delete=models.PROTECT)
                des_file = models.ForeignKey(FileObj,  null=True, blank=True, verbose_name=u'转换后文件', related_name="des_file", on_delete=models.PROTECT)
                img_file = models.ForeignKey(FileObj, null=True, blank=True,  verbose_name=u'转换后文件', related_name="img_file", on_delete=models.PROTECT)

                task_status = models.IntegerField(default=0, choices=TASK_STATUS_CHOICE, verbose_name=u'任务状态')
                task_time = models.DateTimeField(null=True, blank=True, verbose_name=u'任务开始处理时间')
                task_output = models.CharField(default="", blank=True,  max_length=512, verbose_name=u'任务处理输出')

                create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
                update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
                del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')

                class Meta:
                    db_table = "resource"
                    verbose_name_plural = u"资源文件"
                    verbose_name = u"资源文件"

                def __unicode__(self):
                    return self.name

        @ agent.py:
            其中包含的公共模块：
                from ..data.models import FileObj
                from ...utils.err_code import *
                from ...utils.constant import *
                from ...utils.public_fun import send_http_request, str_p_datetime
                from ..data.utils import *

        @ django异步命令 task_auto_convert_trigger.py
            需添加系统定时任务见 deploy/cron/

        @ setting/production.py
            INSTALLED_APPS 添加该模块
            配置 SELF_APP

        @ url.py
            将该模块下的url include 进去
            import apps.convert_service_client.urls
            urlpatterns += [

                    url(r"^convert_service/", include(apps.convert_service_client.urls))
                ]
