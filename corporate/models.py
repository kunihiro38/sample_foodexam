"""
ユーザーメインで管理のmodels
"""
import hashlib
import os

from datetime import datetime
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.dispatch import receiver

from django.db.models.signals import post_delete


class PaymentCourse():
    """支払いコース
    """
    FREE = 0
    JRFOODADV = 1
    FOODADV = 2
    PAYMENT_COURSE_CHOICES = (
        (FREE, 'プラン選択をお願いします'),
        (JRFOODADV, '初級食品表示診断士コース'),
        (FOODADV, '中級食品表示診断士コース'),
    )
    _PAYMENT_COURSE_DICT = dict(PAYMENT_COURSE_CHOICES)

    @classmethod
    def payment_course_as_str(cls, payment_course:int) -> str:
        """引数に数字を与えて文字列で返すクラス
        """
        ret = cls._PAYMENT_COURSE_DICT.get(payment_course)
        if not ret:
            raise ValueError(f'unknown payment_course:{payment_course}')
        if payment_course == PaymentCourse.FREE:
            return cls.PAYMENT_COURSE_CHOICES[0][1]
        elif payment_course == PaymentCourse.JRFOODADV:
            return cls.PAYMENT_COURSE_CHOICES[1][1]
        elif payment_course == PaymentCourse.FOODADV:
            return cls.PAYMENT_COURSE_CHOICES[2][1]
        else:
            raise RuntimeError('invalid')


class UserCourse(models.Model):
    """Userの支払いコース情報
    """
    user_id = models.IntegerField(
        verbose_name='user_id',
        primary_key=True,
    )
    # 初級コース
    payment_course = models.IntegerField(
        verbose_name='payment_course',
        null=False,
        choices=PaymentCourse.PAYMENT_COURSE_CHOICES,
        default=0,
    )
    def payment_course_as_str(self):
        """関数呼び出し
        """
        payment_course_as_str = PaymentCourse.payment_course_as_str(self.payment_course)
        return payment_course_as_str
    # 初級支払日
    paid_at = models.DateTimeField(
        verbose_name='paid_at',
        null=True,
    )
    # 初級有料会員期限切れ日
    expired_at = models.DateTimeField(
        verbose_name='expired_at',
        null=True,
    )
    # 中級コース
    foodadv_payment_course = models.IntegerField(
        verbose_name='foodadv_payment_course',
        null=False,
        choices=PaymentCourse.PAYMENT_COURSE_CHOICES,
        default=0,
    )
    def foodadv_payment_course_as_str(self):
        """関数呼び出し
        """
        foodadv_payment_course_as_str = PaymentCourse.payment_course_as_str(
                                                                self.foodadv_payment_course)
        return foodadv_payment_course_as_str
    # 中級支払日
    foodadv_paid_at = models.DateTimeField(
        verbose_name='foodadv_paid_at',
        null=True,
    )
    # 中級有料会員期限切れ日
    foodadv_expired_at = models.DateTimeField(
        verbose_name='foodadv_expired_at',
        null=True,
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
        str_payment_course = PaymentCourse.payment_course_as_str(self.payment_course)
        str_foodadv_payment_course = PaymentCourse.payment_course_as_str(self.foodadv_payment_course)
        # 有効期限切れかどうかの判定はしていない
        return f'user_id: {self.user_id}| 初級:{str_payment_course}| 中級:{str_foodadv_payment_course}' 

    @classmethod
    def get_user_course_by_id(cls, user_id):
        """ user_id から user_course を取得
            return:
        """
        if not user_id:
            return []
        return UserCourse.objects.get(user_id=user_id)


    # indexを張る
    # indexes = [ models.Index(fields=['user_id'], name='idx_user_id')]
    # とnameでindex名を命名できるが、nameを書かないとsqlmigrateで自動的に命名してくれるのでそうする
    class Meta:
        db_table = 'usercourse'
        indexes = [
            models.Index(fields=['user_id'])
        ]


class Category():
    """カテゴリー
    """
    NEWS = 1
    UPDATE = 2
    CAMPAIGN = 3
    PRESENT = 4
    CONSTRUCTION = 5
    COLUMN = 6
    CATEGORY_CHOICES = (
        (NEWS, 'ニュース'),
        (UPDATE, '更新'),
        (CAMPAIGN, 'キャンペーン'),
        (PRESENT, 'プレゼント'),
        (CONSTRUCTION, '工事'),
        (COLUMN, 'コラム'),
    )
    _CATEGORY_DICT = dict(CATEGORY_CHOICES)

    @classmethod
    def category_as_str(cls, category:int) -> str:
        """引数にintを与えてstrで返すクラス
        """
        ret = cls._CATEGORY_DICT.get(category)
        if not ret:
            raise ValueError(f'unknown category:{category}')
        if category == Category.NEWS:
            return cls.CATEGORY_CHOICES[0][1]
        elif category == Category.UPDATE:
            return cls.CATEGORY_CHOICES[1][1]
        elif category == Category.CAMPAIGN:
            return cls.CATEGORY_CHOICES[2][1]
        elif category == Category.PRESENT:
            return cls.CATEGORY_CHOICES[3][1]
        elif category == Category.CONSTRUCTION:
            return cls.CATEGORY_CHOICES[4][1]
        elif category == Category.COLUMN:
            return cls.CATEGORY_CHOICES[5][1]
        else:
            raise RuntimeError('invalid')


class Release():
    """記事の公開・非公開
    """
    DRAFT = 0
    PUBLIC = 1
    RELEASE_CHOICES = (
        (DRAFT, '下書き'),
        (PUBLIC, '公開'),
    )
    _RELEASE_DICT = dict(RELEASE_CHOICES)

    @classmethod
    def release_as_str(cls, release:int) -> str:
        """引数に数字を与えて文字列で返す
        """
        ret = cls._RELEASE_DICT.get(release)
        if not ret:
            raise ValueError(f'unknown release:{release}')

        if release == Release.DRAFT:
            return cls.RELEASE_CHOICES[0][1]
        elif release == Release.PUBLIC:
            return cls.RELEASE_CHOICES[1][1]
        else:
            raise RuntimeError('invalid')


@transaction.atomic
def _info_eyecatch_upload_to(instance, filename):
    # 既に画像があるなら削除
    if Information.objects.filter(id=instance.id).exists():
        info = Information.objects.get(id=instance.id)
        if info.eyecatch:
            # pathを削除
            os.remove(f'{settings.MEDIA_ROOT}/{info.eyecatch}')
            # 本体を削除

    if not isinstance(filename, str):
        # filenameがstring確認
        raise ValueError(f'{filename} is not string')
    current_time = datetime.now()
    pre_hash_name = f'{instance.id}{filename}{current_time}'
    extension = filename.split('.')[-1] # 拡張子取得
    hs_filename = f'{hashlib.md5(pre_hash_name.encode()).hexdigest()}.{extension}'
    saved_path = '.corporate/info/'
    return f'{saved_path}{hs_filename}'

class Information(models.Model):
    """お知らせ
    """
    category = models.IntegerField(
        verbose_name='category',
        null=True,
        choices=Category.CATEGORY_CHOICES
    )
    def category_as_str(self):
        """関数呼び出し
        """
        category_as_str = Category.category_as_str(self.category)
        return category_as_str
    title = models.CharField(
        verbose_name='title',
        max_length=255,
        null=False,
    )
    eyecatch = models.ImageField(
        verbose_name='eyecatch',
        upload_to=_info_eyecatch_upload_to,
    )
    description = models.CharField(
        verbose_name='description',
        max_length=8192,
        null=False,
    )
    meta_description = models.CharField(
        verbose_name='meta_description',
        max_length=160,
        null=True,
        blank=True,
    )
    contributor = models.IntegerField(
        verbose_name='contributor',
        null=False,
    )
    release = models.IntegerField(
        verbose_name='release',
        null=False,
        default=Release.DRAFT,
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
        str_category = Category.category_as_str(self.category)
        str_release = Release.release_as_str(self.release)
        return f'{self.id}({str_category}|{str_release}), {self.title}'

    @classmethod
    def find_informations(cls, display_cnt=18):
        """ display_cntに合わせたお知らせの一覧を取得
            default引数の18は、一覧で表示できる3の倍数で設定
            TODO:ページングが必要になった際はロジックの整理が必要
            return: list []
        """
        if display_cnt is None:
            return []
        qs = cls.objects\
                .filter(Q(release=Release.PUBLIC))\
                .exclude(Q(category=Category.COLUMN))\
                .order_by('-created_at')\
                [:display_cnt]
        informations_list = []
        for value in qs:
            informations_list.append(value)
        return informations_list

    @classmethod
    def find_columns(cls, display_cnt=18):
        """ display_cntに合わせた学習コラムの一覧を取得
            default引数の18は、一覧で表示できる3の倍数で設定
            TODO:ページングが必要になった際はロジックの整理が必要
            return: list []
        """
        if display_cnt is None:
            return []
        qs = cls.objects\
                .filter(Q(release=Release.PUBLIC)
                        & Q(category=Category.COLUMN))\
                .order_by('-created_at')\
                [:display_cnt]
        columns_list = []
        for value in qs:
            columns_list.append(value)
        return columns_list


@receiver(post_delete, sender=Information)
def delete_file(sender, instance, **kwargs):
    """ Informationオブジェクトがまるまる削除された時に
    それに紐づく media/.corporate/info/xxx.jpg のファイルを削除する
    """
    pass


class Exam():
    """"試験
    """
    JRFOODADV = 1
    FOODADV = 2
    EXAM_CHOICES = (
        (JRFOODADV, '食品表示検定・初級'),
        (FOODADV, '食品表示検定・中級'),
    )
    _EXAM_CHOICES = dict(EXAM_CHOICES)

class PaymentPlan():
    """ 支払いプラン
    """
    MONTHLY_PLAN = 1 
    TEN_DAYS_PLAN = 2
    THREE_DAYS_PLAN = 3 
    PAYMENT_PLAN_CHOICES = (
        (MONTHLY_PLAN, 'マンスリープラン'),
        (TEN_DAYS_PLAN, '10Days集中プラン'),
        (THREE_DAYS_PLAN, '3Daysお試しプラン'),
    )
    _PAYMENT_PLAN_DICT = dict(PAYMENT_PLAN_CHOICES)

    @classmethod
    def payment_plan_as_str(cls, payment_plan:int) -> str:
        """引数に数字を与えて文字列で返すクラス
        """
        ret = cls._PAYMENT_PLAN_DICT.get(payment_plan)
        if not ret:
            raise ValueError(f'unknown payment_course:{payment_plan}')
        if payment_plan == PaymentPlan.MONTHLY_PLAN:
            return cls.PAYMENT_PLAN_CHOICES[0][1]
        elif payment_plan == PaymentPlan.TEN_DAYS_PLAN:
            return cls.PAYMENT_PLAN_CHOICES[1][1]
        elif payment_plan == PaymentPlan.THREE_DAYS_PLAN:
            return cls.PAYMENT_PLAN_CHOICES[2][1]
        else:
            raise RuntimeError('invalid')

class Testimonials(models.Model):
    """合格体験記
    """
    exam_subject = models.IntegerField(
        verbose_name='exam_subject',
        blank=False,
        null=False,
        choices=Exam.EXAM_CHOICES
    )
    payment_course = models.IntegerField(
        verbose_name='payment_course',
        blank=False,
        null=False,
        choices=PaymentCourse.PAYMENT_COURSE_CHOICES,
        default=0,
    )
    def payment_course_as_str(self):
        """関数呼び出し
        """
        payment_course_as_str = PaymentCourse.payment_course_as_str(self.payment_course)
        return payment_course_as_str

    payment_plan = models.IntegerField(
        verbose_name='payment_plan',
        blank=False,
        null=False,
        choices=PaymentPlan.PAYMENT_PLAN_CHOICES,
        default=0,
    )
    def payment_plan_as_str(self):
        """関数呼び出し
        """
        payment_plan_as_str = PaymentPlan.payment_plan_as_str(self.payment_plan)
        return payment_plan_as_str

    pen_name = models.CharField(
        verbose_name='pen_name',
        max_length=64,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        verbose_name='email',
        max_length=254,
    )
    title = models.CharField(
        verbose_name='title',
        max_length=64,
        blank=False,
        null=False,
    )
    # 受験日
    exam_date = models.DateTimeField(
        verbose_name='exam_date',
        blank=False,
        null=False,
    )
    points = models.IntegerField(
        verbose_name='points',
        blank=False,
        null=False,
    )
    times = models.CharField(
        verbose_name='times',
        max_length=64,
        blank=False,
        null=False,
    )
    learning_time = models.CharField(
        verbose_name='learning_time',
        max_length=64,
        blank=False,
        null=False,
    )
    referenced_site = models.CharField(
        verbose_name='referenced_site',
        max_length=64,
        blank=True,
        null=True,
    )
    learning_method = models.CharField(
        verbose_name='learning_method',
        max_length=512,
        blank=False,
        null=False,
    )
    impression = models.CharField(
        verbose_name='impression',
        max_length=512,
        blank=False,
        null=False,
    )
    advice = models.CharField(
        verbose_name='advice',
        max_length=512,
        blank=False,
        null=False,
    )
    next_exam = models.CharField(
        verbose_name='next_exam',
        max_length=64,
        blank=True,
        null=True,
    )
    improvements = models.CharField(
        verbose_name='improvements',
        max_length=512,
        blank=True,
        null=True,
    )
    contributor = models.IntegerField(
        verbose_name='contributor',
        blank=True,
        null=True,
    )
    release = models.IntegerField(
        verbose_name='release',
        null=False,
        default=Release.DRAFT,
    )
    # 公開日
    published_at = models.DateTimeField(
        verbose_name='published_at',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        verbose_name='created_at',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='updated_at',
        auto_now=True,
    )

    @classmethod
    def find_testimonials(cls, display_cnt=18):
        """ display_cntに合わせた合格体験記の一覧を取得
            default引数の18は、一覧で表示できる3の倍数で設定
            TODO:ページングが必要になった際はロジックの整理が必要
            return: list []
        """
        if display_cnt is None:
            return []
        qs = cls.objects.filter(Q(release=Release.PUBLIC))\
                        .order_by('-published_at')\
                        [:display_cnt]

        testimonials_list = []
        for value in qs:
            testimonials_list.append(value)
        return testimonials_list
