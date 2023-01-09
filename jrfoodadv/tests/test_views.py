"""
食品表示検定・初級テスト
全体テスト
python manage.py test jrfoodadv.tests
クラス単位のテスト 例
python manage.py test jrfoodadv.tests.test_views.TestRegularTests

---比較対象---
例えば、assertEqualなどで左右で比較をする場合。
左：調査対象の式。変化する値。
右：比較対象の式。あまり変化しない。
"""
import datetime
import math
import os
import random
import re
import pandas as pd

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils.timezone import make_aware

from corporate.models import UserCourse, PaymentCourse

from jrfoodadv.forms import SelectAnswerForm, SearchQuestionForm
from jrfoodadv.models import JrFoodLabelingAdviseQuestion, Record, TimeLeft, AnswerResult


User = get_user_model()


class TestRegularTests(TestCase):
    """ 全編通しのレギュラーテスト
    """
    def setUp(self):
        # 同じテストクラス内で共通で使用するデータはここで作成する

        # 問題をcsvファイルから作成
        # manage.pyの階層からスタートなのでread_csvはappの先頭
        csv_file = os.environ['csv_file']
        df = pd.read_csv(f'jrfoodadv/csv/{csv_file}')
        df_replace_non = df.where(df.notnull(), '')

        # 辞書にして展開しながら引数を作成
        jrfoodadv_objects = []
        for _, row in df_replace_non.iterrows():
            # _ -> 連番, row -> 行列で整列
            dict_data = row.to_dict()
            jrfoodadv_objects.append(JrFoodLabelingAdviseQuestion(**dict_data))
        JrFoodLabelingAdviseQuestion.objects.bulk_create(jrfoodadv_objects) # 一括作成

        # 一般のclient
        self.client = Client()

        # userのAlexを作成
        user_data = {
            'username': 'Alex',
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        User.objects.create_user(**user_data)
        # user_corseを作成
        latest_user = User.objects.order_by('-date_joined')
        user_id = latest_user[0].id
        user_course_data = {
            'user_id': user_id,
            'payment_course': PaymentCourse.JRFOODADV,
            'paid_at': make_aware(datetime.datetime.now()),
            'expired_at': make_aware(datetime.datetime.now() + datetime.timedelta(days=1)),
        }
        UserCourse.objects.create(**user_course_data)

        # 無料プランのLoganを作成
        user_data = {
            'username': 'Logan',
            'email': 'logan-is-here@testaddress.coom',
            'password': 'Logan20220703!',
        }
        User.objects.create_user(**user_data)
        # user_corseを作成
        latest_user = User.objects.order_by('-date_joined')
        user_id = latest_user[0].id
        user_course_data = {
            'user_id': user_id,
            'payment_course': PaymentCourse.FREE,
        }
        UserCourse.objects.create(**user_course_data)

        # 有料プランのJamesを作成
        user_data = {
            'username': 'James',
            'email': 'james-is-here@testaddress.coom',
            'password': 'James20220703!',
        }
        User.objects.create_user(**user_data)
        # user_corseを作成
        latest_user = User.objects.order_by('-date_joined')
        user_id = latest_user[0].id
        user_course_data = {
            'user_id': user_id,
            'payment_course': PaymentCourse.JRFOODADV,
            'paid_at': make_aware(datetime.datetime.now()),
            'expired_at': make_aware(datetime.datetime.now() + datetime.timedelta(days=1)),
        }
        UserCourse.objects.create(**user_course_data)

        # 有料プランだけど有効期限が切れたLucasを作成
        user_data = {
            'username': 'Lucas',
            'email': 'lucas-is-here@testaddress.coom',
            'password': 'Lucas20220703!',
        }
        User.objects.create_user(**user_data)
        # user_corseを作成
        latest_user = User.objects.order_by('-date_joined')
        user_id = latest_user[0].id
        user_course_data = {
            'user_id': user_id,
            'payment_course': PaymentCourse.JRFOODADV,
            'paid_at': make_aware(datetime.datetime.now()) - datetime.timedelta(days=1),
            'expired_at': make_aware(datetime.datetime.now() - datetime.timedelta(minutes=1)),
        }
        UserCourse.objects.create(**user_course_data)


    def test_no_login_redirect(self):
        """非ログイン状態でアクセスするとリダイレクトされる
        """
        res = self.client.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/setting/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/setting/del_record/success')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/profile/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/count_question_ajax/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/search/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/record/memos/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/record/favorites/')
        self.assertEqual(res.status_code, 302)
        res = self.client.get(path='/jrfoodadv/favorite_ajax/') # ajax
        self.assertEqual(res.status_code, 302)


    def test_no_login_permission_denied(self):
        """非ログイン状態でアクセスするとPermissionDeniedされる
        """
        res = self.client.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 403)
        res = self.client.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 403)


    def test_no_login_not_found(self):
        """非ログイン状態でアクセスすると Not found される
        """
        res = self.client.get(path='/jrfoodadv/setting/later_ajax/')
        self.assertEqual(res.status_code, 404)


    def test_login_valid_url(self):
        """ログイン済みのユーザーでアクセスすると200
        """
        login_user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)

        res = client_for_alex.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        res = client_for_alex.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 200)


    def test_login_invalid_url(self):
        """ログイン済みのユーザーでアクセスすると対応する処理がされる
        ここのURLは、ajaxや解答終了前のurlで練習問題or模擬試験がスタートしない限りアクセスできない
        """
        login_user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        res = client_for_alex.get(path='/jrfoodadv/memo_ajax/')
        self.assertEqual(res.status_code, 405) # @require_http_methods(['POST'])なので405
        res = client_for_alex.get(path='/jrfoodadv/favorite_ajax/')
        self.assertEqual(res.status_code, 405) # @require_http_methods(['POST'])なので405
        res = client_for_alex.get(path='/jrfoodadv/practice_test_finish_confirm/')
        self.assertEqual(res.status_code, 404)
        res = client_for_alex.get(path='/jrfoodadv/practice_test/answer_status')
        self.assertEqual(res.status_code, 404)
        # # 無理矢理ajaxにアクセスすると403される
        res = client_for_alex.get(path='/jrfoodadv/count_question_ajax/')
        self.assertEqual(res.status_code, 403)
        res = client_for_alex.get(path='/jrfoodadv/make_review_flg_ajax/')
        self.assertEqual(res.status_code, 403)
        res = client_for_alex.get(path='/jrfoodadv/forced_termination_ajax/')
        self.assertEqual(res.status_code, 403)


    def test_free_plan_user(self):
        """無料プランユーザーの一式テスト
        """
        login_user_data = {
            'email': 'logan-is-here@testaddress.coom',
            'password': 'Logan20220703!',
        }
        client_for_logan = Client()
        res = client_for_logan.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)
        res = client_for_logan.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False"', res.content.decode())
        self.assertIn('data-one_question_a_day="False"', res.content.decode())
        self.assertIn('あなたは無料プランです。無料プランは1日1問です。', res.content.decode())
        res = client_for_logan.get(path='/jrfoodadv/select_test/')
        self.assertEqual(res.status_code, 200)
        # data-planがFalseでかつdisabledがある
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        # 検索：data-planがFalseでかつdisabledがある
        res = client_for_logan.get(path='/jrfoodadv/search/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        #学習履歴削除：data-planがFalseでかつdisabledがある
        res = client_for_logan.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())


    def test_paid_plan_user(self):
        """有料プランユーザーの一式テスト
        """
        login_user_data = {
            'email': 'james-is-here@testaddress.coom',
            'password': 'James20220703!',
        }
        client_for_james = Client()
        res = client_for_james.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)
        res = client_for_james.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="True"', res.content.decode())
        self.assertNotIn('data-one_question_a_day="False"', res.content.decode())
        self.assertNotIn('あなたは無料プランです。無料プランは1日1問です。', res.content.decode())
        res = client_for_james.get(path='/jrfoodadv/select_test/')
        self.assertEqual(res.status_code, 200)
        # data-planがTrueである
        self.assertIn('data-plan="True"', res.content.decode())
        self.assertNotIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        # 検索：data-planがTrueである
        res = client_for_james.get(path='/jrfoodadv/search/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="True"', res.content.decode())
        self.assertNotIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        #学習履歴削除：data-planがTrueである
        res = client_for_james.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="True"', res.content.decode())
        self.assertNotIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())


    def test_paid_but_expired_plan_user(self):
        """有料プランだけど有効期限が切れたユーザーの一式テスト
        """
        login_user_data = {
            'email': 'lucas-is-here@testaddress.coom',
            'password': 'Lucas20220703!',
        }
        client_for_lucas = Client()
        res = client_for_lucas.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)
        res = client_for_lucas.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False"', res.content.decode())
        self.assertIn('data-one_question_a_day="False"', res.content.decode())
        self.assertIn('あなたは無料プランです。無料プランは1日1問です。', res.content.decode())
        res = client_for_lucas.get(path='/jrfoodadv/select_test/')
        self.assertEqual(res.status_code, 200)
        # data-planがFalseでかつdisabledがある
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        # 検索：data-planがFalseでかつdisabledがある
        res = client_for_lucas.get(path='/jrfoodadv/search/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())

        #学習履歴削除：data-planがFalseでかつdisabledがある
        res = client_for_lucas.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-plan="False" disabled', res.content.decode())
        self.assertIn('あなたは無料プランです。有料プランで利用ができます。', res.content.decode())


    def test_practice_is_true(self):
        """練習モードの単発テスト"""
        login_user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)
        res = client_for_alex.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        res = client_for_alex.get(path='/jrfoodadv/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Alex', res.content.decode())
        self.assertIn(login_user_data['email'], res.content.decode())

        # 自前でレコードを作成する
        question_qs = JrFoodLabelingAdviseQuestion.objects.all()
        question_qs_ids = [question.question_id for question in question_qs]

        user_alex = User.objects.get(email=login_user_data['email'])
        # first_answer,current_answerは全て全問正解にする
        record_objects = []
        for question_id in question_qs_ids:
            data = {
                'question_id': question_id,
                'user_id': user_alex.id,
                'current_answer': AnswerResult.CORRECT,
                'first_answer': AnswerResult.CORRECT,
            }
            record_objects.append(Record(**data))
        Record.objects.bulk_create(record_objects)

        res = client_for_alex.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('登録されている履歴はありません。', res.content.decode())

        # 正解率
        self.assertIn('100 %', res.content.decode())
        # 20データより大きいと次のページがあることを確認
        self.assertIn('?page=2', res.content.decode())

        # 問題IDにアクセスできる
        latest_record_qs = Record.objects.filter(user_id=user_alex.id).latest('saved_at')
        latest_question_id = latest_record_qs.question_id
        self.assertIn(latest_question_id, res.content.decode())

        res = client_for_alex.get(path=f'/jrfoodadv/record/question_id/{latest_question_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(latest_question_id, res.content.decode())

        # リストページに戻る
        res = client_for_alex.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 200)

        # 2ページ目も問題なく表示されていることを確認
        res = client_for_alex.get(path='/jrfoodadv/record/list/?page=2')
        self.assertEqual(res.status_code, 200)

        # メモページ
        res = client_for_alex.get(path='/jrfoodadv/record/memos/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('登録されているメモはありません。', res.content.decode())

        # 全てのレコードにメモを追加
        record_qs = Record.objects.filter(user_id=user_alex.id)
        for record in record_qs:
            record.memo = 'TRUE!!'
        Record.objects.bulk_update(record_qs, fields=['memo'])

        res = client_for_alex.get(path='/jrfoodadv/record/memos/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('登録されているメモはありません。', res.content.decode())
        # メモ(ペン)のfontawesomeがあることを確認
        self.assertIn('fa-pencil', res.content.decode())
        # 20データより大きいと次のページがあることを確認
        self.assertIn('?page=2', res.content.decode())
        # 2ページ目も問題なく表示されていることを確認
        res = client_for_alex.get(path='/jrfoodadv/record/memos/?page=2')
        self.assertEqual(res.status_code, 200)

        # お気に入りページ
        res = client_for_alex.get(path='/jrfoodadv/record/favorites/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('登録されているお気に入りはありません。', res.content.decode())

        # 全てのレコードにお気に入りを追加
        record_qs = Record.objects.filter(user_id=user_alex.id)
        for record in record_qs:
            record.favorite = True
        Record.objects.bulk_update(record_qs, fields=['favorite'])

        res = client_for_alex.get(path='/jrfoodadv/record/favorites/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('登録されているお気に入りはありません。', res.content.decode())
        # お気に入り(星)のfontawesomeがあることを確認
        self.assertIn('fa-star', res.content.decode())
        # 20データより大きいと次のページがあることを確認
        self.assertIn('?page=2', res.content.decode())
        # 2ページ目も問題なく表示されていることを確認
        res = client_for_alex.get(path='/jrfoodadv/record/favorites/?page=2')
        self.assertEqual(res.status_code, 200)

        # 学習履歴の削除
        res = client_for_alex.get(path='/jrfoodadv/setting/')
        self.assertEqual(res.status_code, 200)
        res = client_for_alex.get(path='/jrfoodadv/setting/del_record/')
        self.assertEqual(res.status_code, 200)
        username = user_alex.username
        self.assertIn(username, res.content.decode())
        # 1回目わざと間違える
        different_username = {'username': 'aaaaaa',}
        res = client_for_alex.post(
            path='/jrfoodadv/setting/del_record/',
            data=different_username,)
        error_msg = '無効な値が入力されています。'
        self.assertIn(error_msg, res.content.decode())
        self.assertEqual(res.status_code, 200)
        # 2回目わざと間違える
        different_username = {'username': 'a'*100,}
        res = client_for_alex.post(
            path='/jrfoodadv/setting/del_record/',
            data=different_username,)
        len_username = len(different_username['username'])
        error_msg = f'この値は 16 文字以下でなければなりません( {len_username} 文字になっています)。'
        self.assertIn(error_msg, res.content.decode())
        self.assertEqual(res.status_code, 200)
        # 正しい名前をpostする
        res = client_for_alex.post(
            path='/jrfoodadv/setting/del_record/',
            data={'username': username,},)
        self.assertEqual(res.status_code, 302)

        # 削除後画面遷移する
        res = client_for_alex.get(path='/jrfoodadv/setting/del_record/success')
        self.assertEqual(res.status_code, 200)
        self.assertIn('学習履歴を削除しました。', res.content.decode())

        # 履歴を見ても残っていない
        res = client_for_alex.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('登録されている履歴はありません。', res.content.decode())

        # 問題検索ページにアクセスできる
        res = client_for_alex.get(path='/jrfoodadv/search/')
        self.assertEqual(res.status_code, 200)

        # 問題IDにquestion_type='label'の画像を含むidを取得して検索にかける
        target_ids_include_img = JrFoodLabelingAdviseQuestion.objects.filter(question_type='label')
        target_id_include_type_label = target_ids_include_img[0].question_id
        search_id = {'question_id': target_id_include_type_label}
        form = SearchQuestionForm(search_id)
        self.assertTrue(form.is_valid())

        # imgタグに、data-question_type="label"とclass="resize_img_for_label"
        # が含まれていることを確認する
        res = client_for_alex.get(
            path=f'/jrfoodadv/search/question_id/{target_id_include_type_label}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-question_type="label"', res.content.decode())
        self.assertIn('class="resize_img_for_label"', res.content.decode())

        # 問題IDにquestion_type='ig'の画像を含むidを取得して検索にかける
        target_ids_include_img = JrFoodLabelingAdviseQuestion.objects.filter(question_type='img')
        target_id_include_type_img = target_ids_include_img[0].question_id
        search_id = {'question_id': target_id_include_type_img}
        form = SearchQuestionForm(search_id)
        self.assertTrue(form.is_valid())

        # imgタグに、data-question_type="img"とclass="resize_img_for_mark"
        # が含まれていることを確認する
        res = client_for_alex.get(
            path=f'/jrfoodadv/search/question_id/{target_id_include_type_img}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-question_type="img"', res.content.decode())
        self.assertIn('class="resize_img_for_mark"', res.content.decode())

        # 問題IDにquestion_type='surround'の画像を含むidを取得して検索にかける
        target_ids_include_img = JrFoodLabelingAdviseQuestion.objects.filter(question_type='surround')
        target_id_include_type_surround = target_ids_include_img[0].question_id
        search_id = {'question_id': target_id_include_type_surround}
        form = SearchQuestionForm(search_id)
        self.assertTrue(form.is_valid())

        # imgタグに、data-question_type="label"とclass="choice_label"
        # が含まれていることを確認する
        res = client_for_alex.get(
            path=f'/jrfoodadv/search/question_id/{target_id_include_type_surround}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('data-question_type="surround"', res.content.decode())
        self.assertIn('class="choice_label"', res.content.decode())


    def test_answer_only_one_regular_true(self):
        """1問だけ解答のレギュラーテスト
        1. 練習モードの出題範囲(1問だけ)を選択し、練習モードに進める
        2. 練習モード1ページ目を未解答で進める
        3. 確認ページで未解答であることを確認
        4. もどるで設問ページへ
        5. 正答を解答する
        6. 確認ページで解答済みであることを確認
        7. 確認ページで答え合わせをする
        8. 演習結果
        9. トップページへ進む
        """
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        res = client_for_alex.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'練習モード', res.content.decode())
        self.assertIn('練習モード', get_decoded_text[0])

        # 問題のオブジェクトがあることを確認

        ### 1. 練習モードの出題範囲(1問だけ)を選択し、練習モードに進める
        choiced_data = {
            'target': ['0','1'], # 未出題且つミスを選択
            'chapter': ['1', '2'], # 1章且つ2章
            'answers': 1, # 1問だけ
        }
        res = client_for_alex.get(
            path='/jrfoodadv/',
            data=choiced_data,
        )
        self.assertEqual(res.status_code, 302)

        ### 2. 練習モード1ページ目を未解答で進める
        # ?page=1
        url = res.url
        res = client_for_alex.get(path=url)
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'問題ID', res.content.decode())
        self.assertIn('問題ID', get_decoded_text[0])

        # ページから問題ID取得
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        page_question_id = get_decoded_question_id[0]

        # 未解答でPOSTする
        res = client_for_alex.post(path=url,)
        self.assertEqual(res.status_code, 302)

        ### 3. 確認ページで未解答であることを確認
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'確認', res.content.decode())
        self.assertIn('確認', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答の問題があります。答え合わせしますか？',
                                        res.content.decode())
        self.assertIn('未解答の問題があります。答え合わせしますか？',
                        get_decoded_text[0])
        # 未解答のページNOがある
        self.assertIn('data-page-num="1"', res.content.decode())
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        finish_confirm_question_id = get_decoded_question_id[0]
        # practiceとpractice_finish_confirmのquestion_idを確認
        self.assertEqual(page_question_id, finish_confirm_question_id)

        ### 4. もどるで設問ページへ
        res = client_for_alex.get(url)
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'問題ID', res.content.decode())
        self.assertIn('問題ID', get_decoded_text[0])
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        get_decoded_question_id = get_decoded_question_id[0]
        self.assertEqual(finish_confirm_question_id, get_decoded_question_id)

        ### 5. 正答を解答する
        # 正答をgetする
        question = JrFoodLabelingAdviseQuestion.objects.get(question_id=get_decoded_question_id)
        correct_answer = question.correct_answer
        # 正答をPOSTする
        choiced_answer = {
            'csrfmiddlewaretoken': True,
            'select_answer': correct_answer,
        }
        form = SelectAnswerForm(get_decoded_question_id, choiced_answer)
        self.assertTrue(form.is_valid())

        res = client_for_alex.post(
            path=url,
            data=choiced_answer,
        )
        self.assertEqual(res.status_code, 302)

        ### 6. 確認ページで解答済みであることを確認
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'確認', res.content.decode())
        self.assertIn('確認', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答の問題があります。答え合わせしますか？',
                                        res.content.decode())
        self.assertFalse(get_decoded_text)

        ### 7. 確認ページで答え合わせをする
        res = client_for_alex.post(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 302)

        ### 8. 演習結果
        res = client_for_alex.get(path='/jrfoodadv/practice/result')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'演習結果', res.content.decode())
        self.assertIn('演習結果', get_decoded_text[0])
        get_decoded_text = re.findall(r'100 %', res.content.decode())
        self.assertIn('100 %', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答とミスに再挑戦', res.content.decode())
        self.assertFalse(get_decoded_text)

        ### 9. トップページへ進む
        res = client_for_alex.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)


    def test_answer_three_regular(self):
        """3問解答のレギュラーテスト
        1. 練習モードの出題範囲('未出題')、出題分野(1章、2章、3章)を選択し、練習モードに進める
        2. 1ページ目は未解答で進める
        3. 2ページ目は正答をする
        4. 3ページ目は未解答で進める
        5. 確認ページから、前のページにもどる
        6. 3ページ目であること
            1. 「もどる」と「すすむ」ボタンがある
        7. 再び確認ページへすすむ
        8. 未解答の問題を見直すを選択
        9. 未解答ページで、正答をPOSTする
        10. 9.のポスト後3ページ目で正答する
        11. 確認ページで全て解答済みであることを確認
        12. 演習結果
        """
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        res = client_for_alex.get(path='/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'練習モード', res.content.decode())
        self.assertIn('練習モード', get_decoded_text[0])


        ### 1. 練習モードの出題範囲('未出題')、出題分野(1章、2章、3章)を選択し、練習モードに進める
        choiced_data = {
            'target': ['0'], # 未出題且つミスを選択
            'chapter': ['1', '2', '3'], # 1章、2章、3章
            'answers': 3, # 3問
        }
        res = client_for_alex.get(
            path='/jrfoodadv/',
            data=choiced_data,
        )
        self.assertEqual(res.status_code, 302)

        def _get_question_id(res):
            """ページから問題ID取得"""
            get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                        res.content.decode())
            page_question_id = get_decoded_question_id[0]
            return page_question_id

        def _get_correct_answer(page_question_id):
            """問題IDを渡して正答を返す"""
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            correct_answer = question.correct_answer
            return correct_answer

        def _get_incorrect_answer(page_question_id):
            """問題IDを渡して誤答を返す"""
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            correct_answer = question.correct_answer
            choices_list = ['choice_a', 'choice_b', 'choice_c', 'choice_d']
            for choice in choices_list:
                if correct_answer != choice:
                    return choice
                else:
                    pass

        ### 2. 1ページ目は未解答で進める
        page1_url = res.url
        res = client_for_alex.get(path=page1_url)
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'問題ID', res.content.decode())
        self.assertIn('問題ID', get_decoded_text[0])

        # 問題IDから正答を取得
        page1_question_id = _get_question_id(res)

        # 未解答(空)でpost
        res = client_for_alex.post(path=page1_url,)
        self.assertEqual(res.status_code, 302)

        ### 3. 2ページ目は正答をする
        page2_url = res.url
        res = client_for_alex.get(path=page2_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('?page=2', page2_url)
        get_decoded_text = re.findall(r'問題ID', res.content.decode())
        self.assertIn('問題ID', get_decoded_text[0])

        # 問題IDから正答を取得
        page2_question_id = _get_question_id(res)
        page2_correct_answer = _get_correct_answer(page2_question_id)

        # 正答をPOSTする
        choiced_answer = {
            'csrfmiddlewaretoken': True,
            'select_answer': page2_correct_answer,
        }
        form = SelectAnswerForm(page2_question_id, choiced_answer)
        self.assertTrue(form.is_valid())

        res = client_for_alex.post(
            path=page2_url,
            data=choiced_answer,
        )
        self.assertEqual(res.status_code, 302)

        ### 4. 3ページ目は未解答で進める
        page3_url = res.url
        res = client_for_alex.get(path=page3_url)
        page3_question_id = _get_question_id(res)
        self.assertEqual(res.status_code, 200)
        self.assertIn('?page=3', page3_url)
        res = client_for_alex.post(path=page3_url,)
        self.assertEqual(res.status_code, 302)

        ### 5. 確認ページから、前のページにもどる
        # page1 -> 未解答
        # page2 -> 正答
        # page3 -> 未解答
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'確認', res.content.decode())
        self.assertIn('確認', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答の問題があります。答え合わせしますか？',
                                        res.content.decode())
        self.assertIn('未解答の問題があります。答え合わせしますか？', get_decoded_text[0])
        get_decoded_text = re.findall(page1_question_id, res.content.decode())
        self.assertIn(page1_question_id, get_decoded_text[0])
        # ページに表示されている問題IDが、未解答のpage1とpage3の問題IDである
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        # 1問目の3問目は未解答なのでdata-page-numがある
        self.assertIn('data-page-num="1"' ,res.content.decode())
        self.assertNotIn('data-page-num="2"' ,res.content.decode())
        self.assertIn('data-page-num="3"' ,res.content.decode())
        self.assertEqual(page1_question_id, get_decoded_question_id[0])
        self.assertEqual(page3_question_id, get_decoded_question_id[1])

        # もどるボタン(formのget)でpage3にもどる
        res = client_for_alex.get(
            path=f'/jrfoodadv/back_to_last_page/{page3_question_id}?back_button=',
        )
        self.assertEqual(res.status_code, 302)
        url = res.url
        self.assertEqual(url, page3_url)

        ### 6. 3ページ目であること
        res = client_for_alex.get(path=page3_url)
        self.assertEqual(res.status_code, 200)
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        self.assertIn(page3_question_id, get_decoded_question_id[0])

        # 1. 「もどる」と「すすむ」ボタンがある
        get_decoded_text = re.findall(r'もどる', res.content.decode())
        self.assertIn('もどる', get_decoded_text[0])
        get_decoded_text = re.findall(r'すすむ', res.content.decode())
        self.assertIn('すすむ', get_decoded_text[0])

        ### 7. 再び確認ページへすすむ
        res = client_for_alex.post(path=page3_url,)
        self.assertEqual(res.status_code, 302)

        ### 8. 未解答の問題を見直すを選択
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'未回答の問題を見直す', res.content.decode())
        self.assertIn('未回答の問題を見直す', get_decoded_text[0])
        get_decoded_text = re.findall(page1_url, res.content.decode())

        res = client_for_alex.get(path=page1_url)
        self.assertEqual(res.status_code, 200)
        # TODO: aタグが2つ、同じURLだがどちらかをクリックするかで発動条件が違う。

        ### 9. 未解答ページで、正答をPOSTする
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        self.assertIn(page1_question_id, get_decoded_question_id[0])
        get_decoded_text = re.findall(r'すすむ', res.content.decode())
        self.assertIn('すすむ', get_decoded_text[0])

        # 問題IDから正答を取得
        page1_correct_answer = _get_correct_answer(page1_question_id)
        # 正答をPOSTする
        choiced_answer = {
            'csrfmiddlewaretoken': True,
            'select_answer': page1_correct_answer,
        }
        form = SelectAnswerForm(page1_question_id, choiced_answer)
        self.assertTrue(form.is_valid()
        )
        res = client_for_alex.post(
            path=page1_url,
            data=choiced_answer,
        )
        self.assertEqual(res.status_code, 302)

        ### 10. 9.のポスト後3ページ目で正答する
        res = client_for_alex.get(path=page3_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('?page=3', page3_url)

        # 問題IDから正答を取得
        page3_question_id = _get_question_id(res)
        page3_correct_answer = _get_correct_answer(page3_question_id)
        page3_incorrect_answer = _get_incorrect_answer(page3_question_id)
        self.assertNotEqual(page3_correct_answer, page3_incorrect_answer)

        choiced_answer = {
            'csrfmiddlewaretoken': True,
            'select_answer': page3_incorrect_answer,
        }
        form = SelectAnswerForm(page3_question_id, choiced_answer)
        self.assertTrue(form.is_valid())

        res = client_for_alex.post(
            path=page3_url,
            data=choiced_answer,
        )
        self.assertEqual(res.status_code, 302)

        ### 11. 確認ページで全て解答済みであることを確認
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'確認', res.content.decode())
        self.assertIn('確認', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答の問題があります。答え合わせしますか？',
                                        res.content.decode())
        self.assertFalse(get_decoded_text)

        res = client_for_alex.post(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 302)

        ### 12. 演習結果
        res = client_for_alex.get(path='/jrfoodadv/practice/result')
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'演習結果', res.content.decode())
        self.assertIn('演習結果', get_decoded_text[0])
        get_decoded_text = re.findall(r'66 %', res.content.decode())
        self.assertIn('66 %', get_decoded_text[0])
        get_decoded_text = re.findall(r'未解答とミスに再挑戦', res.content.decode())
        self.assertIn('未解答とミスに再挑戦', get_decoded_text[0])


    def test_practice_test_one_regular(self):
        """模擬試験の1回だけレギュラーテスト
        """
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        # ログイン
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/select_test/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        # 解答状況は模擬試験実施前は404になる
        res = client_for_alex.get(path='/jrfoodadv/practice_test/answer_status')
        self.assertEqual(res.status_code, 404)
        # 答え合わせ前確認は模擬試験実施前は404になる
        res = client_for_alex.get(path='/jrfoodadv/practice_test_finish_confirm/')
        self.assertEqual(res.status_code, 404)

        # 模擬試験のスタート
        choiced_data = {
            'unquestioned_and_mistakes': [], # チェックしない。['0']だとON。
            'start_button': '', # ボタンname指定
        }
        res = client_for_alex.get(
            path='/jrfoodadv/select_test/',
            data=choiced_data,
        )
        self.assertEqual(res.status_code, 302)

        # 1ページ目
        res = client_for_alex.get(path='/jrfoodadv/practice_test/',)
        self.assertEqual(res.status_code, 200)

        # 未解答でPOSTする
        res = client_for_alex.post(path='/jrfoodadv/practice_test/',)
        self.assertEqual(res.status_code, 302)

        # 2ページ目
        res = client_for_alex.get(path='/jrfoodadv/practice_test/?page=2',)
        self.assertEqual(res.status_code, 200)

        # 解答状況にすすむ。模擬試験実施後は200になる
        res = client_for_alex.get(path='/jrfoodadv/practice_test/answer_status')
        self.assertEqual(res.status_code, 200)

        # 2ページ目に戻る
        res = client_for_alex.get(path='/jrfoodadv/practice_test/?page=2')
        self.assertEqual(res.status_code, 200)

        def _get_correct_answer(page_question_id):
            """問題IDを渡して正答を返す"""
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            correct_answer = question.correct_answer
            return correct_answer

        # ページから問題ID取得
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                    res.content.decode())
        page_question_id = get_decoded_question_id[0]
        correct_answer = _get_correct_answer(page_question_id)

        # 正答をPOSTする
        choiced_answer = {
            'csrfmiddlewaretoken': True,
            'select_answer': correct_answer,
        }
        res = client_for_alex.post(
            path='/jrfoodadv/practice_test/?page=2',
            data=choiced_answer,
        )
        self.assertEqual(res.status_code, 302)

        # 3ページ目
        # 未解答ですすむ
        res = client_for_alex.get(path='/jrfoodadv/practice_test/?page=3')
        self.assertEqual(res.status_code, 200)

        # 4ページ目以降は、4-75問をforで処理
        for _ in range(4,76):
            url = f'/jrfoodadv/practice_test/?page={str(_)}'
            res = client_for_alex.get(path=url)
            self.assertEqual(res.status_code, 200)
            # ページから問題IDを取得
            get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                        res.content.decode())
            page_question_id = get_decoded_question_id[0]
            # 正答を取得
            correct_answer = _get_correct_answer(page_question_id)
            # 正答をPOSTする
            choiced_answer = {
                'csrfmiddlewaretoken': True,
                'select_answer': correct_answer,
            }
            res = client_for_alex.post(path=url, data=choiced_answer)

        # 答え合わせ前確認ページは200になる
        res = client_for_alex.get(path='/jrfoodadv/practice_test_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        # 答え合わせ前確認ページで答え合わせ(post)する
        res = client_for_alex.post(path='/jrfoodadv/practice_test_finish_confirm/')
        self.assertEqual(res.status_code, 302)

        # 演習結果
        res = client_for_alex.get(path='/jrfoodadv/practice/result')
        self.assertEqual(res.status_code, 200)
        self.assertIn('演習結果', res.content.decode())

        # 正答率
        # 1ページ目と3ページ目は未解答で、残りの73問は全て正しい答えを選択した
        correct_answer_rate = (73 / 75) * 100
        self.assertIn('73 / 75', res.content.decode()) # 正解は 73 / 75
        self.assertIn(f'{math.floor(correct_answer_rate)} %', res.content.decode()) # 正答率は 97 % でした


    def test_rechallenge_mistakes(self):
        """ 未解答とミスに再挑戦を実行してもエラーにならない
        URL: practice/rechallenge_mistakes
        前提条件: 既に他の誰かの回答がある
        """
        # 先にuser_jamesでRecordを作成しておく
        jrfoodadv_qs = JrFoodLabelingAdviseQuestion.objects.all()
        question_ids = [jrfoodadv.question_id for jrfoodadv in jrfoodadv_qs]
        user_james = User.objects.get(email='james-is-here@testaddress.coom')

        record_data = []
        for question_id in question_ids:
            data = {
                'question_id': question_id,
                'user_id': user_james.id,
                'current_answer': AnswerResult.CORRECT,
                'first_answer': AnswerResult.CORRECT,
            }
            record_data.append(Record(**data))
        # record一括作成
        Record.objects.bulk_create(record_data)
        self.assertEqual(len(question_ids), Record.objects.count())

        # ここから本番
        # 誰かでログインして、わざと間違える
        # 未解答とミスに再挑戦してもエラーにならない
        # jamesとは別のalexでログイン
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        # ログイン
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/select_test/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        # 練習モードの出題範囲('未出題')
        # 出題分野(1章、2章、3章、4章、5章、6章)
        # 出題数(1問)
        choiced_data = {
            'target': ['0'], # 未出題を選択
            'chapter': ['1', '2', '3', '4', '5', '6'], # 1章、2章、3章、4章、5章、6章を選択
            'answers': 1, # 1問
        }
        res = client_for_alex.get(
            path='/jrfoodadv/',
            data=choiced_data,
        )
        self.assertEqual(res.status_code, 302)

        # 未解答でpost
        page1_url = res.url
        res = client_for_alex.get(path=page1_url)
        self.assertEqual(res.status_code, 200)
        get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                        res.content.decode())
        page_question_id = get_decoded_question_id[0]

        # listにidを追加
        session_list = []
        session_list.append(page_question_id)
        # sessionの中に、idがあることを確認
        session = client_for_alex.session
        self.assertEqual(session["session_question_ids_list"], session_list)

        # 未解答(空)でpost
        res = client_for_alex.post(path=page1_url,)
        self.assertEqual(res.status_code, 302)
        # 確認
        res = client_for_alex.get(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 200)
        # 答え合わせをする
        res = client_for_alex.post(path='/jrfoodadv/practice_finish_confirm/')
        self.assertEqual(res.status_code, 302)
        # 演習結果
        res = client_for_alex.get(path='/jrfoodadv/practice/result')
        self.assertEqual(res.status_code, 200)
        # 未解答とミスに再挑戦があることを確認
        get_decoded_text = re.findall(r'未解答とミスに再挑戦', res.content.decode())
        self.assertIn('未解答とミスに再挑戦', get_decoded_text[0])

        # 「未解答とミスに再挑戦」ボタンの発火トリガーは、name="rechallenge_mistakes" ボタンをクリックすること
        # なのでgetにボタンを渡す
        button_name = {
            'rechallenge_mistakes': True
        }
        res = client_for_alex.get(
            path='/jrfoodadv/practice/rechallenge_mistakes',
            data=button_name)
        # 302遷移
        self.assertEqual(res.status_code, 302)

        page_url = res.url
        res = client_for_alex.get(path=page_url)
        self.assertEqual(res.status_code, 200)
        # 問題idが同じであることを確認
        get_decoded_question_id_2 = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                        res.content.decode())
        page_question_id_2 = get_decoded_question_id_2[0]
        self.assertEqual(page_question_id, page_question_id_2)
        # 半端に終えたのでsession削除
        session.delete()


    def test_practice_test_two_regular(self):
        """模擬試験で、「ランダムではなく、未出題・ミスの優先順で出題」に2回チェックを入れて実行。
        当初は、「問題が被っていなければ2回の終了時点でRecordは75*2=150になる」という理解だったが、認識ミスだった
        「ランダムではなく、未出題・ミスの優先順で出題」にチェックを入れると、2回目はミスした内容も問題に含まれる。
        よってここでの証明は、2回目に出題された問題の1回目はミスであることを証明する。
        """
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        # ログイン
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/select_test/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        def _get_incorrect_answer(page_question_id):
            """問題IDを渡して誤答を返す
            answers_listに全回答を用意する
            未解答（''）は含ませない
            """
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            answers_list = ['choice_a', 'choice_b', 'choice_c']
            # choice_d はある問題とない問題があるので場合わけ
            if question.choice_d:
                answers_list.append('choice_d')
            correct_answer = question.correct_answer
            # correct_answerをリストから削除
            answers_list.remove(correct_answer)
            # 最後に誤答しかないリストからランダムに値を取得する
            return random.choice(answers_list)

        def _get_random_answer(page_question_id):
            """問題IDを渡してランダムに解答を返す
            1. 解答が、choice_a, choice_b, choice_c, choice_d まで何問あるか確認
            2. 未解答（''）も含む
            3. ランダムに取得して返す
            """
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            answers_list = ['choice_a', 'choice_b', 'choice_c']
            # choice_d はある問題とない問題があるので場合わけ
            if question.choice_d:
                answers_list.append('choice_d')
            # 未解答も追加する
            answers_list.append('')
            return random.choice(answers_list)

        def _run_practice_test():
            # 模擬試験のスタート
            choiced_data = {
                'unquestioned_and_mistakes': ['0'], # チェックしない。['0']だとON。
                'start_button': '', # ボタンname指定
            }
            res = client_for_alex.get(
                path='/jrfoodadv/select_test/',
                data=choiced_data,
            )
            self.assertEqual(res.status_code, 302)

            test_ids_list = []
            for _ in range(1, 76): # 全75問
                url = f'/jrfoodadv/practice_test/?page={str(_)}'
                res = client_for_alex.get(path=url)
                self.assertEqual(res.status_code, 200)
                # ページから問題IDを取得
                get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                            res.content.decode())
                page_question_id = get_decoded_question_id[0]
                # ランダム解答を取得
                random_answer = _get_random_answer(page_question_id)
                # ランダム解答をPOSTする
                choiced_answer = {
                    'csrfmiddlewaretoken': True,
                    'select_answer': random_answer,
                }
                # 稀に全問正解の場合も発生する可能性があるので、必ず1ページ目は間違うようにしておく
                if _ == 1:
                    incorrect_answer = _get_incorrect_answer(page_question_id)
                    choiced_answer = {
                        'csrfmiddlewaretoken': True,
                        'select_answer': incorrect_answer,
                    }
                res = client_for_alex.post(path=url, data=choiced_answer)
                test_ids_list.append(page_question_id)
            self.assertEqual(len(test_ids_list), 75) # 問題総数75

            # 答え合わせ前確認ページは200になる
            res = client_for_alex.get(path='/jrfoodadv/practice_test_finish_confirm/')
            self.assertEqual(res.status_code, 200)
            # 答え合わせ前確認ページで答え合わせ(post)する
            res = client_for_alex.post(path='/jrfoodadv/practice_test_finish_confirm/')
            self.assertEqual(res.status_code, 302)

            # 演習結果
            res = client_for_alex.get(path='/jrfoodadv/practice/result')
            self.assertEqual(res.status_code, 200)
            return test_ids_list

        # 模擬試験1回目
        test_ids_list_01 = _run_practice_test()
        # 模擬試験2回目
        test_ids_list_02 = _run_practice_test()

        # 重複した要素を抽出
        duplicated_ids = []
        for test_id in test_ids_list_01:
            if test_id in test_ids_list_02:
                duplicated_ids.append(test_id)
        record_qs = Record.objects.filter(question_id__in=duplicated_ids)

        for question in record_qs:
            self.assertTrue(question.first_answer) # 重複しているRecordのfirst_answerとsecond_answerは必ず存在する
            self.assertTrue(question.second_answer)
            # first_answerは必ず不正解である
            # → 最初に「ランダムではなく、未出題・ミスの優先順で出題」にチェックを入れているから、不正解が優先されている
            self.assertTrue(question.first_answer, AnswerResult.INCORRECT)


    def test_practice_test_many_times(self):
        """模擬試験を複数回続けて実行してもエラーが起きないことを確認する。また毎回同じ問題IDで問題が生成されないことも確認する。
        以下の2点を特にチェック
        ・20220620現在は全問で275問だが、それを超えたタイミングで模擬試験を生成、終了した時にrecordが275問を超えて生成されるエラーがあった。
        ・模擬試験IDがn回目の時とn回目の時が、並びは別だが問題は全く同じだった。
        検証として
        unquestioned_and_mistakesの「ランダムではなく、未出題・ミスの優先順で出題」にチェックを入れて9回実行する。
        今度はチェックを入れないで2回実行する。
        """
        user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        # ログイン
        client_for_alex = Client()
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/select_test/',
            data=user_data,
        )
        self.assertEqual(res.status_code, 302)

        def _get_correct_answer(page_question_id):
            """問題IDを渡して正答を返す"""
            question = JrFoodLabelingAdviseQuestion.objects.get(question_id=page_question_id)
            correct_answer = question.correct_answer
            return correct_answer

        def _run_practice_test(unquestioned_and_mistakes):
            # 模擬試験のスタート
            res = client_for_alex.get(path='/jrfoodadv/')
            self.assertEqual(res.status_code, 200)

            data = {'start_button': ''} # ボタンname指定
            data.update(unquestioned_and_mistakes) # 辞書型の結合

            res = client_for_alex.get(
                path='/jrfoodadv/select_test/',
                data=data,
            )
            self.assertEqual(res.status_code, 302)

            test_ids_list = []
            # 全75問をfor文で回す。
            for _ in range(1, 76):
                url = f'/jrfoodadv/practice_test/?page={str(_)}'
                res = client_for_alex.get(path=url)
                self.assertEqual(res.status_code, 200)
                # ページから問題IDを取得
                get_decoded_question_id = re.findall(r'(?<=data-question-id=")j[0-9]{1,6}',
                                                            res.content.decode())
                # str
                page_question_id = get_decoded_question_id[0]
                # 正答を取得
                correct_answer = _get_correct_answer(page_question_id)
                # とりあえず正答をPOSTする
                choiced_answer = {
                    'csrfmiddlewaretoken': True,
                    'select_answer': correct_answer,
                }
                # 出題される問題IDが被っていないことを確認
                if page_question_id in test_ids_list:
                    self.assertNotIn(page_question_id, test_ids_list)
                test_ids_list.append(page_question_id)
                # 問題なければpost
                res = client_for_alex.post(path=url, data=choiced_answer)

            # 答え合わせ前確認ページは200になる
            res = client_for_alex.get(path='/jrfoodadv/practice_test_finish_confirm/')
            self.assertEqual(res.status_code, 200)
            # 答え合わせ前確認ページで答え合わせ(post)する
            res = client_for_alex.post(path='/jrfoodadv/practice_test_finish_confirm/')
            self.assertEqual(res.status_code, 302)
            # 演習結果
            res = client_for_alex.get(path='/jrfoodadv/practice/result')
            self.assertEqual(res.status_code, 200)

            return test_ids_list # 問題重複チェックのためにtest_ids_listを返す

        all_questions = JrFoodLabelingAdviseQuestion.objects.count()
        answers = 75 # 模擬試験の解答数
        # 何回まで未解答の問題に遭遇するか
        target_count = all_questions // answers

        # unquestioned_and_mistakesをONで9回実行
        unquestioned_and_mistakes_on = {
            'unquestioned_and_mistakes': ['0']} # チェックON。ONは['0']。OFFの場合は[]。

        for _ in range(1,target_count+1): # 明示的に1回目からn回目
            _run_practice_test(unquestioned_and_mistakes_on)
            res = client_for_alex.get(path='/jrfoodadv/record/list/')
            self.assertEqual(res.status_code, 200)
            # 学習履歴は75問*n回であることを確認
            # ちなみにここでは正答しかしていないので、「ランダムではなく、未出題・ミスの優先順で出題」にチェックを入れた場合
            # 未出題が優先され、ミスの出題はなく結果として75*2のRecordしか生まれない
            self.assertIn(f'data-count_all_questions="{75*_}"', res.content.decode())

        # 学習履歴は75問*n回を超えると、self.assertIn(f'data-count_all_questions="{75*_}"', res.content.decode())
        # ができなくなるので、for文を回さないで確認する。
        _run_practice_test(unquestioned_and_mistakes_on) # 4回目(20220622時点)
        _run_practice_test(unquestioned_and_mistakes_on) # 5回目
        _run_practice_test(unquestioned_and_mistakes_on) # 6回目
        test_ids_list_07 = _run_practice_test(unquestioned_and_mistakes_on) # 7回目
        test_ids_list_07.sort()
        test_ids_list_08 = _run_practice_test(unquestioned_and_mistakes_on) # 8回目
        test_ids_list_08.sort()
        # 7回目と8回目の問題IDが被っていないことを確認
        self.assertNotEqual(test_ids_list_07, test_ids_list_08)
        test_ids_list_09 = _run_practice_test(unquestioned_and_mistakes_on) # 9回目
        test_ids_list_09.sort()
        self.assertNotEqual(test_ids_list_08, test_ids_list_09)

        # unquestioned_and_mistakes をOFFにしても問題ないことを確認
        # unquestioned_and_mistakesをONで9回実行
        unquestioned_and_mistakes_off = {
            'unquestioned_and_mistakes': []} # チェックON。ONは['0']。OFFの場合は[]

        test_ids_list_10 = _run_practice_test(unquestioned_and_mistakes_off) # 10回目
        test_ids_list_10.sort()
        test_ids_list_11 = _run_practice_test(unquestioned_and_mistakes_off) # 11回目
        test_ids_list_11.sort()
        # 問題が被っていないことを確認
        self.assertNotEqual(test_ids_list_10, test_ids_list_11)

        # 履歴の数と問題総数がequalであることを確認
        all_questions = JrFoodLabelingAdviseQuestion.objects.count()
        res = client_for_alex.get(path='/jrfoodadv/record/list/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-count_all_questions="{all_questions}"', res.content.decode())


    def tearDown(self):
        """データベースの掃除
        """
        User.objects.all().delete()
        UserCourse.objects.all().delete()
        Record.objects.all().delete()
        TimeLeft.objects.all().delete()
        JrFoodLabelingAdviseQuestion.objects.all().delete()
