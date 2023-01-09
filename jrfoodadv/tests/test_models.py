"""
test_models.pyの全体テスト
% python manage.py test jrfoodadv.tests.test_models

test_models.pyのユニットテスト
% python manage.py test jrfoodadv.tests.test_models.JrFoodLabelingAdviseQuestionModelTests.test_is_empty
"""
import os
import pandas as pd

from django.test import TestCase
from jrfoodadv.models import JrFoodLabelingAdviseQuestion, TextbookChapter


class JrFoodLabelingAdviseQuestionModelTests(TestCase):
    """JrFoodLabelingAdviseQuestionモデルのテスト
    """
    def test_is_empty(self):
        """初期状態では何も登録されていないことを確認
        """
        saved_jrfoodadv = JrFoodLabelingAdviseQuestion.objects.count()
        self.assertFalse(saved_jrfoodadv)

    def test_jrfoodadv_is_count_one(self):
        """が同じレコードが1つ保存される
        """
        sample_question_title = 'sample question title 20220604'
        jrfoodadv = JrFoodLabelingAdviseQuestion(
            question_id='j111111',
            original_data='original',
            original_data_num='111111',
            textbook_chapter=TextbookChapter.FRESH_FOOD,
            question_title=sample_question_title,
            sub_question_title='',
            question_type='',
            question_img='',
            choice_a='食品の表示は、消費者にとって、その食品を購入する際になくてはならない情報の宝庫である。',
            choice_b='食品の表示は、安全性を伝えるものではなく、消費者に商品の持つ情報を伝えるだけのものである。',
            choice_c='食品の表示は、問題が起こった際に原因究明や製品回収の対策を素早く的確に行うための糸口となる。',
            choice_d='食品の表示は、表示義務事項が法令により決められており、違反した場合は食品関連事業者は罰則や行政処分を受けることになる。',
            correct_answer='choice_b',
            commentary='食品の表示には、商品の安全性を伝える役割と商品の持つ情報を消費者に正確に伝える役割があります。万が一商品に問題が起こった際には原因究明や製品回収を迅速に、且つ的確に行うための情報となります。',
            created_at='2022/02/10 10:30:59',
            updated_at='2022/02/10 10:30:59',
        )
        jrfoodadv.save()
        saved_jrfoodadv = JrFoodLabelingAdviseQuestion.objects.count()
        self.assertEqual(saved_jrfoodadv, 1)
        self.assertEqual(sample_question_title, jrfoodadv.question_title)

    def test_jrfoodadv_record_is_true(self):
        """csvデータが保存される
        """
        # 問題をcsvファイルから作成
        # manage.pyの階層からスタートなのでread_csvはappの先頭
        csv_file = os.environ['csv_file']
        df = pd.read_csv(f'jrfoodadv/csv/{csv_file}')
        df_replace_non = df.where(df.notnull(), '')

        # 辞書にして展開しながら引数を作成
        object_count = 0
        for _, row in df_replace_non.iterrows():
            # _ -> 連番, row -> 行列で整列
            dict_data = row.to_dict()
            # objectをcreate
            JrFoodLabelingAdviseQuestion.objects.create(**dict_data)
            object_count += 1
        # objectが1以上であることを確認
        self.assertTrue(JrFoodLabelingAdviseQuestion.objects.count())
