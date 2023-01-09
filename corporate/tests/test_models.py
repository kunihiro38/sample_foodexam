"""
test_models.pyの全体テスト
% python manage.py test corporate.tests.test_models

test_models.pyのユニットテスト
% python manage.py test corporate.tests.test_models.InformationTests.test_is_empty
"""


from django.test import TestCase
from corporate.models import Information, Category, Release


class InformationModelTests(TestCase):
    """informationモデルのテスト
    """
    def test_is_empty(self):
        """初期状態では何も登録されていないことを確認
        """
        saved_information = Information.objects.count()
        self.assertFalse(saved_information)

    def test_info_is_count_one(self):
        """titleが同じレコードが1つ保存される
        """
        information_title = 'sample title 20220604'
        information = Information(
            category=Category.NEWS,
            title=information_title,
            description='sample description 20220604',
            contributor=0, # admin
            release=Release.PUBLIC
        )
        information.save()
        saved_information = Information.objects.count()
        self.assertEqual(saved_information, 1)
        self.assertEqual(information_title, information.title)
