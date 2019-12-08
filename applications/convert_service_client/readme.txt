# coding=utf-8

ģ�飺 convert_service_client
���ƣ� ת�����ͻ���
���ܣ� �ṩ��Դ�ĸ�ʽת��������ͼƬ��ʽ����Ƶ��ʽ������swf��תMP4���ĵ���ʽתpdf,��ƵתMP3

˵����
        @conf.py : �����ļ��������������ò���

            # ���õ�ǰ��Ҫת������Ӧ��url,��Ӧ�ò����û�����ʱ���߱�������ʱ����ʹ��,���ػ��͵�ַ
            CONVERT_SERVICE_CLIENT_APP_URL_CONF = "http://127.0.0.1"

            # ����ת������url,Զ�˷�������ַ
            CONVERT_SERVICE_SERVER_URL_CONF = "http://10.1.3.58"

            # ���õ����ת����Դģ��·�����硰teacher_source.apps.resource.models��
            CONVERT_SERVICE_CLIENT_RESOURCE_PATH = "teacher_source.apps.resource.models"
            # ���õ����ת����Դ������ ���硰Resource��
            CONVERT_SERVICE_CLIENT_RESOURCE_NAME = "Resource"


            # convert_service api :
            # ת�����ķ���˽ӿ��Լ�����
            API_CONVERT_SERVICE_INIT_SERVICE = "/api/init/service"
            SERVICE_CONVERT_SERVICE = "convert_service"

            ��Դ�ļ��ı����һ�¸�ʽ���壬ת����Ҫ�Ĺ̶��ֶ����£�
            class Resource(models.Model):
                src_file = models.ForeignKey(FileObj, verbose_name=u'ԭʼ�ļ�', related_name="src_file", on_delete=models.PROTECT)
                des_file = models.ForeignKey(FileObj,  null=True, blank=True, verbose_name=u'ת�����ļ�', related_name="des_file", on_delete=models.PROTECT)
                img_file = models.ForeignKey(FileObj, null=True, blank=True,  verbose_name=u'ת�����ļ�', related_name="img_file", on_delete=models.PROTECT)

                task_status = models.IntegerField(default=0, choices=TASK_STATUS_CHOICE, verbose_name=u'����״̬')
                task_time = models.DateTimeField(null=True, blank=True, verbose_name=u'����ʼ����ʱ��')
                task_output = models.CharField(default="", blank=True,  max_length=512, verbose_name=u'���������')

                create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'����ʱ��')
                update_time = models.DateTimeField(auto_now=True, verbose_name=u'�޸�ʱ��')
                del_flag = models.IntegerField(default=0, choices=((1, u"��"), (0, u"��")), verbose_name=u'�Ƿ�ɾ��')

                class Meta:
                    db_table = "resource"
                    verbose_name_plural = u"��Դ�ļ�"
                    verbose_name = u"��Դ�ļ�"

                def __unicode__(self):
                    return self.name

        @ agent.py:
            ���а����Ĺ���ģ�飺
                from ..data.models import FileObj
                from ...utils.err_code import *
                from ...utils.constant import *
                from ...utils.public_fun import send_http_request, str_p_datetime
                from ..data.utils import *

        @ django�첽���� task_auto_convert_trigger.py
            �����ϵͳ��ʱ����� deploy/cron/

        @ setting/production.py
            INSTALLED_APPS ��Ӹ�ģ��
            ���� SELF_APP

        @ url.py
            ����ģ���µ�url include ��ȥ
            import apps.convert_service_client.urls
            urlpatterns += [

                    url(r"^convert_service/", include(apps.convert_service_client.urls))
                ]
