"""
jrfoodadvのforms
"""
import itertools
import datetime

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from .models import JrFoodLabelingAdviseQuestion


User = get_user_model()


class DelRecordForm(forms.Form):
    """履歴削除"""
    username = forms.CharField(
        required=True,
        min_length=3,
        max_length=16,
        widget=forms.TextInput(
            attrs={
                'placeholder': ''
            }
        )
    )

    def __init__(self, user, *args, **kwargs):
        self.login_user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if str(self.login_user) != username:
            raise ValidationError('無効な値が入力されています。')
        return username


class SelectQuestions:
    """食品表示検定・初級：練習モード
    """
    # 出題対象
    UNQUESTIONED = 0
    MISS = 1

    TARGET_CHOICES = (
        (UNQUESTIONED, '未出題'),
        (MISS, 'ミス'),
    )

    # 出題分野
    LABELING_BRIDGE = 1
    FRESH_FOOD = 2
    PROCESSED_FOOD = 3
    VARIOUS_FOOD = 4
    OTHER_FOOD = 5
    THINK_FOOD = 6

    CHAPTER_CHOICES = (
        (LABELING_BRIDGE, '食品表示は消費者と事業者をつなぐ架け橋'),
        (FRESH_FOOD, '生鮮食品の表示'),
        (PROCESSED_FOOD, '加工食品の表示'),
        (VARIOUS_FOOD, 'いろいろな食品表示の例'),
        (OTHER_FOOD, 'その他の食品表示やマーク'),
        (THINK_FOOD, '私たちの食生活について考える'),
    )


class SearchRecord:
    """お気に入り・メモを検索対象に含める"""
    FAVORITE = 0
    FAVORITE_CHOICES = (
        (FAVORITE, 'しぼる'),
    )
    MEMO = 0
    MEMO_CHOICES = (
        (MEMO, 'しぼる'),
    )


class SearchQuestionForm(forms.Form):
    """問題検索"""
    question_id = forms.CharField(
        required=False,
        max_length=7,
    )
    chapter = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'chapter',
            }
        ),
        choices=SelectQuestions.CHAPTER_CHOICES
    )
    word = forms.CharField(
        required=False,
        max_length=50,
    )
    target = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'target',
            }
        ),
        choices=SelectQuestions.TARGET_CHOICES,
    )
    favorite = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(),
        choices=SearchRecord.FAVORITE_CHOICES,
    )
    memo = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(),
        choices=SearchRecord.MEMO_CHOICES,
    )

    def clean_question_id(self):
        question_id = self.cleaned_data['question_id']
        return question_id
    def clean_chapter(self):
        chapter = self.cleaned_data['chapter']
        return chapter
    def clean_word(self):
        word = self.cleaned_data['word']
        return word
    def clean_target(self):
        target = self.cleaned_data['target']
        return target
    def clean_favorite(self):
        favorite = self.cleaned_data['favorite']
        return favorite
    def clean_memo(self):
        memo = self.cleaned_data['memo']
        return memo
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class SelectQuestionForm(forms.Form):
    """分野で問題検索
    """
    target = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'target',
            }
        ),
        choices=SelectQuestions.TARGET_CHOICES 
    )
    chapter = forms.MultipleChoiceField(
        required=True,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'chapter',
            }
        ),
        choices=SelectQuestions.CHAPTER_CHOICES
    )
    answers = forms.fields.ChoiceField(
        choices = (
            (1, 1),
            (3, 3),
            (5, 5),
            (10, 10),
            (20, 20),
            (30, 30),
            (40, 40),
            (75, 75),
            (999, 'ALL')
        ),
        initial=10,
        required=True,
        widget=forms.widgets.Select(
            attrs={
                'class': 'answers',
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    def clean_target(self):
        target = self.cleaned_data['target']
        return target
    def clean_chapter(self):
        chapter = self.cleaned_data['chapter']
        return chapter
    def clean_answers(self):
        answers = self.cleaned_data['answers']
        return answers


class SelectPracticeTest:
    """食品表示検定・初級：模擬試験
    """
    # 出題対象
    UNQUESTIONED_AND_MISTAKES = 0
    UNQUESTIONED_AND_MISTAKES_CHOICES = (
        (UNQUESTIONED_AND_MISTAKES, 'ランダムではなく、未出題・ミスの優先順で出題'),
    )

class SelectPracticeTestForm(forms.Form):
    """ランダムではなく、未出題・ミスの優先順で出題
    """
    unquestioned_and_mistakes = forms.MultipleChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'random',
            }
        ),
        choices=SelectPracticeTest.UNQUESTIONED_AND_MISTAKES_CHOICES 
    )
    def clean_unquestioned_and_mistakes(self):
        unquestioned_and_mistakes = self.cleaned_data['unquestioned_and_mistakes']
        return unquestioned_and_mistakes

class GetPageNumForm(forms.Form):
    """Getでページ番号の取得
    -> ページングで使用
    """
    page = forms.IntegerField(
        required=False,
    )
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_page(self):
        page = self.cleaned_data['page']
        if page is None:
            page = 1
        return page


def _make_choice_combination(choices):
    """問題の並び一辺倒(choice_a→choice_d)を防ぐために日によってパターンを替える
    基本的には選択肢4つからと、選択肢3つからの2パターン
    選択肢4つのパターンは、4*3*2=24通り
    選択肢3つのパターンは、3*2=6通り
    実施日から全パターン(24or6)を割った「商」が問題番号になるようにする
    """
    # 24か6を判定
    all_combinations_counts = len(list(itertools.permutations(choices)))

    all_combinations = []
    # 全ての問題の組み合わせを作成する
    for choice in itertools.permutations(choices, len(choices)):
        all_combinations.append(choice)

    # 一応逆順にしておく
    all_combinations.reverse()

    # 本日の日付取得
    dt_now = datetime.datetime.now()
    dt_now_day = dt_now.day

    # all_combinations_countsは24通りか6通りしかない
    if all_combinations_counts == 24:
        # 24は4つの組み合わせの全通り(4*3*2)
        # choice_numは商
        choice_num = dt_now_day % all_combinations_counts

    elif all_combinations_counts == 6:
        # 6は3つの組み合わせの全通り(3*2)
        # choice_numは商
        choice_num = dt_now_day % all_combinations_counts

    return all_combinations[choice_num]


class SelectAnswerForm(forms.Form):
    """練習モードの解答選択画面
    """
    select_answer = forms.ChoiceField(
        required = False,
        widget=forms.RadioSelect(),
    )

    def __init__(self, question_id, param):
        """ choicesをquestion_idからqsを使って作成する
        """
        self.question_id = question_id
        # question_idの不正をチェック
        try:
            qs = JrFoodLabelingAdviseQuestion.objects.get(question_id=self.question_id)
        except JrFoodLabelingAdviseQuestion.DoesNotExist:
            raise RuntimeError("invalid")

        # MultipleChoiceFieldのchoiceに該当する箇所の初期値作成
        forms.Form.__init__(self, param)
        qs = JrFoodLabelingAdviseQuestion.objects.get(question_id=self.question_id)
        choices = []
        choices.append(('choice_a', qs.choice_a))
        choices.append(('choice_b', qs.choice_b))
        choices.append(('choice_c', qs.choice_c))
        # choice_dは問題によって存在しないものがあるので存在しなければlistに追加しない
        if qs.choice_d:
            choices.append(('choice_d', qs.choice_d))

        choices_daily = _make_choice_combination(choices)

        self.fields['select_answer'].choices = choices_daily

    def clean_select_answer(self):
        """choice_a, choice_b, choice_c, choice_d以外のpostのバリデーションエラーは不要
        ChoiceFieldがchoices以外は自動的にバリデーションエラーを排出してくれる。
        """
        select_answer = self.cleaned_data['select_answer']
        return select_answer
