""" DBに直接アクセスしてCRUD処理系
"""
from django.db import transaction
from django.db.models import Q
from jrfoodadv.models import Record


@transaction.atomic
def delete_record_by_user_id(user_id):
    """ recordの削除
    """
    pass