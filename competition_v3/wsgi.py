# -*- coding: utf-8 -*-

import os
import sys
from django.core.wsgi import get_wsgi_application

reload(sys)
sys.setdefaultencoding('utf8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "competition_v3.settings")

application = get_wsgi_application()
