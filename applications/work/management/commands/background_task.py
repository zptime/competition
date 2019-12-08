#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import logging

from django.db import transaction

from applications.common.models import TaskTrace, TASK_STATUS_WAIT, TASK_STATUS_DOING, TASK_STATUS_FAIL, TASK_STATUS_SUCC, TASK_EXPORT_WORK_BY_CREATOR
from applications.work.agents import export_work_super_all_task
from utils.const_def import TRUE_INT
from utils.utils_except import TaskException

logger = logging.getLogger('django_command')


def dispatch_task(task):
    try:
        if task.name == TASK_EXPORT_WORK_BY_CREATOR:
            return export_work_super_all_task(task)
        else:
            return None
    except Exception as e:
        logger.exception(e)
        raise e


class Command(BaseCommand):
    def handle(self, *args, **options):
        task = TaskTrace.objects.filter(status=TASK_STATUS_WAIT).first()
        try:
            task.status = TASK_STATUS_DOING
            task.save()
            dispatch_task(task)
        except TaskException as te:
            task.status = TASK_STATUS_FAIL
            task.del_flag = TRUE_INT
            task.result = te.msg
            task.save()
        except Exception:
            task.status = TASK_STATUS_FAIL
            task.del_flag = TRUE_INT
            task.save()
        else:
            task.status = TASK_STATUS_SUCC
            task.save()





