"""
全体テスト
python manage.py test utils.tests
クラス単位のテスト 例
python manage.py test utils.tests.ValidatorTests
"""

from django.test import TestCase

import utils.validator as validator

class ValidatorTests(TestCase):
    """validator.pyに定義されている関数のテスト
    """
    def setUp(self):
        pass

    def test_validate_password_with_email(self):
        """emailのusernameと同じ文字列を含むpasswordの場合は不可
        """
        # 正常系
        self.assertTrue(validator.validate_password_with_email(
            password='XYZ#!"#¥123', email='abcd@example.com'))
        # usernameが1文字OK
        self.assertTrue(validator.validate_password_with_email(
            password='abcd#EFGH', email='a@example.com'))
        # ユーザー名と同じ文字列を含むパスワードを登録NG
        self.assertFalse(validator.validate_password_with_email(
            password='XYZabc#DEFG', email='abc@example.com'))
        # emailがintの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password='XYZ#ABC', email=123)
        # passwordがintの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password=12345, email='abcd@example.com')
        # passwordがNoneの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password=None, email='abcd@example.com')
        # emailがNoneの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password='abcd#EFGH', email=None)
        # passwordが空文字の時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password='', email='abcd@example.com')
        # emailが空文字の時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password_with_email(
                password='abcd@EFG', email='')


    def test_validate_password1_and_password2(self):
        """password1とpassword2がequalでなければNG。
        """
        # 正常系
        self.assertTrue(validator.validate_password1_and_password2(
            password1='abcDEF!', password2='abcDEF!'))
        # not equal
        self.assertFalse(validator.validate_password1_and_password2(
            password1='abcDEF!', password2='ABCdef!'))
        # passpword1がintの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password1_and_password2(
                password1=12345, password2='abcDEF!'
            )
        # passpword2がintの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password1_and_password2(
                password1='abcDEF!', password2=12345
            )
        # passpword1がNoneの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password1_and_password2(
                password1=None, password2='abcDEF!'
            )
        # passpword2がNoneの時ValueError
        with self.assertRaises(ValueError):
            validator.validate_password1_and_password2(
                password1='abcDEF!', password2=None
            )


    def test_validate_emoji(self):
        """emojiが含まれていればNG。
        """
        SUSHI_EMOJI = '🍣'
        THINK_EMOJI = '🤔'
        # アルファベットOK
        self.assertTrue(validator.validate_emoji(text='ABCDE'))
        # ランダム英数字記号OK
        random_alphanumerical_symbol = 'randombwV5Agcu9NhU%yAh$AW_k3y#-GV" ~|Dxi- j7dfkSS@ :*kyg5UEaV8WnDgji_5znLyGyxP9tRZgBxaK7VzGdUTurwcWLte9P3_Fxj7TLtUYMhn4wN_ngK_5yCUP_bgRDwwJWkeJ'
        self.assertTrue(validator.validate_emoji(text=random_alphanumerical_symbol))
        # 日本語OK
        self.assertTrue(validator.validate_emoji(text='こんにちは'))
        # 漢字OK
        self.assertTrue(validator.validate_emoji(text='本日ハ晴天ナリ'))
        description = '食品業界資格支援のフードイグザムは、食品表示検定初級をはじめとした食品業界の資格合格を目指す人を応援するeラーニングのwebアプリです。ユーザー登録をするとwebアプリで問題集が利用できるようになります。食品業界で習得が求められる、食品表示検定の初級や各種資格をeラーニングのwebアプリで簡単に学べることができます。'
        self.assertTrue(validator.validate_emoji(text=description))

        # # 絵文字が含まれているのでNG
        self.assertFalse(validator.validate_emoji(text=f'ABC{SUSHI_EMOJI}DE!!'))
        self.assertFalse(validator.validate_emoji(text=f'ABCDE!!{THINK_EMOJI}'))
        # 絵文字が1文字だけはNG
        self.assertFalse(validator.validate_emoji(text=f'{SUSHI_EMOJI}'))
        self.assertFalse(validator.validate_emoji(text=f'{THINK_EMOJI}'))
        # 絵文字が10だけもNG
        emoji_10 = SUSHI_EMOJI*10
        self.assertFalse(validator.validate_emoji(text=f'{emoji_10}'))
        emoji_10 = THINK_EMOJI*10
        self.assertFalse(validator.validate_emoji(text=f'{emoji_10}'))
