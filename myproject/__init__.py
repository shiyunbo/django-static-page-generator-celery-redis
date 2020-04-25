# coding:utf-8
from __future__ import absolute_import, unicode_literals

# 引入celery实例对象
from .celery import app as celery_app

__all__ = ('celery_app',)