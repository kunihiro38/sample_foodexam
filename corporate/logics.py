""" DBに直接アクセスしてのCRUD処理系
"""
import datetime
import pytz

from django.conf import settings
from django.db import transaction

from corporate.models import Testimonials


# HACK
# かなり乱暴な直し方なので修正必要
def _make_aware_time(exam_date):
    if not isinstance(exam_date, str):
        exam_date = str(exam_date)
    parsed_date = datetime.datetime.strptime(exam_date, '%Y-%m-%d')
    fix_timezone = pytz.timezone(settings.TIME_ZONE)
    exam_date = fix_timezone.localize(parsed_date)
    return exam_date

@transaction.atomic
def create_testimonials(
                    exam_subject,
                    payment_course,
                    payment_plan,
                    pen_name,
                    email,
                    title,
                    exam_date,
                    points,
                    times,
                    learning_time,
                    referenced_site,
                    learning_method,
                    impression,
                    advice,
                    next_exam,
                    improvements,
                    ):
    """ 合格体験記の新規作成
    """
    pass
