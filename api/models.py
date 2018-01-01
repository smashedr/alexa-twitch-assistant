from __future__ import unicode_literals

from django.db import models


class TokenDatabase(models.Model):
    uuid = models.CharField('uuid', max_length=255, primary_key=True)
    code = models.CharField('code', max_length=255)
    refresh = models.CharField('refresh', max_length=255)
