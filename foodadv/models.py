"""
foodadv（中級）のmodels
"""
import hashlib

from datetime import datetime

from django.db import models


class AnswerResult():
    """解答結果
    """
    WAITING = 0
    UNANSWERED = 1
    INCORRECT = 2
    CORRECT = 3
    ANSWER_RESULT_CHOICES = (
        (WAITING, '未実施'),
        (UNANSWERED, '未解答'),
        (INCORRECT, '不正解'),
        (CORRECT, '正解'),
    )
    _ANSWER_RESULT_DICT = dict(ANSWER_RESULT_CHOICES)

    @classmethod
    def answer_result_as_str(cls, answer_result:int) -> str:
        """引数に数字を与えて文字列で返すクラス
        """
        ret = cls._ANSWER_RESULT_DICT.get(answer_result)
        if not ret:
            raise ValueError(f'unknown answer_result{answer_result}')
        if answer_result == AnswerResult.WAITING:
            return cls.ANSWER_RESULT_CHOICES[0][1]
        elif answer_result == AnswerResult.UNANSWERED:
            return cls.ANSWER_RESULT_CHOICES[1][1]
        elif answer_result == AnswerResult.INCORRECT:
            return cls.ANSWER_RESULT_CHOICES[2][1]
        elif answer_result == AnswerResult.CORRECT:
            return cls.ANSWER_RESULT_CHOICES[3][1]
        else:
            raise RuntimeError('invalid')


class FoodadvRecord(models.Model):
    """問題の解答記録
    """
    # 基本はFoodLabelingAdviseQuestionのquestion_idで1対1
    question_id = models.CharField(
        verbose_name='question_id',
        max_length=7,
        null=False,
    )
    # 基は内部のuser_idで1対1
    user_id = models.IntegerField(
        verbose_name='user_id',
        null=False,
    )
    # お気に入り
    favorite = models.BooleanField(
        verbose_name='favorite',
        default=False,
    )
    # 後でやる
    later = models.BooleanField(
        verbose_name='later',
        default=False,
    )
    # メモ
    memo = models.CharField(
        verbose_name='memo',
        max_length=512,
        null=True,
        blank=True,
        default='',
    )
    current_answer = models.IntegerField(
        verbose_name='current_answer',
        null=False,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    def current_answer_as_str(self:int) -> str:
        """数字を文字列で返す"""
        current_answer_as_str = AnswerResult.answer_result_as_str(self.current_answer)
        return current_answer_as_str
    current_choice = models.CharField(
        verbose_name='current_choice',
        max_length=126,
        null=True,
        blank=True,
    )
    first_answer = models.IntegerField(
        verbose_name='first_answer',
        null=True,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    second_answer = models.IntegerField(
        verbose_name='second_answer',
        null=True,
        blank=True,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    third_answer = models.IntegerField(
        verbose_name='third_answer',
        null=True,
        blank=True,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    fourth_answer = models.IntegerField(
        verbose_name='fourth_answer',
        null=True,
        blank=True,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    fifth_answer = models.IntegerField(
        verbose_name='fifth_answer',
        null=True,
        blank=True,
        choices=AnswerResult.ANSWER_RESULT_CHOICES,
        default=0,
    )
    # お気に入りとメモを除く解答時にupdateされる
    saved_at = models.DateTimeField(
        verbose_name='saved_at',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name='created_at',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='updated_at',
        auto_now=True,
    )
    def __str__(self):
        return f'user_id: {self.user_id}, question_id: {self.question_id}'
    # indexを張る
    # indexes = [ models.Index(fields=['user_id'], name='idx_user_id')]
    # とnameでindex名を命名できるが、nameを書かないとsqlmigrateで自動的に命名してくれるのでそうする
    class Meta:
        db_table = 'foodadv_record'
        indexes = [
            models.Index(fields=['user_id'])
        ]


def _create_hash_id():
    """問題のPK自動生成
    現状はcsvから直接データを入力するのでこの関数は仮置き
    ・7桁
    ・先頭文字が初級なのでj
    ・英数字含む
    """
    pre_hash_name = '%s' % (datetime.now())
    long_hs_name = '%s' % (hashlib.md5(pre_hash_name.encode()).hexdigest())
    created_id = '%s%s' % ('j', str(long_hs_name)[-6:])
    return created_id


class TextbookChapter():
    """教科書の章
    """
    LAW_SYSTEM = 1
    FRESH_FOOD = 2
    PROCESSED_FOOD = 3
    LABEL_EXAMPLE = 4
    INDIVIDUAL_COMMENTARY = 5
    NUTRITION_LABEL = 6
    TEXTBOOK_CHAPTER_CHOICES = (
        (LAW_SYSTEM, '食品表示を規定している法の体系'),
        (FRESH_FOOD, '生鮮食品の表示'),
        (PROCESSED_FOOD, '加工食品の表示'),
        (LABEL_EXAMPLE, '事例でわかる食品表示'),
        (INDIVIDUAL_COMMENTARY, '表示の個別解説'),
        (NUTRITION_LABEL, '栄養成分表示の解説'),
    )
    _TEXTBOOK_CHAPTER_DICT = dict(TEXTBOOK_CHAPTER_CHOICES)

    @classmethod
    def textbook_chapter_as_str(cls, textbook_chapter:int) -> str:
        """引数に数字を与えて文字列で返すクラス
        """
        ret = cls._TEXTBOOK_CHAPTER_DICT.get(textbook_chapter)
        if not ret:
            raise ValueError(f'unknown textbook_chapter{textbook_chapter}')
        elif textbook_chapter == TextbookChapter.LAW_SYSTEM:
            return cls.TEXTBOOK_CHAPTER_CHOICES[0][1]
        elif textbook_chapter == TextbookChapter.FRESH_FOOD:
            return cls.TEXTBOOK_CHAPTER_CHOICES[1][1]
        elif textbook_chapter == TextbookChapter.PROCESSED_FOOD:
            return cls.TEXTBOOK_CHAPTER_CHOICES[2][1]
        elif textbook_chapter == TextbookChapter.LABEL_EXAMPLE:
            return cls.TEXTBOOK_CHAPTER_CHOICES[3][1]
        elif textbook_chapter == TextbookChapter.INDIVIDUAL_COMMENTARY:
            return cls.TEXTBOOK_CHAPTER_CHOICES[4][1]
        elif textbook_chapter == TextbookChapter.NUTRITION_LABEL:
            return cls.TEXTBOOK_CHAPTER_CHOICES[5][1]
        else:
            raise RuntimeError('invalid')


class FoodLabelingAdviseQuestion(models.Model):
    """問題
    """
    class Meta:
        db_table = 'food_labeling_advise_question'
    # 問題番号
    question_id = models.CharField(
        verbose_name='question_id',
        max_length=7,
        default=_create_hash_id,
        primary_key=True,
    )
    # 元データ->表には表示させずに内部的に管理。
    original_data = models.CharField(
        verbose_name='original_data',
        max_length=126
    )
    original_data_num = models.IntegerField(
        verbose_name='original_data_num',
        null=False,
    )
    # 認定テキストの章
    textbook_chapter = models.IntegerField(
        verbose_name='textbook_chapter',
        null=False,
        choices=TextbookChapter.TEXTBOOK_CHAPTER_CHOICES,
    )
    def textbook_chapter_as_str(self:int) -> str:
        """数値を文字列で返す"""
        textbook_chapter_as_str = TextbookChapter.textbook_chapter_as_str(self.textbook_chapter)
        return textbook_chapter_as_str
    # 問題文
    question_title = models.CharField(
        verbose_name='question_title',
        max_length=255,
        null=False,
    )
    # 補足問題文
    sub_question_title = models.CharField(
        verbose_name='sub_question_title',
        max_length=255,
        blank=True,
        null=True,
    )
    # 問題の型 surround, label, img
    question_type = models.CharField(
        verbose_name='question_type',
        max_length=32,
        blank=True,
        null=True,
    )
    # 画像の問題
    question_img = models.ImageField(
        verbose_name='question_img',
        upload_to='foodadv_img/',
        blank=True,
        null=True,
    )
    # 選択肢a
    choice_a = models.CharField(
        verbose_name='choice_a',
        max_length=126,
        null=True,
    )
    # 選択肢b
    choice_b = models.CharField(
        verbose_name='choice_b',
        max_length=126,
        null=True,
    )
    # 選択肢c
    choice_c = models.CharField(
        verbose_name='choice_c',
        max_length=126,
        null=True,
    )
    # 選択肢d
    choice_d = models.CharField(
        verbose_name='choice_d',
        max_length=126,
        null=True,
        blank=True,
    )
    # choice_aからchoice_dの中から選択される
    correct_answer = models.CharField(
        verbose_name='correct_answer',
        max_length=10,
        null=False,
    )
    # 解説
    commentary = models.CharField(
        verbose_name='commentary',
        max_length=512,
        null=False,
    )
    created_at = models.DateTimeField(
        verbose_name='created_at',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='updated_at',
        auto_now=True,
    )
    def __str__(self):
        return f'{self.question_id}'

    @classmethod
    def count_foodadv_questions(cls):
        """ 問題総数をカウントして返す
            return: int
        """
        return cls.objects.count()


class FoodadvTimeLeft(models.Model):
    """タイマー残り時間"""
    user_id = models.IntegerField(
        verbose_name='user_id',
        primary_key=True,
    )
    time_left_at = models.DateTimeField(
        verbose_name='time_left_at',
        null=False,
    )
    created_at = models.DateTimeField(
        verbose_name='created_at',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='updated_at',
        auto_now=True,
    )
    def __str__(self):
        return f'user_id: {self.user_id}, time_left_at: {self.time_left_at}'
    # indexを張る
    # indexes = [ models.Index(fields=['user_id'], name='idx_user_id')]
    # とnameでindex名を命名できるが、nameを書かないとsqlmigrateで自動的に命名してくれるのでそうする
    class Meta:
        db_table = 'foodadv_timeleft'
        indexes = [
            models.Index(fields=['user_id'])
        ]
