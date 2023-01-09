"""
test_forms.pyの全体テスト
% python manage.py test foodadv.tests.test_forms

test_forms.pyのユニットテスト
% python manage.py test foodadv.tests.test_forms.SelectQuestionFormTests.test_correct_form
"""

from django.test import TestCase

from foodadv.forms import SelectQuestionForm, SelectPracticeTestForm


class SelectQuestionFormTests(TestCase):
    """食品表示検定・中級：練習モード
    """
    def test_correct_form(self):
        """正しいデータはフォームをきちんと通過する
        """
        choiced_data = {
            'target': ['1'],
            'chapter': ['1', '4'],
            'answers': 3
        }
        form = SelectQuestionForm(choiced_data)
        self.assertTrue(form.is_valid())

    def test_correct_form_second(self):
        """正しいデータはフォームをきちんと通過する
        """
        choiced_data = {
            'target': ['0', '1'],
            'chapter': ['1', '2', '3', '4', '5', '6'],
            'answers': 999 # ALL
        }
        form = SelectQuestionForm(choiced_data)
        self.assertTrue(form.is_valid())

    def test_incorrect_chapter_form(self):
        """chapterが不正なデータはフォームを通過できない
        """
        choiced_data = {
            'target': ['0', '1'],
            'chapter': ['100'],
            'answers': 1
        }
        form = SelectQuestionForm(choiced_data)
        self.assertFalse(form.is_valid())

    def test_incorrect_answers_form(self):
        """選択肢になりanswersが選択された場合はフォームを通過できない
        """
        choiced_data = {
            'target': ['0', '1'],
            'chapter': ['1', '5', '6'],
            'answers': 77
        }
        form = SelectQuestionForm(choiced_data)
        self.assertFalse(form.is_valid())


class SelectPracticeTestFormTests(TestCase):
    """食品表示検定・中級:模擬試験
    """
    def test_correct_form(self):
        """正しいデータはフォームをきちんと通過する
        """
        choiced_data = {
            'unquestioned_and_mistakes': ['0']
        }
        form = SelectPracticeTestForm(choiced_data)
        self.assertTrue(form.is_valid())

    def test_incorrect_form(self):
        """0以外のデータはフォームを通過できない
        """
        choiced_data = {
            'unquestioned_and_mistakes': ['1']
        }
        form = SelectPracticeTestForm(choiced_data)
        self.assertFalse(form.is_valid())
