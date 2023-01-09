"""
forms
"""
from utils import validator
from common.messages import FormMessages

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.admin.widgets import AdminDateWidget

from .models import Category, Information, Release, PaymentCourse, PaymentPlan

User = get_user_model()

class SigninForm(forms.Form):
    """ログインフォーム
    """
    email = forms.EmailField(
        required=True,
        max_length=255,
        min_length=3,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'your-email@example.com',
            }
        )
    )
    password = forms.CharField(
        required=True,
        max_length=255,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '******',
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        return password

    def cleaned_username(self):
        username = self.cleaned_data['username']
        return username

    def clean(self):
        cleaned_data = super(SigninForm, self).clean()
        if 'email' and 'password' in cleaned_data:
            # authenticateメソッドは(username, password)をとるので
            # メールアドレス認証を実行するために以下のコードになる
            try:
                user = User.objects.get(email=cleaned_data['email'])
            except:
                raise ValidationError(FormMessages.WRONG_EMAIL_OR_PASSWORD)
            auth_result = authenticate(
                username=str(user),
                password = self.cleaned_data.get('password')
            )
            if not auth_result:
                self.add_error(
                    field='password',
                    error=ValidationError(FormMessages.WRONG_EMAIL_OR_PASSWORD)
                )
            # cleaned_dataに追加
            cleaned_data['username'] = str(user)
            return cleaned_data


class SignUpForm(UserCreationForm):
    """ユーザー登録用フォーム"""
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        """username"""
        username = self.cleaned_data['username']
        forbidden_username_list = ['admin']
        for forbidden_username in forbidden_username_list:
            if forbidden_username in username:
                raise ValidationError(FormMessages.CANT_SIGNUP_USERNAME)

        if not validator.validate_emoji(username):
            raise ValidationError(FormMessages.CANT_USE_EMOJI)

        return username

    def clean_email(self):
        """email"""
        email = self.cleaned_data['email']
        if not email:
            raise ValidationError('このフィールドを入力してください。')
        if User.objects.filter(email=email, is_active=True):
            raise ValidationError(FormMessages.ALREADY_EXISTS)
        # 仮登録のメールは送信したけど、本登録していない時

        forbidden_emails = ['example.', 'sample.', 'test.', 'invalid.']
        for forbidden_email in forbidden_emails:
            if forbidden_email in email:
                raise ValidationError(FormMessages.CANT_SIGNUP_EMAIL)
        return email
    def clean_password1(self):
        """password1"""
        password1 = self.cleaned_data['password1']
        return password1

    def clean_password2(self):
        """password2"""
        password2 = self.cleaned_data['password2']
        return password2

    def clean(self):
        cleaned_data = super().clean()
        email = self.cleaned_data.get('email')
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        # ユーザー名と同じ文字列を含むパスワードの登録不可
        if password1 and email:
            if not validator.validate_password_with_email(password=password1, email=email):
                self.add_error(
                    field='password1',
                    error=FormMessages.INVALID_PASSWORD_WITH_EMAIL)

        # password1と確認用のpassword2が一致しなければNG
        # django2.2->3.0にバージョンアップした際にエラーメッセージが英語になったので以下を作成
        if password1 and password2:
            if not validator.validate_password1_and_password2(password1=password1,
                                                                password2=password2):
                self.add_error(
                    field='password2',
                    error=FormMessages.NOT_EQUAL_PASSWD1_AND_PASSWD2)
        return cleaned_data

class CustomPasswordResetForm(PasswordResetForm):
    """パスワードを忘れた時のフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        find_user = User.objects.filter(email=email)
        if not find_user:
            raise ValidationError('入力されたメールアドレスは登録されていません。')
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """パスワード再設定用フォーム(パスワード忘れて再設定)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class WithdrawalForm(forms.Form):
    """退会処理"""
    email = forms.EmailField(
        required=True,
        max_length=255,
        min_length=3,
        widget=forms.EmailInput(),
    )
    password = forms.CharField(
        required=True,
        max_length=255,
        min_length=6,
        widget=forms.PasswordInput(),
    )

    def __init__(self, user_id, *args, **kwargs):
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        return password

    def clean(self):
        cleaned_data = super().clean()
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        user = User.objects.get(id=self.user_id)
        if user.email != email:
            self.add_error(
                field='email',
                error=ValidationError('無効な値が入力されています。'))

        auth_result = authenticate(
            username = user.username,
            password = password,
        )
        if not auth_result:
            self.add_error(
                field='password',
                error=ValidationError(FormMessages.INCORRECT_PASSWORD))
        return cleaned_data


class EditUsernameForm(forms.Form):
    """アカウント名編集"""
    username = forms.CharField(
        required=True,
        min_length=3,
        max_length=16,
    )
    def clean_username(self):
        """2つ判定
        ・adminという名前の使用不可
        ・絵文字の使用不可
        """
        username = self.cleaned_data['username']
        forbidden_username_list = ['admin']
        for forbidden_username in forbidden_username_list:
            if forbidden_username in username:
                raise ValidationError(FormMessages.CANT_SIGNUP_USERNAME)

        if not validator.validate_emoji(username):
            raise ValidationError(FormMessages.CANT_USE_EMOJI)

        return username


class ChangeEmailForm(forms.Form):
    """メールアドレス変更"""
    email = forms.EmailField(
        required=True,
        max_length=255,
        min_length=3,
        widget=forms.EmailInput(),
    )
    def clean_email(self):
        """validation"""
        email = self.cleaned_data['email']
        forbidden_emails = ['example.', 'sample.', 'test.', 'invalid.']
        for forbidden_email in forbidden_emails:
            if forbidden_email in email:
                raise ValidationError(FormMessages.CANT_SIGNUP_EMAIL)
        if User.objects.filter(email=email):
            raise ValidationError(FormMessages.ALREADY_EXISTS)

        return email


class ChangePasswordForm(forms.Form):
    """パスワード変更"""
    current_password = forms.CharField(
        required=True,
        max_length=255,
        min_length=6,
        widget=forms.PasswordInput(),
    )
    new_password = forms.CharField(
        required=True,
        max_length=255,
        min_length=8,
        widget=forms.PasswordInput(),
    )
    confirm_new_password = forms.CharField(
        required=True,
        max_length=255,
        min_length=8,
        widget=forms.PasswordInput(),
    )
    def __init__(self, user_id, *args, **kwargs):
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """password"""
        current_password = self.cleaned_data['current_password']
        user = User.objects.get(id=self.user_id)
        if user.username and current_password:
            auth_result = authenticate(
                username = user.username,
                password=current_password,
            )
            if not auth_result:
                raise ValidationError(FormMessages.INCORRECT_PASSWORD)
        return current_password

    def clean_new_password(self):
        """new password"""
        new_password = self.cleaned_data['new_password']
        return new_password

    def clean_confirm_new_password(self):
        """confirm new password"""
        confirm_new_password = self.cleaned_data['confirm_new_password']
        return confirm_new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = self.cleaned_data.get('new_password')
        confirm_new_password = self.cleaned_data.get('confirm_new_password')
        email = User.objects.get(id=self.user_id).email

        # ユーザー名と同じ文字列を含むパスワードの登録不可
        if new_password and email:
            if not validator.validate_password_with_email(password=new_password, email=email):
                self.add_error(
                    field='new_password',
                    error=FormMessages.INVALID_PASSWORD_WITH_EMAIL)

        # password1と確認用のpassword2が一致しなければNG
        if new_password and confirm_new_password:
            if not validator.validate_password1_and_password2(password1=new_password,
                                                                password2=confirm_new_password):
                self.add_error(
                    field='confirm_new_password',
                    error=FormMessages.NOT_EQUAL_PASSWD1_AND_PASSWD2)

        return cleaned_data


class InfoAdminForm(forms.ModelForm):
    """Django 管理サイト専用のフォーム
    """
    class Meta:
        model = Information
        fields = ['category',
                'title',
                'description',
                'meta_description',
                'contributor',
                'release',
                ]

    category = forms.ChoiceField(
        required=False,
        disabled=False,
        initial=[],
        # widget=forms.CheckboxSelectMultiple(),
        widget=forms.RadioSelect(),
        choices=Category.CATEGORY_CHOICES,
    )
    title = forms.CharField(
        required=True,
        max_length=255,
        widget=forms.Textarea(
            attrs={
                'placeholder': '255文字以内で入力してください。',
                'rows': 0,
                'cols': 120,
            }
        )
    )
    eyecatch = forms.ImageField(
        required=True,
        widget=forms.FileInput(
            attrs={
                'class': '',
            }
        )
    )
    description = forms.CharField(
        required=True,
        max_length=8192,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を8,192文字以内で入力してください。',
                'rows': 40,
                'cols': 120,
            }
        )
    )
    meta_description = forms.CharField(
        required=False,
        max_length=160,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を160文字以内で入力してください。',
                'cols': 60,
            }
        )
    )
    release = forms.ChoiceField(
        required=False,
        disabled=False,
        initial=[],
        widget=forms.RadioSelect(),
        choices=Release.RELEASE_CHOICES,
    )


class InquiryAddForm(forms.Form):
    """お問い合わせフォーム
    """
    name = forms.CharField(
        required=True,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                'placeholder': '氏名',
            }
        )
    )
    email = forms.EmailField(
        required=True,
        max_length=255,
        min_length=3,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'your-email@example.com',
            }
        )
    )
    subject = forms.CharField(
        required=True,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                'placeholder': '件名',
            }
        )
    )
    message = forms.CharField(
        required=True,
        max_length=1024,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を1,000文字以内で入力してください。',
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name']
        return name

    def clean_email(self):
        email = self.cleaned_data['email']
        return email

    def clean_subject(self):
        subject = self.cleaned_data['subject']
        return subject

    def clean_message(self):
        message = self.cleaned_data['message']
        return message

class TestimonialsForm(forms.Form):
    """合格体験記の投稿フォーム
    """
    # 合格した試験
    exam_subject = forms.fields.ChoiceField(
        choices = (
            # (0, '選択してください'),
            (1, '食品表示検定・初級'),
            # (2, '食品表示検定中級'),
        ),
        initial=1,
        required=True,
        widget=forms.widgets.Select()
    )
    # 利用したコース
    payment_course = forms.fields.ChoiceField(
        choices = (
            # (0, '選択してください'),
            (1, '食品表示検定・初級'),
            # (2, '食品表示検定・中級'),
        ),
        # TODO: 中級できたら以下に変える
        # choices = PaymentCourse.PAYMENT_COURSE_CHOICES,
        # initial = PaymentCourse.Free,
        initial=1,
        required=True,
        widget=forms.widgets.Select()
    )
    # 利用したプラン
    payment_plan = forms.fields.ChoiceField(
        choices = (
            (0, '選択してください'),
            (1, 'マンスリープラン'),
            (2, '10days集中プラン'),
            (3, '3daysお試しプラン'),
        ),
        initial=0,
        required=True,
        widget=forms.widgets.Select()
    )
    # ペンネーム
    pen_name = forms.CharField(
        required=True,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        max_length=255,
        min_length=3,
        widget=forms.EmailInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    title = forms.CharField(
        required=True,
        min_length=5,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    # 受験日
    exam_date = forms.DateField(
        required=True,
        # widget=forms.SelectDateWidget()
        widget=forms.NumberInput(
            attrs={
                'type': 'date',
            }
        ),
    )
    # 取得点数
    points = forms.IntegerField(
        required=True,
        min_value=70,
        max_value=100,
        initial=70,
    )
    # 何回目の受験か
    times = forms.CharField(
        required=True,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    # 学習期間
    learning_time = forms.CharField(
        required=True,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    # 参考にしたサイト
    referenced_site = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        ),
    )
    # 学習方法
    learning_method = forms.CharField(
        required=True,
        min_length=50,
        max_length=512,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を50文字以上で入力してください。',
                'rows': '4',
            }
        ),
    )
    # 試験の感想
    impression = forms.CharField(
        required=True,
        min_length=50,
        max_length=512,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を50文字以上で入力してください。',
                'rows': '4',
            }
        ),
    )
    # 受験者へのアドバイス
    advice = forms.CharField(
        required=True,
        min_length=50,
        max_length=512,
        widget=forms.Textarea(
            attrs={
                'placeholder': '内容を50文字以上で入力してください。',
                'rows': '4',
            }
        ),
    )
    # 次に受験予定の試験
    next_exam = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
            }
        )
    )
    # フードイグザムの改善点、応援メッセージ
    improvements = forms.CharField(
        required=False,
        max_length=512,
        widget=forms.Textarea(
            attrs={
                'placeholder': '',
                'rows': '4',
            }
        )
    )

    def clean_exam_subject(self):
        """合格した試験"""
        exam_subject = self.cleaned_data['exam_subject']
        if isinstance(exam_subject, str):
            exam_subject = int(exam_subject)
        if exam_subject == 0:
            self.add_error(
                field='exam_subject',
                error='選択してください。')
        return exam_subject

    def clean_payment_course(self):
        """利用したコース"""
        payment_course = self.cleaned_data['payment_course']
        if isinstance(payment_course, str):
            payment_course = int(payment_course)
        if payment_course == 0:
            self.add_error(
                field='payment_course',
                error='選択してください。')
        return payment_course

    def clean_payment_plan(self):
        """利用したプラン"""
        payment_plan = self.cleaned_data['payment_plan']
        if isinstance(payment_plan, str):
            payment_plan = int(payment_plan)
        if payment_plan == 0:
            self.add_error(
                field='payment_plan',
                error='選択してください。')
        return payment_plan

    def clean_pen_name(self):
        """ペンネーム"""
        pen_name = self.cleaned_data['pen_name']
        return pen_name

    def clean_email(self):
        """email"""
        email = self.cleaned_data['email']
        return email

    def clean_title(self):
        """タイトル"""
        title = self.cleaned_data['title']
        return title

    def clean_exam_date(self):
        """受験日"""
        exam_date = self.cleaned_data['exam_date']
        return exam_date

    def clean_points(self):
        """取得点数"""
        points = self.cleaned_data['points']
        return points

    def clean_learning_time(self):
        """何回目の受験か"""
        learning_time = self.cleaned_data['learning_time']
        return learning_time

    def clean_referenced_site(self):
        """参考にしたサイト"""
        referenced_site = self.cleaned_data['referenced_site']
        return referenced_site

    def clean_learning_method(self):
        """learning_method"""
        learning_method = self.cleaned_data['learning_method']
        return learning_method

    def clean_impression(self):
        """試験の感想"""
        impression = self.cleaned_data['impression']
        return impression

    def clean_advice(self):
        """受験者へのアドバイス"""
        advice = self.cleaned_data['advice']
        return advice

    def clean_next_exam(self):
        """次に受験予定の試験"""
        next_exam = self.cleaned_data['next_exam']
        return next_exam

    def clean_improvements(self):
        """フードイグザムの改善点、応援メッセージ"""
        improvements = self.cleaned_data['improvements']
        return improvements

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
