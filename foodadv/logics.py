""" DBに直接アクセスしてCRUD処理系
"""
from django.db import transaction
from django.db.models import Q
from foodadv.models import FoodadvRecord


@transaction.atomic
def delete_foodadv_record_by_user_id(user_id):
    """ recordの削除
    """
    pass
