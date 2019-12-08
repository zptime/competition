# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('user', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', max_length=256, verbose_name='\u6807\u9898')),
                ('content', models.TextField(default=b'', verbose_name='\u5185\u5bb9', blank=True)),
                ('type', models.CharField(max_length=256, verbose_name='\u65b0\u95fb\u7c7b\u578b')),
                ('is_top', models.IntegerField(default=0, verbose_name='\u662f\u5426\u7f6e\u9876', choices=[(1, '\u662f'), (0, '\u5426')])),
                ('status', models.IntegerField(default=0, verbose_name='\u65b0\u95fb\u72b6\u6001', choices=[(0, '\u8349\u7a3f'), (1, '\u53d1\u5e03')])),
                ('public_time', models.DateField(null=True, verbose_name='\u53d1\u5e03\u65f6\u95f4', blank=True)),
                ('area_id', models.CharField(default=b'', max_length=256, verbose_name='\u5730\u533a\u7f16\u53f7')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('del_flag', models.IntegerField(default=0, verbose_name='\u662f\u5426\u5220\u9664', choices=[(1, '\u662f'), (0, '\u5426')])),
            ],
            options={
                'db_table': 'news',
                'verbose_name': '\u65b0\u95fb',
                'verbose_name_plural': '\u65b0\u95fb',
            },
        ),
        migrations.CreateModel(
            name='NewsType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type_name', models.CharField(default=b'', max_length=32, null=True, verbose_name='\u65b0\u95fb\u7c7b\u578b\u540d\u79f0', blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('del_flag', models.IntegerField(default=0, verbose_name='\u662f\u5426\u5220\u9664', choices=[(1, '\u662f'), (0, '\u5426')])),
                ('area', models.ForeignKey(related_name='news_type_area', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u76f8\u5173\u5730\u533a', blank=True, to='user.Area', null=True)),
            ],
            options={
                'db_table': 'news_type',
                'verbose_name': '\u65b0\u95fb\u7c7b\u578b',
                'verbose_name_plural': '\u65b0\u95fb\u7c7b\u578b',
            },
        ),
        migrations.AddField(
            model_name='news',
            name='news_type',
            field=models.ForeignKey(related_name='news_type', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u65b0\u95fb\u7c7b\u578b', blank=True, to='news.NewsType', null=True),
        ),
        migrations.AddField(
            model_name='news',
            name='publisher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u53d1\u5e03\u4eba', to=settings.AUTH_USER_MODEL),
        ),
    ]
