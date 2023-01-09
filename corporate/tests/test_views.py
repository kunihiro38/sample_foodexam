"""
全体テスト
python manage.py test corporate.tests
クラス単位のテスト 例
python manage.py test corporate.tests.test_views.TestRegularTests

---書き方マナー---
1. テストは分かりやすく、見やすく
2. 全てのページに対してのassertEqualを当てる
3. ループ処理はテストコード中でなるべく使用しない
4. 常に値が想定したものになっているかを確認するテストを書く
5. 先に失敗するパターンを書く

---比較対象---
例えば、assertEqualなどで左右で比較をする場合。
左：調査対象の式。変化する値。
右：比較対象の式。あまり変化しない。
"""

import datetime
import re

from django.core import mail
from django.db.models import Q
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model

from corporate.forms import InquiryAddForm, SignUpForm, SigninForm, EditUsernameForm, \
    ChangePasswordForm
from corporate.models import UserCourse, PaymentCourse, Release, Information, Testimonials,\
    Exam, PaymentPlan

User = get_user_model()


class TestRegularTests(TestCase):
    """全編通しのレギュラーテスト
    """
    def setUp(self):
        # 同じテストクラス内で共通で使用するデータはここで作成する
        # johnは無料会員
        User.objects.create_user(username='john',
                                    email='john@examp1e.com',
                                    password='abcdefghij1234!')
        self.response = self.client.post(reverse('corporate:password_reset'),
                                            { 'email': 'john@examp1e.com' })
        self.email = mail.outbox[0]

        latest_user = User.objects.order_by('-date_joined')
        usercourse_data = {
            'user_id': latest_user[0].id,
        }
        UserCourse.objects.create(**usercourse_data)

        # Aliceは有料会員
        User.objects.create_user(username='Alice',
                                    email='alice@goalice.com',
                                    password='xyzALICE123!!')
        latest_user = User.objects.order_by('-date_joined')
        dt_now = datetime.datetime.now()
        tomorrow = dt_now + datetime.timedelta(days=1)
        dt_now = make_aware(dt_now)
        tomorrow = make_aware(tomorrow)
        usercourse_data = {
            'user_id': latest_user[0].id,
            'payment_course': PaymentCourse.JRFOODADV,
            'paid_at': dt_now,
            'expired_at': tomorrow,
        }
        UserCourse.objects.create(**usercourse_data)

    def test_access_no_signin_to_corporate(self):
        """コーポレートサイトにログインしていない状態で一通りアクセスできる"""
        client = Client()
        res = client.get(path='/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/signup/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/introduction/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/course/')
        self.assertEqual(res.status_code, 200)
        # res = client.get(path='/pay/jrfoodadv/')
        # self.assertEqual(res.status_code, 200)
        res = client.get(path='/course/jrfoodadv/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/course/jrfoodadv/monthly')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/course/jrfoodadv/10days')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/course/jrfoodadv/3days')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/signin/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/password_reset/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/terms')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/policy')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/law')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/inquiry/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/info/')
        self.assertEqual(res.status_code, 200)
        res = client.get(path='/column/')
        self.assertEqual(res.status_code, 200)


    def test_invalid_access_no_signin_to_corporate(self):
        """全て存在する正規のURLにinvalidな英数字を付け足してテストする"""
        client = Client()
        res = client.get(path='/invalide_url')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/signup/invalide_url1234')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/introduction/invalide_url!@:')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/course/invalide_url-=|')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/pay/jrfoodadv/invalide_url+*`')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/signin/123456')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/password_reset/invalide_url{*}')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/terms123456789')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/policyxyz')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/law*')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/inquiry/$#"!')
        self.assertEqual(res.status_code, 404)

    def test_toppage(self):
        """トップページでのログイン・非ログイン時のリダイレクト先の確認
        """
        # anonymousの時はmain_kvにプラン選択のリダイレクト先リンクが表示される
        # 「無料ではじめる」ボタンのところ
        client = Client()
        res = client.get(path="/")
        self.assertEqual(res.status_code, 200)
        redirect_link = 'href="/course/jrfoodadv/" data-href="/course/jrfoodadv/"'
        self.assertIn(redirect_link, res.content.decode())

        # 有料会員の時はリンク先が練習モードのトップページ
        client_for_alice = Client()
        res = client_for_alice.get(path='/signin/')
        login_user_data = {
            'email': 'alice@goalice.com',
            'password': 'xyzALICE123!!'}
        res = client_for_alice.post(
            path='/signin/',
            data=login_user_data)
        res = client_for_alice.get(path="/")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(redirect_link, res.content.decode())
        login_user_redirect_link = 'href="/jrfoodadv/" data-href="/jrfoodadv/"'
        self.assertIn(login_user_redirect_link, res.content.decode())


    def test_breadcrumbs(self):
        """breadcrumbsの有無を確認するテスト
        corporateアプリのみにbreadcrumbsは存在。jrfoodadvはなし。
        indexとmaintenance→なし
        それ以外→あり
        """
        breadcrumbs_content_1 = \
            '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/Listitem"><a itemprop="item" href="/"><span itemprop="name">ホーム</span></a><meta itemprop="position" content="1"/></li>'

        client = Client()
        res = client.get(path='/')
        self.assertEqual(res.status_code, 200)
        # indexのトップページにはパンくずリストは置いていない
        self.assertNotIn(breadcrumbs_content_1, res.content.decode())

        res = client.get(path='/introduction/')
        # 2階層
        breadcrumbs_content_2_for_introduction = \
            '<a itemprop="item" href="/introduction/"><span itemprop="name">フードイグザムとは？</span></a>'
        self.assertIn(breadcrumbs_content_2_for_introduction, res.content.decode())
        breadcrumbs_content_2_meta = '<meta itemprop="position" content="2">'
        self.assertIn(breadcrumbs_content_2_meta, res.content.decode())

        # 2階層
        res = client.get(path='/info/')
        self.assertEqual(res.status_code, 200)
        breadcrumbs_content_2_for_info = \
            '<a itemprop="item" href="/info/"><span itemprop="name">お知らせ一覧</span></a>'
        self.assertIn(breadcrumbs_content_2_for_info, res.content.decode())
        breadcrumbs_content_2_meta = '<meta itemprop="position" content="2">'
        self.assertIn(breadcrumbs_content_2_meta, res.content.decode())

        # 3階層（/info/の直下）
        dict_public_information = {
            'category': 3, # CAMPAIGN
            'title': '新規入会キャンペーン',
            'description': '新規入会キャンペーンを開催しました!!',
            'contributor': 1, # admin
            'release': Release.PUBLIC, # 下書き
        }
        # objectをcreateする
        info = Information.objects.create(**dict_public_information)
        path = f'/info/{info.id}'
        res = client.get(path=path)
        self.assertEqual(res.status_code, 200)
        # breadcrumbsの階層が3つあることを確認
        # スペースの関係で分解してassertInを確認

        # 1階層目
        breadcrumbs_content_1 = \
            '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/Listitem"><a itemprop="item" href="/"><span itemprop="name">ホーム</span></a><meta itemprop="position" content="1"/></li>'
        self.assertIn(breadcrumbs_content_1, res.content.decode())
        breadcrumbs_content_2_li_tag = \
            '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/Listitem">'
        self.assertIn(breadcrumbs_content_2_li_tag, res.content.decode())

        # 2階層目
        content_2_num = 2
        content_2_url = '/info/'
        content_2_title = 'お知らせ一覧'
        breadcrumbs_content_2_a_tag = f'<a itemprop="item" href="{content_2_url}"><span itemprop="name">{content_2_title}</span></a>'
        self.assertIn(breadcrumbs_content_2_a_tag, res.content.decode())
        breadcrumbs_content_2_meta_tag = f'<meta itemprop="position" content="{content_2_num}">'
        self.assertIn(breadcrumbs_content_2_meta_tag, res.content.decode())

        # 3階層目
        content_3_num = 3
        content_3_url = path
        content_3_title = info.title
        breadcrumbs_content_2_a_tag = f'<a itemprop="item" href="{content_3_url}"><span itemprop="name">{content_3_title}</span></a>'
        self.assertIn(breadcrumbs_content_2_a_tag, res.content.decode())
        breadcrumbs_content_2_meta_tag = f'<meta itemprop="position" content="{content_3_num}">'
        self.assertIn(breadcrumbs_content_2_meta_tag, res.content.decode())


    def test_information(self):
        """お知らせ画面のテスト
        releaseが公開（PUBLIC）なのでアクセスでき、404にならない
        """
        client = Client()
        dict_public_information = {
            'category': 1, # NEWS
            'title': '新規登録受付',
            'description': 'ユーザーの新規登録開始は4月頃を予定しております。登録開始までもう暫くお待ちください。',
            'contributor': 1, # admin
            'release': Release.PUBLIC, # 公開
        }
        # objectをcreateする
        public_information = Information.objects.create(**dict_public_information)

        # releaseが下書き（DRAFT）の場合は公開されずに、アクセスしたら404になる
        dict_draft_information = {
            'category': 3, # CAMPAIGN
            'title': '新規入会キャンペーン',
            'description': '新規入会キャンペーンを開催しました!!',
            'contributor': 1, # admin
            'release': Release.DRAFT, # 下書き 
        }
        # objectをcreateする
        draft_information = Information.objects.create(**dict_draft_information)

        # 存在しないお知らせ画面は404になる
        res = client.get(path='/info/100')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/info/invalid')
        self.assertEqual(res.status_code, 404)

        # ok
        res = client.get(path=f'/info/{public_information.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-info-id="{public_information.id}"', res.content.decode())
        # 「お知らせ一覧に戻る」が含まれている
        self.assertIn('お知らせ一覧に戻る', res.content.decode())
        self.assertIn('href="/info/"', res.content.decode())

        # ng
        res = client.get(path=f'/info/{draft_information.id}')
        self.assertEqual(res.status_code, 404)
        self.assertNotIn(f'data-info-id="{draft_information.id}"', res.content.decode())


    def test_column(self):
        """学習コラム画面のテスト
        releaseが公開（PUBLIC）なのでアクセスでき、404にならない
        また次のページと前のページが表示されている
        """
        client = Client()
        dict_public_column = {
            'category': 6, # COLUMN
            'title': '食品表示検定合格への道001',
            'description': '食品表示検定合格への道を紹介します。',
            'contributor': 1, # admin
            'release': Release.PUBLIC, # 公開
        }
        # objectをcreateする
        public_column = Information.objects.create(**dict_public_column)

        # releaseが下書き（DRAFT）の場合は公開されずに、アクセスしたら404になる
        dict_public_column = {
            'category': 6, # COLUMN
            'title': '食品表示検定合格への道002',
            'description': '新規入会キャンペーンを開催しました!!',
            'contributor': 1, # admin
            'release': Release.DRAFT, # 下書き 
        }
        # objectをcreateする
        draft_column = Information.objects.create(**dict_public_column)

        # 存在しないお知らせ画面は404になる
        res = client.get(path='/column/100')
        self.assertEqual(res.status_code, 404)
        res = client.get(path='/column/invalid')
        self.assertEqual(res.status_code, 404)

        # ok
        res = client.get(path=f'/column/{public_column.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-info-id="{public_column.id}"', res.content.decode())
        # 「お知らせ一覧に戻る」が含まれている
        self.assertIn('学習コラム一覧に戻る', res.content.decode())
        self.assertIn('href="/column/"', res.content.decode())

        # ng
        res = client.get(path=f'/info/{draft_column.id}')
        self.assertEqual(res.status_code, 404)
        self.assertNotIn(f'data-info-id="{draft_column.id}"', res.content.decode())

        # 次のページと前のページが表示されている
        # まず新たにinfoを追加する
        dict_public_column = {
            'category': 6, # COLUMN
            'title': '学習コラム3',
            'description': '勉強がうまくいく方法3',
            'contributor': 1, # admin
            'release': Release.PUBLIC, # 公開 
        }
        # objectをcreateする
        public_column = Information.objects.create(**dict_public_column)

        dict_public_column = {
            'category': 6, # COLUMN
            'title': '学習コラム4',
            'description': '勉強がうまくいく方法4',
            'contributor': 1, # admin
            'release': Release.PUBLIC, # 公開 
        }
        # objectをcreateする
        public_column = Information.objects.create(**dict_public_column)

        res = client.get(path=f'/column/{public_column.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-info-id="{public_column.id}"', res.content.decode())
        # 最新の最新の学習コラム個別ページを見ている。
        # next-pageのリンクは存在しないがprev-pageのリンクは存在する
        # public_column.idは4
        prev_info_id = public_column.id-1
        self.assertNotIn(f'data-next-info-id', res.content.decode())
        self.assertIn(f'data-prev-info-id="{prev_info_id}"', res.content.decode())

        # public_column の3には、4（next_page）と1（prev_page）の両方が表示されている
        public_column_id = prev_info_id
        res = client.get(path=f'/column/{public_column_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-info-id="{public_column_id}"', res.content.decode())

        next_info_id = public_column_id+1
        prev_info_id = public_column_id-2
        self.assertIn(f'data-next-info-id="{next_info_id}"', res.content.decode())
        self.assertIn(f'data-prev-info-id="{prev_info_id}"', res.content.decode())


    def test_testimonials(self):
        """合格体験記のテスト
        トップページの表示
        一覧表示
        個別表示
        個別表示のページング確認
        """
        client = Client()
        res = client.get(path='/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('合格体験記はありません。', res.content.decode())
        res = client.get(path='/testimonials/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('データがありません。', res.content.decode())

        # 合格体験記のデータ5つ作成
        create_data_cnt = 5
        testimonials_obj = []
        for index in range(create_data_cnt):
            data = {
                'exam_subject': Exam.JRFOODADV,
                'payment_course': PaymentCourse.JRFOODADV,
                'payment_plan': PaymentPlan.THREE_DAYS_PLAN,
                'pen_name': 'SampleUser',
                'email': 'sample@examp1e.com',
                'title': f'{index}つめの件名です。',
                'exam_date': make_aware(datetime.datetime.now()) + datetime.timedelta(days=-10),
                'points': '100',
                'times': '初めて',
                'learning_time': '1ヶ月',
                'referenced_site': '',
                'learning_method': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                                sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
                'impression': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                                sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
                'advice': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                                sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
                'next_exam': '食品表示検定中級',
                'improvements': 'これからも頑張ってください!!',
                'contributor': '1', # 管理人
                'release': Release.PUBLIC,
                'published_at': (make_aware(datetime.datetime.now())\
                                            + datetime.timedelta(days=-5))\
                                            + datetime.timedelta(days=+index),
            }
            testimonials_obj.append(Testimonials(**data))
        Testimonials.objects.bulk_create(testimonials_obj)

        # 一覧表示
        testimonials = Testimonials.objects.filter(Q(release=Release.PUBLIC)).latest('published_at')
        res = client.get(path='/testimonials/')
        self.assertIn(f'data-testimonials-id="{testimonials.id}"', res.content.decode())

        # 個別合格体験記
        res = client.get(path=f'/testimonials/{testimonials.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-testimonials-id="{testimonials.id}"', res.content.decode())

        # ページング確認
        # 最新の個別ページを表示しているので次のページはない
        self.assertNotIn(f'data-prev-testimonials-id="{testimonials.id + 1}"', res.content.decode())
        # 前のページはある
        self.assertIn(f'data-prev-testimonials-id="{testimonials.id - 1}"', res.content.decode())

        # 2番目の個別合格体験記
        second_page = testimonials.id - 1
        res = client.get(path=f'/testimonials/{second_page}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'data-testimonials-id="{second_page}"', res.content.decode())

        # ページング確認
        # 次のページはある
        self.assertNotIn(f'data-prev-testimonials-id="{second_page + 1}"', res.content.decode())
        # 前のページはある
        self.assertIn(f'data-prev-testimonials-id="{second_page - 1}"', res.content.decode())


    def test_inquiry_is_true(self):
        """お問い合わせのテスト
        """
        client = Client()
        res = client.get(path='/inquiry/')
        self.assertEqual(res.status_code, 200)
        inquiry_data = {
            'name': 'sample_inquiry_user',
            'email': 'sample@example.com',
            'subject': 'This is subject',
            'message': 'This is test message.',
        }
        form = InquiryAddForm(inquiry_data)
        self.assertTrue(form.is_valid())
        res = client.post(
            path='/inquiry/',
            data=inquiry_data
        )
        self.assertEqual(res.status_code, 302)
        res = client.get(path='/inquiry/success')
        self.assertIn('送信が完了しました。', res.content.decode())


    def test_testimonials_is_true(self):
        """合格体験記の投稿テスト
        """
        client = Client()
        res = client.get(path='/testimonials/post/')
        self.assertEqual(res.status_code, 200)
        testimonials_data = {
            'exam_subject': 1,
            'payment_course': 1,
            'payment_plan': 1,
            'pen_name': 'SampleUser',
            'email': 'sample@examp1e.com',
            'title': '件名です。',
            'exam_date': '2022-11-11',
            'points': '100',
            'times': '初めて',
            'learning_time': '1ヶ月',
            'referenced_site': '',
            'learning_method': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'impression': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'advice': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'next_exam': '食品表示検定中級',
            'improvements': 'これからも頑張ってください!!',
        }
        res = client.post(
            path='/testimonials/post/',
            data=testimonials_data)
        self.assertEqual(res.status_code, 302)
        res = client.get(path='/testimonials/post/success')
        self.assertIn('送信が完了しました。', res.content.decode())

        res = client.get(path='/testimonials/post/')
        self.assertEqual(res.status_code, 200)
        testimonials_data = {
            'exam_subject': 1,
            'payment_course': 1,
            'payment_plan': 3,
            'pen_name': 'SampleUser',
            'email': 'sample@examp1e.com',
            'title': '件名です。',
            'exam_date': '2022-11-08',
            'points': '78',
            'times': '初めて',
            'learning_time': '60時間',
            'referenced_site': 'food exam',
            'learning_method': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'impression': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'advice': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'next_exam': '食品表示検定中級',
            'improvements': '',
        }
        res = client.post(
            path='/testimonials/post/',
            data=testimonials_data)
        self.assertEqual(res.status_code, 302)
        res = client.get(path='/testimonials/post/success')
        self.assertIn('送信が完了しました。', res.content.decode())


    def test_testimonials_is_false(self):
        """合格体験記の投稿テストが失敗する
        """
        client = Client()
        res = client.get(path='/testimonials/post/')
        self.assertEqual(res.status_code, 200)
        testimonials_data = {
            'exam_subject': 1,
            'payment_course': 0,
            'payment_plan': 1,
            'pen_name': 'SampleUser',
            'email': 'sample@examp1e.com',
            'title': '件名です。',
            'exam_date': '2022-11-11',
            'points': '100',
            'times': '初めて',
            'learning_time': '1ヶ月',
            'referenced_site': '',
            'learning_method': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'impression': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'advice': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit,\
                            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ',
            'next_exam': '食品表示検定中級',
            'improvements': 'これからも頑張ってください!!',
        }
        res = client.post(
            path='/testimonials/post/',
            data=testimonials_data)
        # 302リダイレクトされず200のまま
        self.assertEqual(res.status_code, 200)
        # course_used は0以外を選択することが必須
        self.assertIn('選択してください。', res.content.decode())


    def test_password_reset_is_true(self):
        """パスワードリセットのレギュラーテスト
        setUpで作成した john を使用
        """
        client_for_john = Client()

        # リセットパスワード
        res = client_for_john.get(path='/password_reset/')
        self.assertEqual(res.status_code, 200)

        # 明らかに間違いのemailをpostする
        invalid_email = {'email': 'a'*300+'@examp1e.com'}
        res = client_for_john.post(
            path='/password_reset/',
            data=invalid_email,
        )
        self.assertEqual(res.status_code, 200)
        len_email = len(invalid_email['email'])
        error_msg = f'この値は 254 文字以下でなければなりません( {len_email} 文字になっています)。'
        self.assertIn(error_msg, res.content.decode())

        # 未登録のemailをpostする
        incorrect_email = {'email': 'john2@examp1e.com'}
        res = client_for_john.post(
            path='/password_reset/',
            data=incorrect_email,
        )
        self.assertEqual(res.status_code, 200)
        error_msg = '入力されたメールアドレスは登録されていません。'
        self.assertIn(error_msg, res.content.decode())

        # 正しいemailをpostする
        # setUpで作成したuser_johnを使用
        user_john = User.objects.get(email='john@examp1e.com')
        correct_email = {'email': user_john.email}
        res = client_for_john.post(
            path='/password_reset/',
            data=correct_email,
        )
        self.assertEqual(res.status_code, 302)


    def test_password_reset_mail(self):
        """パスワードリセットのメールのテスト
        setUpで作成したjohnを使用
        """
        self.assertEqual('【フードイグザム】パスワード再設定のメールの送信', self.email.subject)
        context = self.response.context
        token = context.get('token')
        uid = context.get('uid')
        password_reset_token_url = reverse('corporate:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })
        self.assertIn(password_reset_token_url, self.email.body)
        self.assertIn('john', self.email.body)
        self.assertEqual(['john@examp1e.com',], self.email.to)


    def test_access_to_jrfoodadv(self):
        """ アクセステスト """
        # 新規登録ユーザー→jrfoodadvにアクセスできない
        # 新規にuserのAlexを作成
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
            'payment_course': 0,
        }
        UserCourse.objects.create(**user_course_data)
        client_for_alex = Client()
        login_user_data = {
            'email': 'alex-from-brazil@examp1e.coom',
            'password': 'alex20210604',
        }
        res = client_for_alex.post(
            path='/jrfoodadv/signin/?next=/jrfoodadv/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)

        # 食品表示検定・初級コース支払い -> 20220629 -> 最初に作成した月額1100円の固定コース。案として残しておく
        # 有効期限は現在時刻から30日後で、かつ23時59分であるか
        # res = client_for_alex.get(path='/pay/jrfoodadv/')
        # self.assertEqual(res.status_code, 200)
        # dt_now = datetime.datetime.now()
        # after_thirty_days = dt_now + datetime.timedelta(days=settings.USABLE_PERIOD) # 31
        # after_thirty_days = after_thirty_days.date()

        # year = after_thirty_days.strftime('%Y年')
        # month = after_thirty_days.strftime('%m月').lstrip('0')
        # day = after_thirty_days.strftime('%d日').lstrip('0')
        # day_of_week = after_thirty_days.strftime('(%a)')
        # # 曜日の日本語変換
        # # import locale
        # # locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
        # w_list = ['(月)', '(火)', '(水)', '(木)', '(金)', '(土)', '(日)']
        # day_of_week = w_list[after_thirty_days.weekday()]
        # time = ' 23時59分'
        # after_thirty_days_and_time = year + month + day + day_of_week + time
        # self.assertIn(after_thirty_days_and_time, res.content.decode())

        def _access_to_jrfoodadv(res, self, status_code):
            res = client_for_alex.get(path='/jrfoodadv/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/setting/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/setting/del_record/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/setting/del_record/success')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/profile/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/search/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/record/list/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/record/memos/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/record/favorites/')
            self.assertEqual(res.status_code, status_code)
            res = client_for_alex.get(path='/jrfoodadv/select_test/')
            self.assertEqual(res.status_code, status_code)

        # 無料プランでもjrfoodadvにアクセスできる
        _access_to_jrfoodadv(res, self, 200)
        # 支払い完了したユーザー→jrfoodadvにアクセスできる
        # expired_atは仮でtomorrowとおく
        dt_now = datetime.datetime.now()
        tomorrow = dt_now + datetime.timedelta(days=1)
        dt_now = make_aware(dt_now)
        tomorrow = make_aware(tomorrow)
        user_course = UserCourse.objects.get(user_id=user_id)
        user_course.payment_course = PaymentCourse.JRFOODADV
        user_course.paid_at = dt_now
        user_course.expired_at = tomorrow
        user_course.save()
        _access_to_jrfoodadv(res, self, 200)

        # 支払い完了、期限切れユーザー→jrfoodadvにアクセスできる
        # expired_atは仮でdt_nowとおく
        user_course = UserCourse.objects.get(user_id=user_id)
        user_course.paid_at = dt_now
        user_course.expired_at = dt_now
        user_course.save()
        _access_to_jrfoodadv(res, self, 200)


    def test_all_regular_true(self):
        """レギュラーテスト"""
        client = Client()
        res = client.get(path='/')
        self.assertEqual(res.status_code, 200)

        # 新規登録画面で255文字数を超えるメールアドレスでは作成できない
        def _make_test_data(override_dict):
            default_user_data = {
                'username': 'sample_user',
                'email': 'sample@example.com',
                'password': 'abcdefghijklmn',
                'confirm_password': 'abcdefghijklmn',
            }
            ret = default_user_data.copy()
            ret.update(override_dict)
            return ret

        test_user_data01 = _make_test_data({
            'email': 'a'*300 + '@example.com'
        })
        res = client.post(
            path='/signup/',
            data=test_user_data01
        )
        form = SignUpForm(test_user_data01)
        len_test_user_data01 = str(len(test_user_data01['email']))
        errorlist = f'この値は 254 文字以下でなければなりません( {len_test_user_data01} 文字になっています)。'
        self.assertEqual(form.errors['email'], [errorlist])
        self.assertFalse(form.is_valid())

        # 長すぎる名前は作成できない
        test_user_data02 = _make_test_data({
            'username': 'a'*300+ '@example.com',
        })
        form = SignUpForm(test_user_data02)
        len_test_user_data02 = str(len(test_user_data02['username']))
        errorlist = f'この値は 150 文字以下でなければなりません( {len_test_user_data02} 文字になっています)。'
        self.assertEqual(form.errors['username'], [errorlist])
        self.assertFalse(form.is_valid())

        # 新規登録画面でパスワードが不一致だと作成できない
        test_user_data03 = _make_test_data({
            'password1': 'test_user_password0805' ,
            'password2': 'sample_user_password0805',
        })
        form = SignUpForm(test_user_data03)
        self.assertEqual(form.errors['password2'], ['確認用パスワードが一致しません。'])
        self.assertFalse(form.is_valid())

        # 新規登録画面で新規ユーザーを作成できる
        # res = client.get(path='/signup/')
        # self.assertEqual(res.status_code, 200)
        # signup_user_data = {
        #     'username': 'sample_user',
        #     'email': 'sample@examp1e.com',
        #     'password1': 'abcdefghijklmn',
        #     'password2': 'abcdefghijklmn',
        # }
        # client_for_sampleuser = Client()
        # self.response = self.client.post(reverse('corporate:signup'), signup_user_data)

        # res = client_for_sampleuser.post(
        #     path='/signup/',
        #     data=signup_user_data
        # )
        # self.assertEqual(res.status_code, 302)

        # res = client_for_sampleuser.get(
        #     path='/signup/sent'
        # )
        # self.assertEqual(res.status_code, 200)
        # get_decoded_text = re.findall(r'会員登録確認メールを送信しました。', res.content.decode())
        # self.assertIn('会員登録確認メールを送信しました。', get_decoded_text[0])
        # self.assertEqual(res.status_code, 200)

        client_for_tom = Client()
        user_tom_data = {
            'username': 'user_tom',
            'email': 'tom_is_fine@examp1e.com',
            'password': 'abcdefghijklmn',
        }
        User.objects.create_user(**user_tom_data)
        latest_user = User.objects.order_by('-date_joined')
        usercourse_data = {
            'user_id': latest_user[0].id,
        }
        UserCourse.objects.create(**usercourse_data)

        res = client_for_tom.get(path='/signin/')
        # 間違ったemailとpasswordではNG
        self.assertEqual(res.status_code, 200)
        login_user_data = {
            'email': 'tom_is_not_fine@example.com',
            'password': 'ngpasswordisHERE!'
        }
        res = client_for_tom.post(
            path='/signin/',
            data=login_user_data
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('class="errorlist nonfield"', res.content.decode())
        self.assertIn('メールアドレスかパスワードが間違っています。', res.content.decode())

        # OK
        self.assertEqual(res.status_code, 200)
        login_user_data = {
            'email': user_tom_data['email'],
            'password': user_tom_data['password'],
        }
        res = client_for_tom.post(
            path='/signin/',
            data=login_user_data,
        )

        # ログイン中のユーザーはアクセスできない
        res = client_for_tom.get(
            path='/signup/'
        )
        self.assertEqual(res.status_code, 403)

        # ログアウトできる
        res = client_for_tom.get(
            path='/profile/'
        )
        self.assertEqual(res.status_code, 200)
        res = client_for_tom.post(
            path='/profile/'
        )
        self.assertEqual(res.status_code, 302)
        res = client_for_tom.get(
            path='/profile/logout'
        )
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'ログアウトしました。', res.content.decode())
        self.assertIn('ログアウトしました。', get_decoded_text[0])

        # 重複したメールアドレスでは登録できない
        res = client.get(
            path='/signup/'
        )
        self.assertEqual(res.status_code, 200)
        signup_user_data2 = {
            'username': 'sample_user2',
            'email': 'tom_is_fine@examp1e.com',
            'password1': 'abcdefghijklmnop',
            'password2': 'abcdefghijklmnop',
        }
        client_for_sampleuser2 = Client()
        res = client_for_sampleuser2.post(
            path='/signup/',
            data=signup_user_data2
        )
        self.assertEqual(res.status_code, 200)
        get_decoded_text = re.findall(r'既に登録されているメールアドレスです。', res.content.decode())
        self.assertIn('既に登録されているメールアドレスです。', get_decoded_text[0])

        # ログインできる
        res = client_for_tom.get(path='/signin/')
        self.assertEqual(res.status_code, 200)
        login_user_data = {
            'email': user_tom_data['email'],
            'password': user_tom_data['password'],
        }
        res = client_for_tom.post(
            path='/signin/',
            data=login_user_data,
        )
        # ログイン後はトップページへリダイレクト
        self.assertEqual(res.status_code, 302)
        res = client_for_tom.get(path='/')
        # ログインユーザーが表示されていることを確認
        get_decoded_username = re.findall(r'user_tom', res.content.decode())
        self.assertIn('user_tom', get_decoded_username[0])

        # プロフィールページで自分の情報が見ることができることを確認
        res = client_for_tom.get(path='/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('プロフィール', res.content.decode())
        # admin限定のお知らせ投稿のリンクが表示されていない
        self.assertNotIn('/info/add/', res.content.decode())

        # アカウント名変更画面
        res = client_for_tom.get(path='/profile/edit/username/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(user_tom_data['username'], res.content.decode())
        new_username = {'username': 'Al',}
        form = EditUsernameForm(new_username)
        len_username = len(new_username['username'])
        error_msg = f'この値が少なくとも 3 文字以上であることを確認してください ({len_username} 文字になっています)。'
        self.assertEqual(form.errors['username'], [error_msg])
        self.assertEqual(res.status_code, 200)
        new_username = {'username': 'new Tom',}
        res = client_for_tom.post(
            path='/profile/edit/username/',
            data=new_username,
        )
        self.assertEqual(res.status_code, 302)
        # 更新完了画面で確認
        res = client_for_tom.get(path='/profile/edit/success/')
        self.assertIn(new_username['username'], res.content.decode())

        res = client_for_tom.get(path='/profile/')
        self.assertEqual(res.status_code, 200)

        # # email変更画面 → 廃止した
        # res = client_for_sampleuser.get(path='/profile/change/email/')
        # self.assertEqual(res.status_code, 200)

        # same_email = {'email': 'sample@examp1e.com',}
        # form = ChangeEmailForm(same_email)
        # self.assertEqual(form.errors['email'], ['既に登録されているメールアドレスです。'])

        # new_email = {'email': 'abcdefg@@eijklmn',}
        # form = ChangeEmailForm(new_email)
        # self.assertEqual(form.errors['email'], ['有効なメールアドレスを入力してください。'])
        # new_email = {'email': 'abcdefg@examp1e2.com',}
        # res = client_for_sampleuser.post(
        #     path='/profile/change/email/',
        #     data=new_email
        # )
        # self.assertEqual(res.status_code, 302)
        # # 更新完了画面で確認
        # res = client_for_sampleuser.get(path='/profile/edit/success/')
        # self.assertIn(new_email['email'], res.content.decode())

        res = client_for_tom.get(path='/profile/')
        self.assertEqual(res.status_code, 200)

        # パスワード変更画面
        # パスワードの確認が相違でNG
        res = client_for_tom.get(path='/profile/change/password/')
        self.assertEqual(res.status_code, 200)

        dict_new_password_1 = {
            'current_password': user_tom_data['password'],
            'new_password': 'tom20210908',
            'confirm_new_password': 'tom20210907',
        }
        form = ChangePasswordForm(dict_new_password_1)
        self.assertIn('上記パスワードと同様のパスワードの入力をお願いします。', res.content.decode())

        # パスワードの確認が相違でNG
        dict_new_password_2 = {
            'current_password': user_tom_data['password'],
            'new_password': 'tom_is_fine20220425',
            'confirm_new_password': 'tom_is_fine2022042520220425',
        }
        form = ChangePasswordForm(dict_new_password_2)
        res = client_for_tom.post(
            path='/profile/change/password/',
            data=dict_new_password_2
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(form.is_valid())
        self.assertIn('メールアカウントをパスワードの一部として使用することはできません。', res.content.decode())

        # OK
        new_password_dict = {
            'current_password': user_tom_data['password'],
            'new_password': 'tom20210908',
            'confirm_new_password': 'tom20210908',
        }
        res = client_for_tom.post(
            path='/profile/change/password/',
            data=new_password_dict
        )
        self.assertEqual(res.status_code, 302)
        # 更新完了画面で確認
        res = client_for_tom.get(path='/profile/edit/success/')
        self.assertIn(new_username['username'], res.content.decode())
        # self.assertIn(new_email['email'], res.content.decode())

        # 初級コース登録
        # res = client_for_tom.get(path='/pay/jrfoodadv/')
        # self.assertEqual(res.status_code, 200)

        # コース登録
        # expired_atは仮で+30とおく
        dt_now = datetime.datetime.now()
        tomorrow = dt_now + datetime.timedelta(days=+30)
        dt_now = make_aware(dt_now)
        tomorrow = make_aware(tomorrow)

        user_id = latest_user[0].id
        user_course = UserCourse.objects.get(user_id=user_id)
        user_course.payment_course = PaymentCourse.JRFOODADV
        user_course.paid_at = dt_now
        user_course.expired_at = tomorrow
        user_course.save()

        # 登録成功
        res = client_for_tom.get(path='/pay/success')
        self.assertEqual(res.status_code, 200)

        # 退会
        res = client_for_tom.get(path='/setting/withdrawal/')
        self.assertEqual(res.status_code, 200)
        login_user_data = {
            'email': user_tom_data['email'],
            'password': new_password_dict['new_password']
        }
        res = client_for_tom.post(
            path='/setting/withdrawal/',
            data=login_user_data,
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, '【フードイグザム】退会手続きが完了しました')
        self.assertIn('お客様のアカウントの退会手続きが完了しました。', mail.outbox[1].body, )
        self.assertEqual(mail.outbox[1].to[0], login_user_data['email'])

        res = client_for_tom.get(path='/profile/del/success')
        self.assertEqual(res.status_code, 200)
        self.assertIn('アカウントの削除が完了しました。', res.content.decode())

        # 退会したのでログインできない
        res = client_for_tom.get(path='/signin/')
        self.assertEqual(res.status_code, 200)
        res = client_for_tom.post(
            path='/signin/',
            data=login_user_data,
        )
        form = SigninForm(login_user_data)
        self.assertFalse(form.is_valid())


    def tearDown(self):
        """データベースの掃除
        """
        User.objects.all().delete()
        UserCourse.objects.all().delete()
        Information.objects.all().delete()
