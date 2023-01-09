"""
test_forms.pyの全体テスト
% python manage.py test corporate.tests.test_forms

test_forms.pyのユニットテスト
% python manage.py test corporate.tests.test_forms.SigninFormTests.test_correct_form
"""

from django.conf import settings
from django.core import mail

from django.test import TestCase
from django.contrib.auth import get_user_model

from corporate.forms import SigninForm, SignUpForm, InfoAdminForm, InquiryAddForm, TestimonialsForm

from corporate.models import Category, Release

User = get_user_model()


class SigninFormTests(TestCase):
    """ログインフォーム
    """
    def test_correct_form(self):
        """正しいユーザーデータはフォームをきちんと通過する
        """
        User.objects.create_user(
            username='Keybon',
            email='keybon@example.com',
            password='keybon20210526',
        )
        user_data = {
            'email': 'keybon@example.com',
            'password': 'keybon20210526',
        }
        form = SigninForm(user_data)
        self.assertTrue(form.is_valid())

    def test_no_user_cant_login_form(self):
        """ユーザーデータがないのにログインはできない
        エラーメッセージも確認できる
        """
        user_data = {
            'email': 'keybon@example.com',
            'password': 'keybon20210526',
        }
        form = SigninForm(user_data)
        self.assertFalse(form.is_valid())

    def test_incorrect_form(self):
        """間違ったパスワードではフォームを通過できない
        """
        User.objects.create_user(
            username='Keybon',
            email='keybon@example.com',
            password='keybon20210526',
        )
        user_data = {
            'email': 'keybon@example.com',
            'password': '20210526keybon',
        }
        form = SigninForm(user_data)
        self.assertEqual(form.errors['password'], ['メールアドレスかパスワードが間違っています。'])
        self.assertFalse(form.is_valid())


class SignUpFormTests(TestCase):
    """新規ユーザー登録フォームのテスト
    """
    def test_correct_form(self):
        """正しいユーザーデータはフォームをきちんと通過する
        """
        user_data = {
            'username': 'Jackson',
            'email': 'jack@examp1e.com',
            'password1': 'foodexam20210526',
            'password2': 'foodexam20210526',
        }
        form = SignUpForm(user_data)
        self.assertTrue(form.is_valid())

    def test_incorrect_username_form(self):
        """長すぎる名前にはバリデーションがかかる
        """
        user_data = {
            'username': 'i'*17,
            'email': 'jack@examp1e.com',
            'password': 'aaa@ABC',
            'confirm_password': 'aaa@ABC',
        }
        form = SignUpForm(user_data)
        self.assertFalse(form.is_valid())

    def test_not_match_password_form(self):
        """パスワードが不一致だと有効ではない
        """
        user_data = {
            'username': 'Jackson',
            'email': 'jack@examp1e.com',
            'password1': 'foodexam20210526',
            'password2': 'foodtech20210526',
        }
        form = SignUpForm(user_data)
        self.assertEqual(form.errors['password2'], ['確認用パスワードが一致しません。'])
        self.assertFalse(form.is_valid())

    def test_validate_password_with_email(self):
        """メールアカウントをパスワードの一部として使用することはできない
        """
        user_data = {
            'username': 'Jackson',
            'email': 'jack@examp1e.com',
            'password1': 'jack20210526',
            'password2': 'jack20210526',
        }
        form = SignUpForm(user_data)
        self.assertEqual(form.errors['password1'], ['メールアカウントをパスワードの一部として使用することはできません。'])
        self.assertFalse(form.is_valid())

    def test_validate_username_emoji(self):
        """usernameに絵文字は使えない
        """
        user_data = {
            'username': '🐱よろしくお願いします🙇‍♂️',
            'email': 'jeff@examp1e.com',
            'password1': 'jack20210526',
            'password2': 'jack20210526',
        }
        form = SignUpForm(user_data)
        self.assertEqual(form.errors['username'], ['絵文字を使用しないでください。'])
        self.assertFalse(form.is_valid())


class InfoAdminFormTests(TestCase):
    """adminのお知らせ投稿フォームのテスト
    """
    def test_correct_info_admin_form(self):
        """正しいユーザーデータはフォームをきちんと通過する
        """
        info_data = {
            'category': Category.NEWS,
            'title': 'test title',
            'eyecatch': '',
            'description': 'test description',
            'meta_description': 'test meta description',
            'contributor': 0, # admin
            'release': Release.DRAFT,
        }
        # TODO: eyecatchのpath設定する必要ある
        # form = InfoAdminForm(info_data)
        # self.assertTrue(form.is_valid())

    def test_invalid_category_form(self):
        """存在しないcategory（番号）はNG
        """
        invalid_category = 100
        info_data = {
            'category': invalid_category,
            'title': 'test title',
            'description': 'test description',
            'contributor': 0, # admin
            'release': Release.PUBLIC,
        }
        form = InfoAdminForm(info_data)
        self.assertEqual(
            form.errors['category'],
            [f'正しく選択してください。 {invalid_category} は候補にありません。'])
        self.assertFalse(form.is_valid())

    def test_invalid_too_long_title_form(self):
        """長すぎるtitleはNG
        """
        too_long_title = 'a'*10000
        info_data = {
            'category': Category.PRESENT,
            'title': too_long_title,
            'description': 'test description',
            'contributor': 0, # admin
            'release': Release.DRAFT,
        }
        form = InfoAdminForm(info_data)
        len_too_long_title = len(too_long_title)
        self.assertEqual(
            form.errors['title'],
            [f'この値は 255 文字以下でなければなりません( {len_too_long_title} 文字になっています)。'])
        self.assertFalse(form.is_valid())

    def test_invalid_too_long_description_form(self):
        """長すぎるdescriptionはNG
        """
        too_long_description = 'a'*10000
        info_data = {
            'category': Category.PRESENT,
            'title': 'test title',
            'description': too_long_description,
            'contributor': 0, # admin
            'release': Release.PUBLIC,
        }
        form = InfoAdminForm(info_data)
        len_too_long_description = len(too_long_description)
        self.assertEqual(
            form.errors['description'],
            [f'この値は 8192 文字以下でなければなりません( {len_too_long_description} 文字になっています)。'])
        self.assertFalse(form.is_valid())

    def test_invalid_release_form(self):
        """存在しないrelease（番号）はNG
        """
        invalid_num = 100
        info_data = {
            'category': Category.COLUMN,
            'title': 'test title',
            'description': 'test description',
            'contributor': 0, # admin
            'release': invalid_num,
        }
        form = InfoAdminForm(info_data)
        self.assertEqual(
            form.errors['release'],
            [f'正しく選択してください。 {invalid_num} は候補にありません。'])
        self.assertFalse(form.is_valid())


class InquiryAddFormTests(TestCase):
    """問い合わせフォームのテスト
    """
    def test_correct_form(self):
        """正しい値はフォームをきちんと通過する
        """
        inquiry_data = {
            'name': 'SampleUser',
            'email': 'sample@examp1e.com',
            'subject': '正しいメッセージの件名です。',
            'message': '正しい質問内容を本文中に記載します。',
        }
        form = InquiryAddForm(inquiry_data)
        self.assertTrue(form.is_valid())

    def test_incorrect_email(self):
        """不正なメールアドレスを入力するとエラーが起こる
        """
        inquiry_data = {
            'name': 'TestUser',
            'email': 'sample@@@example.com',
            'subject': 'incorrect message',
            'message': 'This is incorrect message',
        }
        form = InquiryAddForm(inquiry_data)
        self.assertEqual(form.errors['email'], ['有効なメールアドレスを入力してください。'])
        self.assertFalse(form.is_valid())

    def test_incorrect_message(self):
        """メッセージ文字数が多すぎるとエラーが起こる
        """
        inquiry_data = {
            'name': 'NewVisitor',
            'email': 'sample@examp1e.com',
            'subject': '件名',
            'message': 'i'*1025,
        }
        form = InquiryAddForm(inquiry_data)
        self.assertEqual(form.errors['message'], ['この値は 1024 文字以下でなければなりません( 1025 文字になっています)。'])
        self.assertFalse(form.is_valid())

    def test_send_email(self):
        """きちんとメールが送信されるかテスト
        """
        mail.send_mail(subject='Example Subject',
                        message='This is example message.',
                        from_email='tom@example.com',
                        recipient_list=[settings.EMAIL_HOST_USER])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Example Subject')
        self.assertEqual(mail.outbox[0].body, 'This is example message.')
        self.assertEqual(mail.outbox[0].from_email, 'tom@example.com')
        self.assertEqual(mail.outbox[0].to[0], settings.EMAIL_HOST_USER)


class TestimonialsFormTests(TestCase):
    """合格体験記の投稿のテスト
    """
    def test_correct_form(self):
        """正しい値はフォームをきちんと通過する
        """
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
        form = TestimonialsForm(testimonials_data)
        self.assertTrue(form.is_valid())

    def test_incorrect_course_num(self):
        """course が0の初期値のままだとfalseになる
        """
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
        form = TestimonialsForm(testimonials_data)
        # TODO: 現状初級だけなので、選択肢に0を用意していないのでこのエラーが発生する仕様。
        self.assertEqual(form.errors['payment_course'], ['正しく選択してください。 0 は候補にありません。'])
        self.assertFalse(form.is_valid())

    def test_advice_not_enough_chars(self):
        """advise が短すぎるとfalseになる
        """
        testimonials_data = {
            'exam_subject': 1,
            'course': 0,
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
            'advice': 'Lorem ipsum dolor sit amet.',
            'next_exam': '食品表示検定中級',
            'improvements': 'これからも頑張ってください!!',
        }
        form = TestimonialsForm(testimonials_data)
        len_advice = len(testimonials_data['advice'])
        self.assertEqual(form.errors['advice'],
                        [f'この値が少なくとも 50 文字以上であることを確認してください ({len_advice} 文字になっています)。'])
        self.assertFalse(form.is_valid())

    def test_not_enough_fields(self):
        """title が空文字、exam_date が空文字だとfalseになる
        """
        testimonials_data = {
            'exam_subject': 1,
            'course': 1,
            'pen_name': 'SampleUser',
            'email': 'sample@examp1e.com',
            'title': '',
            'exam_date': '',
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
            'next_exam': '',
            'improvements': '',
        }
        form = TestimonialsForm(testimonials_data)
        self.assertEqual(form.errors['title'], ['このフィールドは必須です。'])
        self.assertEqual(form.errors['exam_date'], ['このフィールドは必須です。'])
        self.assertFalse(form.is_valid())
