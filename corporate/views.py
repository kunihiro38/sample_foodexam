"""
記法
TODO:あとで手をつける
FIXME:既知の不具合があるコード
HACK:あまりキレイじゃない解決案
XXX:危険!大きな問題がある
"""
import datetime
from datetime import timezone

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.core.exceptions import PermissionDenied
from django.core.mail import BadHeaderError, send_mail
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, Http404, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from jrfoodadv.models import JrFoodLabelingAdviseQuestion
from foodadv.models import FoodLabelingAdviseQuestion

import corporate.logics as corporate_logics
import jrfoodadv.logics as jrfoodadv_logics
import foodadv.logics as foodadv_logics

from .forms import InquiryAddForm, SignUpForm, SigninForm, \
    CustomPasswordResetForm, CustomSetPasswordForm, WithdrawalForm, EditUsernameForm, \
    ChangePasswordForm, TestimonialsForm
    # ChangeEmailForm
from .models import UserCourse, Release, Information, Category, PaymentCourse, \
    PaymentPlan, Testimonials, Exam


User = get_user_model()


def check_limited_user_by_email(email):
    """ usernameからuserを取得
    利用制限したemail。フードイグザムの機能を使ってもらいたい時に提示する。
    """
    qs = User.objects.get(email=email)
    if qs.email == settings.LIMITED_EMAIL:
        return qs
    return None


def _check_plan(request):
    """無料プランか初級の有料プランかの判定
    無料プラン：支払日と有効期限がない（登録しただけ）、もしくは過去に有料会員で現在有効期限切れ
    初級有料プラン：支払い済みで有効期限も切れていない
    """
    plan = False
    user_course = UserCourse.get_user_course_by_id(user_id=request.user.id)
    if user_course.payment_course != PaymentCourse.FREE:
        # 有料会員、or過去に有料会員
        if user_course.expired_at < datetime.datetime.now(timezone.utc):
            # 過去に有料会員で期限が切れている
            pass
        else:
            # 有料会員で、期限も切れていない
            plan = True
    elif user_course.payment_course == PaymentCourse.FREE:
        # 無料会員
        pass
    return plan


def _check_foodadv_plan(request):
    """無料プランか中級の有料プランかの判定
    _check_planが初級でこちらは中級を判定
    無料プラン：支払日と有効期限がない（登録しただけ）、もしくは過去に有料会員で現在有効期限切れ
    中級有料プラン：支払い済みで有効期限も切れていない
    """
    foodadv_plan = False
    user_course = UserCourse.get_user_course_by_id(user_id=request.user.id)
    if user_course.foodadv_payment_course != PaymentCourse.FREE:
        # 有料会員、or過去に有料会員
        if user_course.foodadv_expired_at < datetime.datetime.now(timezone.utc):
            # 過去に有料会員で期限が切れている
            pass
        else:
            # 有料会員で、期限も切れていない
            foodadv_plan = True
    elif user_course.foodadv_payment_course == PaymentCourse.FREE:
        # 無料会員
        pass
    return foodadv_plan


@require_http_methods(['GET'])
def index(request):
    """トップページ
    """
    # トップページに表示するオブジェクトの数
    display_cnt = 4
    # お知らせ
    informations = Information.find_informations(display_cnt=display_cnt)
    # 学習コラム
    columns = Information.find_columns(display_cnt=display_cnt)
    # 合格体験記
    testimonials = Testimonials.find_testimonials(display_cnt=display_cnt)

    # category="present"の更新情報を取ってくる
    latest_category_present_info = None
    category_present_info = Information.objects.filter(category=Category.PRESENT)
    if category_present_info:
        latest_category_present_info = category_present_info\
                                        .order_by('-updated_at')[0]

    # category="campaign"の更新情報を取ってくる
    latest_category_campaign_info = None
    category_campaign_info = Information.objects.filter(category=Category.CAMPAIGN)
    if category_campaign_info:
        latest_category_campaign_info = category_campaign_info\
                                            .order_by('-updated_at')[0]

    # フロントでswiperを使用の可否判定
    # フロントでinfoのreleaseで判定もできるがここで統一して行う
    # ここで影響を与えるのは
    # 1. ページネーションとナビボタンの表示
    # 2. swiper-bundle.min.jsとindex.jsの発火
    use_swiper = False
    if category_present_info:
        pass
        # 以前まではキャンペーンが固定されていたので以下を使っていたが不要なので一旦コメントアウト
        # if latest_category_present_info.release == Release.PUBLIC:
        #     use_swiper = True
    if category_campaign_info:
        if latest_category_campaign_info.release == Release.PUBLIC:
            use_swiper = True

    # indexのトップページであることを証明
    # 以下に影響を及ぼすのでケース分けで使用
    # 1. header-logのh1タグ
    # 2. _food_exam_feature.html
    top_page = True

    jrfoodadv_redirect_url = _check_user_course(request)
    foodadv_redirect_url = _check_foodadv_user_course(request)
    context = {
        'informations': informations,
        'columns': columns,
        'testimonials': testimonials,
        'exam': Exam,
        'informations_count': len(informations),
        'columns_count': len(columns),
        'testimonials_count': len(testimonials),
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(),
        'jrfoodadv_redirect_url': jrfoodadv_redirect_url,
        'foodadv_redirect_url': foodadv_redirect_url,
        'latest_category_present_info': latest_category_present_info,
        'latest_category_campaign_info': latest_category_campaign_info,
        'top_page' : top_page,
        'release_model': Release,
        'use_swiper': use_swiper,
    }
    return render(request, 'corporate/index.html', context)


@require_http_methods(['GET'])
def info_list(request):
    """お知らせ一覧
    ・学習コラムは除外
    """
    informations = Information.find_informations()
    context = {
        'informations': informations,
        'model_category': Category,
    }
    return render(request, 'corporate/info/info_list.html', context)


@require_http_methods(['GET'])
def column(request):
    """学習コラム一覧
    ・学習コラムのみをfilterでキャッチ
    """
    columns = Information.find_columns()
    context = {
        'informations': columns,
        'model_category': Category,
    }
    return render(request, 'corporate/column.html', context)


@require_http_methods(['GET'])
def testimonials_list(request):
    """合格体験記一覧
    """
    testimonials = Testimonials.find_testimonials()
    context = {
        'testimonials': testimonials,
        'exam': Exam,
    }
    return render(request, 'corporate/testimonials/testimonials_list.html', context)


def _make_next_and_prev_page(info_id, information, category=None):
    """ 次のページと前のページを作成する
    informationに、next_pageとprev_pageを参照渡しして返す
    releaseが公開中のものに限る
    categoryはCategory.COLUMN（学習コラム）かそれ以外に分けられる
    """
    # 学習コラム
    if category == Category.COLUMN:
        information_qs = Information.objects\
                            .filter(Q(category=category)\
                                    & (Q(release=Release.PUBLIC)))\
                            .order_by('-created_at')
        
        latest_info = information_qs.first()
        last_info = information_qs.last()
    # 学習コラム以外
    else:
        information_qs = Information.objects\
                            .filter(release=Release.PUBLIC)\
                            .exclude(category=Category.COLUMN)\
                            .order_by('-created_at')
        latest_info = information_qs.first()
        last_info = information_qs.last()

    # idの一覧をリストに格納する
    list_all_info_category_column = [info.id for info in information_qs]

    # 次のページのidを取得する
    if isinstance(info_id, str):
        int_info_id = int(info_id)
    information.next_page = None
    for _id in range(int_info_id, latest_info.id):
        next_info_id = _id+1
        if next_info_id in list_all_info_category_column:
            next_info = Information.objects.get(id=next_info_id)
            information.next_page = next_info
            break

    # 前のページのidを取得する
    information.prev_page = None
    for _id in reversed(range(last_info.id, int_info_id)):
        if _id in list_all_info_category_column:
            prev_info = Information.objects.get(id=_id)
            information.prev_page = prev_info
            break

    return information


@require_http_methods(['GET'])
def info_individual(request, info_id):
    """お知らせ個別
    学習コラム個別との違いは、categoryがcolumnか否か
    """
    # 数字以外が来たら404
    if info_id.isdecimal() is False:
        raise Http404('Page not found')
    information = get_object_or_404(Information, id=info_id)
    # 下書きなら404
    if information.release == Release.DRAFT:
        raise Http404('Page not found')
    # 学習コラムなら404
    if information.category == Category.COLUMN:
        raise Http404('Page not found')

    information = _make_next_and_prev_page(
                                    info_id=info_id,
                                    information=information,
                                    category=None)

    information.category_as_str = information.category_as_str()
    context = {
        'information': information,
        'model_category': Category,
        'site_url': settings.FOOD_EXAM_SITE_URL,
    }
    return render(request, 'corporate/info/info_individual.html', context)


@require_http_methods(['GET'])
def column_individual(request, info_id):
    """学習コラム個別
    お知らせ個別との違いは、categoryがcolumnか否か
    """
    # 数字以外が来たら404
    if info_id.isdecimal() is False:
        raise Http404('Page not found')
    information = get_object_or_404(Information, id=info_id)
    # 下書きなら404
    if information.release == Release.DRAFT:
        raise Http404('Page not found')
    # 学習コラム以外なら404
    if information.category != Category.COLUMN:
        raise Http404('Page not found')

    information = _make_next_and_prev_page(
                                    info_id=info_id,
                                    information=information,
                                    category=Category.COLUMN)

    information.category_as_str = information.category_as_str()
    context = {
        'information': information,
        'model_category': Category,
        'site_url': settings.FOOD_EXAM_SITE_URL,
    }
    return render(request, 'corporate/info/info_individual.html', context)


def _make_testimonials_next_and_prev_page(testimonials_id, testimonials):
    testimonials_qs = Testimonials.objects\
                                    .filter(Q(release=Release.PUBLIC))\
                                    .order_by("-published_at")
    testimonials_ids = [testimonial.id for testimonial in testimonials_qs]

    latest_testimonials = testimonials_qs.first()
    last_testimonials = testimonials_qs.last()

    # 次のページのidを取得する
    if isinstance(testimonials_id, str):
        int_testimonials_id = int(testimonials_id)
    testimonials.next_page = None
    for _id in range(int_testimonials_id, latest_testimonials.id):
        next_testimonials_id = _id+1
        if next_testimonials_id in testimonials_ids:
            next_testimonials = Testimonials.objects.get(id=next_testimonials_id)
            testimonials.next_page = next_testimonials
            break

    # 前のページのidを取得する
    testimonials.prev_page = None
    for _id in reversed(range(last_testimonials.id, int_testimonials_id)):
        if _id in testimonials_ids:
            prev_testimonials = Testimonials.objects.get(id=_id)
            testimonials.prev_page = prev_testimonials
            break

    return testimonials


@require_http_methods(['GET'])
def testimonials_individual(request, testimonials_id):
    """合格体験記個別
    """
    # 数字以外が来たら404
    if testimonials_id.isdecimal() is False:
        raise Http404('Page not found')
    testimonials_obj = get_object_or_404(Testimonials, id=testimonials_id)
    # 下書きなら404
    if testimonials_obj.release == Release.DRAFT:
        raise Http404('Page not found')

    testimonials = _make_testimonials_next_and_prev_page(
                                    testimonials_id=testimonials_id,
                                    testimonials=testimonials_obj)

    # 参照渡しで格納しておく
    testimonials.payment_course = testimonials.payment_course_as_str()
    testimonials.payment_plan = testimonials.payment_plan_as_str()
    testimonials.exam = Exam

    context = {
        'testimonials': testimonials,
        'site_url': settings.FOOD_EXAM_SITE_URL,
    }
    return render(request, 'corporate/testimonials/testimonials_individual.html', context)



@require_http_methods(['GET'])
def maintenance(request):
    """メンテナンス"""
    return render(request, 'corporate/maintenance.html')


class Signup(generic.CreateView):
    """アカウント仮登録とメッセージ送信"""
    template_name = 'corporate/signup/signup.html'
    form_class = SignUpForm
    def get(self, request, *args, **kwargs):
        # TODO:本番時は消す
        if not settings.PRODUCTION is True:
            return render(request, 'corporate/maintenance.html')

        # 既にログイン中の場合はアクセスできない
        if request.user.is_authenticated:
            raise PermissionDenied
        context = {
            'form': SignUpForm()
        }
        return render(request, 'corporate/signup/signup.html', context)

    def form_valid(self, form):
        """仮登録と本登録用メールの発行"""
        # 仮登録と本登録の切り替えは、is_active属性を使用
        # 退会処理も、is_activeをFalseにする
        user = form.save(commit=False)
        user.is_active = False

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
            'site_url': settings.FOOD_EXAM_SITE_URL,
        }

        subject = render_to_string('corporate/signup/signup_subject.txt', context)
        message = render_to_string('corporate/signup/signup_message.txt', context)

        user.email_user(subject, message)
        return HttpResponseRedirect(reverse('corporate:signup_sent'))


class SignupSent(generic.TemplateView):
    """アカウント仮登録完了"""
    template_name = 'corporate/signup/signup_sent.html'


class SignupComplete(generic.TemplateView):
    """メール内URLアクセル後のユーザー本登録"""
    template_name = 'corporate/signup/signup_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録"""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録
                    user.is_active = True

                    # UserCourseを作成
                    if not UserCourse.objects.filter(user_id=user.id):
                        user_data = {
                            'user_id': user.id,
                            'payment_course': PaymentCourse.FREE,
                            'paid_at': None,
                            'expired_at': None,
                        }

                    # 自動ログインさせる
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                    return super().get(request, **kwargs)

        return render(request, 'corporate/signup/signup_complete.html')


@require_http_methods(['GET'])
def introduction(request):
    return render(request, 'corporate/introduction.html')


def _check_user_course(request):
    # """ユーザーのステータスを確認してリダイレクト先を遷移
    # もし、1.支払い済み 2.期限切れでない
    # →jrfoodadv:indexにリダイレクト
    # そうでなければ
    # →corporate:jrfoodadv_planにリダイレクト
    # """
    # redirect_url = '/course/jrfoodadv/'
    # if str(request.user) != 'AnonymousUser':
    #     user_course = UserCourse.get_user_course_by_id(user_id=request.user.id)
    #     # 登録済みだが、未支払い：payment_courseが0ではないことを確認
    #     # 登録済みで支払い済みだが、期限切れ->payment_courseが1でも期限切れを想定
    #     if user_course.payment_course != PaymentCourse.FREE and \
    #         user_course.expired_at > datetime.datetime.now(timezone.utc):
    #         redirect_url = '/jrfoodadv/'

    # return redirect_url


    """
    会員未登録 → corporate:jrfoodadv_planにリダイレクト
    無料プラン → corporate:jrfoodadv_planにリダイレクト
    有料プラン → jrfoodadv:indexにリダイレクト
    """
    redirect_url = '/course/jrfoodadv/'
    if str(request.user) != 'AnonymousUser':
        if _check_plan(request):
            # 有料プラン
            redirect_url = '/jrfoodadv/'

    return redirect_url


def _check_foodadv_user_course(request):
    """
    会員未登録 → corporate:foodadv_planにリダイレクト
    無料プラン → corporate:foodadv_planにリダイレクト
    有料プラン → foodadv:indexにリダイレクト
    """
    foodadv_redirect_url = '/course/foodadv/'
    if str(request.user) != 'AnonymousUser':
        if _check_foodadv_plan(request):
            # 有料プラン
            foodadv_redirect_url = '/foodadv/'

    return foodadv_redirect_url


@require_http_methods(['GET'])
def course(request):
    """コース選択"""
    jrfoodadv_redirect_url = _check_user_course(request)
    foodadv_redirect_url = _check_foodadv_user_course(request)
    context = {
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(),
        'count_foodadv': FoodLabelingAdviseQuestion.count_foodadv_questions(),
        'jrfoodadv_redirect_url': jrfoodadv_redirect_url,
        'foodadv_redirect_url': foodadv_redirect_url,
    }
    return render(request, 'corporate/course/course.html', context)


@require_http_methods(['GET'])
def jrfoodadv_plan(request):
    """食品表示検定・初級のプラン選択"""
    context = {
        'monthly_plan_name': settings.JRFOODADV_MONTHLY_PLAN_NAME,
        'ten_days_plan_name': settings.JRFOODADV_TEN_DAYS_PLAN_NAME,
        'tree_days_plane_name': settings.JRFOODADV_THREE_DAYS_PLAN_NAME,
        'monthly_amount': settings.JRFOODADV_MONTHLY_AMOUNT,
        'monthly_usable_period': settings.MONTHLY_USABLE_PERIOD,
        'ten_days_amount': settings.JRFOODADV_TEN_DAYS_AMOUNT,
        'ten_days_usable_period': settings.TEN_DAYS_USABLE_PERIOD,
        'three_days_amount': settings.JRFOODADV_THREE_DAYS_AMOUNT,
        'three_days_usable_period': settings.THREE_DAYS_USABLE_PERIOD,
    }
    return render(request, 'corporate/course/jrfoodadv/jrfoodadv_plan.html', context)


def _make_expired_at(usable_period):
    dt_now = datetime.datetime.now()
    after_thirty_one_days = dt_now + datetime.timedelta(days=usable_period + 1) # 31
    basetime = datetime.time(00, 00, 00)
    expired_at = datetime.datetime.combine(after_thirty_one_days, basetime) \
                    - datetime.timedelta(seconds=1)
    return expired_at


def _pay_plan(request, plan_name, amount, payment_course, expired_at):
    payjp_token = request.POST.get("payjp-token")

    if payment_course == PaymentCourse.JRFOODADV:
        # 初級
        course_description = "食品表示検定・初級コース"
        directory = 'jrfoodadv'
    elif payment_course == PaymentCourse.FOODADV:
        # 中級
        course_description = "食品表示検定・中級コース"
        directory = 'foodadv'
    else:
        raise RuntimeError()

    # トークンから顧客情報を生成
    pass

    # 支払いの実行
    pass

    user_course = UserCourse.objects.filter(user_id=request.user.id)[0]
    if payment_course == PaymentCourse.JRFOODADV:
        # 初級
        user_course.payment_course = payment_course
        user_course.paid_at = datetime.datetime.now()
        user_course.expired_at = expired_at
    elif payment_course == PaymentCourse.FOODADV:
        # 中級
        user_course.foodadv_payment_course = payment_course
        user_course.foodadv_paid_at = datetime.datetime.now()
        user_course.foodadv_expired_at = expired_at

    user = User.objects.get(id=request.user.id)
    subject_context = {
        'course_description': course_description,
    }
    message_context = {
        'email': user.email,
        'course_description': course_description,
        'updated_at': user_course.updated_at,
        'plan_name': plan_name,
        'amount': amount,
        'expired_at': expired_at,
        'site_url': settings.FOOD_EXAM_SITE_URL,
        'directory': directory,
    }
    send_mail(subject=render_to_string(
                    'corporate/course/pay_success_subject.txt', subject_context),
                message=render_to_string(
                    'corporate/course/pay_success_message.txt', message_context),
                from_email=user.email,
                recipient_list=[user.email])


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def plan_monthly(request):
    """初級マンスリープラン"""
    plan_name = settings.JRFOODADV_MONTHLY_PLAN_NAME
    amount = settings.JRFOODADV_MONTHLY_AMOUNT
    payment_course = PaymentCourse.JRFOODADV
    expired_at = _make_expired_at(settings.MONTHLY_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:pay_success'))

    context = {
        'plan_name': plan_name,
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(),
        'amount': amount,
        'usable_period': settings.MONTHLY_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/jrfoodadv/plan_monthly.html', context)


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def plan_10days(request):
    """初級10days集中プラン"""
    plan_name = settings.JRFOODADV_TEN_DAYS_PLAN_NAME
    amount = settings.JRFOODADV_TEN_DAYS_AMOUNT
    payment_course = PaymentCourse.JRFOODADV
    expired_at = _make_expired_at(settings.TEN_DAYS_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:pay_success'))

    context = {
        'plan_name': settings.JRFOODADV_TEN_DAYS_PLAN_NAME,
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(),
        'amount': amount,
        'usable_period': settings.TEN_DAYS_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/jrfoodadv/plan_10days.html', context)


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def plan_3days(request):
    """初級3days短期プラン"""
    plan_name = settings.JRFOODADV_THREE_DAYS_PLAN_NAME
    amount = settings.JRFOODADV_THREE_DAYS_AMOUNT
    payment_course = PaymentCourse.JRFOODADV
    expired_at = _make_expired_at(settings.THREE_DAYS_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:pay_success'))

    context = {
        'plan_name': settings.JRFOODADV_THREE_DAYS_PLAN_NAME,
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(),
        'amount': amount,
        'usable_period': settings.THREE_DAYS_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/jrfoodadv/plan_3days.html', context)


@require_http_methods(['GET'])
def pay_success(request):
    """支払い成功
    """
    redirect_url = _check_user_course(request)
    context = {
        'count_jrfoodadv': JrFoodLabelingAdviseQuestion.count_jrfoodadv_questions(), # 全問題数カウント
        'redirect_url': redirect_url
    }
    return render(request, 'corporate/course/jrfoodadv/pay_success.html', context)


@require_http_methods(['GET'])
def foodadv_plan(request):
    """食品表示検定・中級のプラン選択"""
    # TODO: 完成するまでは404
    raise Http404()
    context = {
        'monthly_plan_name': settings.FOODADV_MONTHLY_PLAN_NAME,
        'ten_days_plan_name': settings.FOODADV_TEN_DAYS_PLAN_NAME,
        'tree_days_plane_name': settings.FOODADV_THREE_DAYS_PLAN_NAME,
        'monthly_amount': settings.FOODADV_MONTHLY_AMOUNT,
        'monthly_usable_period': settings.MONTHLY_USABLE_PERIOD,
        'ten_days_amount': settings.FOODADV_TEN_DAYS_AMOUNT,
        'ten_days_usable_period': settings.TEN_DAYS_USABLE_PERIOD,
        'three_days_amount': settings.FOODADV_THREE_DAYS_AMOUNT,
        'three_days_usable_period': settings.THREE_DAYS_USABLE_PERIOD,
    }
    return render(request, 'corporate/course/foodadv/foodadv_plan.html', context)


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def foodadv_plan_monthly(request):
    """中級マンスリープラン"""
    # TODO: 完成するまでは404
    raise Http404()
    plan_name = settings.FOODADV_MONTHLY_PLAN_NAME
    amount = settings.FOODADV_MONTHLY_AMOUNT
    payment_course = PaymentCourse.FOODADV
    expired_at = _make_expired_at(settings.MONTHLY_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:foodadv_pay_success'))

    context = {
        'plan_name': plan_name,
        'count_foodadv': FoodLabelingAdviseQuestion.count_foodadv_questions(),
        'amount': amount,
        'usable_period': settings.MONTHLY_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/foodadv/foodadv_plan_monthly.html', context)


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def foodadv_plan_10days(request):
    """中級10days集中プラン"""
    # TODO: 完成するまでは404
    raise Http404()
    plan_name = settings.FOODADV_TEN_DAYS_PLAN_NAME
    amount = settings.FOODADV_TEN_DAYS_AMOUNT
    payment_course = PaymentCourse.FOODADV
    expired_at = _make_expired_at(settings.TEN_DAYS_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:foodadv_pay_success'))

    context = {
        'plan_name': settings.FOODADV_TEN_DAYS_PLAN_NAME,
        'count_foodadv': FoodLabelingAdviseQuestion.count_foodadv_questions(),
        'amount': amount,
        'usable_period': settings.TEN_DAYS_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/foodadv/foodadv_plan_10days.html', context)


@csrf_exempt # 外部のURLを対象にするpostフォームのCSRFトークンの脆弱性を防ぐ
@require_http_methods(['GET', 'POST'])
def foodadv_plan_3days(request):
    """中級3days短期プラン"""
    # TODO: 完成するまでは404
    raise Http404()
    plan_name = settings.FOODADV_THREE_DAYS_PLAN_NAME
    amount = settings.FOODADV_THREE_DAYS_AMOUNT
    payment_course = PaymentCourse.FOODADV
    expired_at = _make_expired_at(settings.THREE_DAYS_USABLE_PERIOD)
    if request.method == 'GET':
        # user_course = get_object_or_404(UserCourse, user_id=request.user.id)
        pass
    elif request.method == 'POST':
        _pay_plan(request, plan_name, amount, payment_course, expired_at)
        return HttpResponseRedirect(reverse('corporate:foodadv_pay_success'))

    context = {
        'plan_name': settings.FOODADV_THREE_DAYS_PLAN_NAME,
        'count_foodadv': FoodLabelingAdviseQuestion.count_foodadv_questions(),
        'amount': amount,
        'usable_period': settings.THREE_DAYS_USABLE_PERIOD,
        'expired_at': expired_at,
        'public_key': settings.PAYJP_API_TEST_PUBLICK_KEY,
    }
    return render(request, 'corporate/course/foodadv/foodadv_plan_3days.html', context)


@require_http_methods(['GET'])
def foodadv_pay_success(request):
    """中級支払い成功
    """
    # TODO: 完成するまで404
    # raise Http404()
    foodadv_redirect_url = _check_foodadv_user_course(request)
    context = {
        'count_foodadv': FoodLabelingAdviseQuestion.count_foodadv_questions(), # 全問題数カウント
        'foodadv_redirect_url': foodadv_redirect_url,
    }
    return render(request, 'corporate/course/foodadv/foodadv_pay_success.html', context)


@require_http_methods(['GET', 'POST'])
def signin(request):
    """ログイン
    """
    logout(request)
    if request.method != 'POST':
        if str(request.user) != 'AnonymousUser':
            form = ''
        else:
            form = SigninForm()
    else:
        form = SigninForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('corporate:index'))
            else:
                pass
    context = {
        'form': form
    }
    return render(request, 'corporate/signin/signin.html', context)


class PasswordReset(PasswordResetView):
    """パスワードリセット"""
    subject_template_name = 'corporate/password_reset/reset_password_subject.txt'
    email_template_name = 'corporate/password_reset/reset_password_message.txt'
    template_name = 'corporate/maintenance.html' if not settings.PRODUCTION is True \
        else 'corporate/password_reset/password_reset_form.html'
    template_name = 'corporate/password_reset/password_reset_form.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('corporate:password_reset_sent')


class PasswordResetSent(PasswordResetDoneView):
    """パスワード変更用URL送信"""
    def get(self, request, *args, **kwargs):
        if str(request.user) != 'AnonymousUser':
            raise PermissionDenied()
        return render(request, 'corporate/password_reset/password_reset_sent.html')


class PasswordResetConfirm(PasswordResetConfirmView):
    """パスワード再設定"""
    template_name = 'corporate/password_reset/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('corporate:password_reset_complete')


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定完了"""
    template_name = 'corporate/password_reset/password_reset_complete.html'


@login_required
@require_http_methods(['GET'])
def setting(request):
    """設定"""
    return render(request, 'corporate/corporate_setting/setting.html')


@login_required
@require_http_methods(['GET', 'POST'])
def withdrawal(request):
    """退会処理"""
    # TODO:本番時は消す
    limited_user = check_limited_user_by_email(request.user.email)
    if not settings.PRODUCTION is True or limited_user:
        return render(request, 'corporate/maintenance.html')

    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        form = WithdrawalForm(user_id=request.user.id)
    elif request.method == 'POST':
        form = WithdrawalForm(user_id=request.user.id, data=request.POST)
        if form.is_valid():
            @transaction.atomic
            def withdrawal_user(request, user):
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                if user.email != email:
                    raise RuntimeError()
                auth_result = authenticate(
                    username = user.username,
                    password = password,)
                if not auth_result:
                    raise RuntimeError()
                jrfoodadv_logics.delete_record_by_user_id(user_id=request.user.id)
                foodadv_logics.delete_foodadv_record_by_user_id(user_id=request.user.id)

                message_context = {
                    'site_url': settings.FOOD_EXAM_SITE_URL,
                }
                send_mail(subject=render_to_string(
                                'corporate/corporate_setting/withdrawal_subject.txt'),
                            message=render_to_string(
                                'corporate/corporate_setting/withdrawal_message.txt',
                                message_context),
                            from_email=email,
                            recipient_list=[email])
            withdrawal_user(request=request, user=user)
            return HttpResponseRedirect(reverse('corporate:del_profile_success'))

    context = {
        'form':form,
    }
    return render(request, 'corporate/corporate_setting/withdrawal.html', context)


@login_required(login_url='/signin/')
@require_http_methods(['GET', 'POST'])
def profile(request):
    """プロフィール"""
    user = User.objects.get(id=request.user.id)
    user_course = UserCourse.get_user_course_by_id(user_id=request.user.id)

    user_info_dict = {
        'username': user.username,
        'email': user.email,
        'payment_course': user_course.payment_course_as_str(),
        'paid_at': user_course.paid_at,
        'expired_at': user_course.expired_at,
        'foodadv_payment_course': user_course.foodadv_payment_course_as_str(),
        'foodadv_paid_at': user_course.foodadv_paid_at,
        'foodadv_expired_at': user_course.foodadv_expired_at,
    }
    # ログアウト処理
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('corporate:user_logout'))

    context = {
        'user_info': user_info_dict,
    }
    return render(request, 'corporate/profile/profile.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def edit_username(request):
    """アカウント名編集"""
    # TODO:本番時は消す
    limited_user = check_limited_user_by_email(request.user.email)
    if not settings.PRODUCTION is True or limited_user:
        return render(request, 'corporate/maintenance.html')

    user = User.objects.get(id=request.user.id)

    if request.method == 'GET':
        form = EditUsernameForm()

    elif request.method == 'POST':
        form = EditUsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user.username = username
            return HttpResponseRedirect(reverse('corporate:edit_success'))

    context = {
        'username': user.username,
        'form': form,
    }
    return render(request, 'corporate/profile/edit_username.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def change_email(request):
    """メールアドレス変更"""
    # TODO:本番時は消す
    # TODO: 20220312-有用性を感じないので、テスト含めてコメントアウトしておく。
    # if not settings.PRODUCTION is True:
    return render(request, 'corporate/maintenance.html')
    # user = User.objects.get(id=request.user.id)
    # if request.method == 'GET':
    #     form = ChangeEmailForm()
    # elif request.method == 'POST':
    #     form = ChangeEmailForm(request.POST)
    #     if form.is_valid():
    #         email = form.cleaned_data['email']
    #         user.email = email
    #         # TODO:
    #         # パスワード変更時のメール送信
    #         return HttpResponseRedirect(reverse('corporate:edit_success'))
    # context = {
    #     'email': user.email,
    #     'form': form,
    # }
    # return render(request, 'corporate/profile/change_email.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def change_password(request):
    """パスワード変更"""
    # TODO:本番時は消す
    limited_user = check_limited_user_by_email(request.user.email)
    if not settings.PRODUCTION is True or limited_user:
        return render(request, 'corporate/maintenance.html')

    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        form = ChangePasswordForm(user_id=request.user.id)
    elif request.method == 'POST':
        form = ChangePasswordForm(user_id=request.user.id, data=request.POST)
        if form.is_valid():
            confirm_new_password = form.cleaned_data['confirm_new_password']
            user.set_password(confirm_new_password)

            user = authenticate(
                username=user.username,
                password=confirm_new_password,)
            if user is not None:
                login(request, user)
            else:
                raise RuntimeError('invalid')
            return HttpResponseRedirect(reverse('corporate:edit_success'))
    context = {
        'form': form,
    }
    return render(request, 'corporate/profile/change_password.html', context)



@login_required
@require_http_methods(['GET'])
def edit_success(request):
    """更新"""
    user = User.objects.get(id=request.user.id)
    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, 'corporate/profile/edit_success.html', context)


@require_http_methods(['GET'])
def del_profile_success(request):
    """アカウント削除完了
    基本的には、jrfoodadv:withdrawalの退会処理からしか302されない
    """
    if str(request.user) != 'AnonymousUser':
        raise PermissionDenied()
    return render(request, 'corporate/profile/del_profile_success.html')


@login_required(login_url='/signin/')
@require_http_methods(['GET'])
def user_logout(request):
    """ログアウト完了後のページ
    """
    logout(request)
    return render(request, 'corporate/profile/logout.html')


@require_http_methods(['GET'])
def terms(request):
    """利用規約
    """
    return render(request, 'corporate/terms.html')


@require_http_methods(['GET'])
def policy(request):
    """プライバシーポリシー
    """
    return render(request, 'corporate/policy.html')


@require_http_methods(['GET'])
def law(request):
    """特定商取引に基づく表記
    """
    context = {
        'site_url': settings.FOOD_EXAM_SITE_URL,
        'amount': settings.JRFOODADV_THREE_DAYS_AMOUNT
    }
    return render(request, 'corporate/law.html', context)


def _get_client_ip(request):
    """IPアドレス取得
    """
    # 'HTTP_X_FORWARDED_FOR'ヘッダを参照して転送経路のIPアドレスを取得する
    forwarded_addresses = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_addresses:
        # 'HTTP_X_FORWARDED_FOR'ヘッダがある場合は転送経路の先頭要素を取得する
        client_ip = forwarded_addresses.split(',')[0]
    else:
        # 'HTTP_X_FORWARDED_FOR'ヘッダがない場合は直接接続なので'REMOTE_ADDR'ヘッダを参照する
        client_ip = request.META.get('REMOTE_ADDR')
    return client_ip

@require_http_methods(['GET', 'POST'])
def inquiry(request):
    """ 問い合わせ
    """
    client_ip = _get_client_ip(request)

    if request.method != 'POST':
        form = InquiryAddForm()
    else:
        form = InquiryAddForm(request.POST)
        if not form.is_valid():
            # バリデーションエラーの発火
            pass
        elif form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            context = {
                'client_ip': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', None),
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
            }
            try:
                send_mail(subject=render_to_string(
                            'corporate/inquiry/inquiry_subject.txt'),
                            message=render_to_string(
                                'corporate/inquiry/inquiry_message.txt', context),
                            from_email=email,
                            recipient_list=[settings.EMAIL_HOST_USER])
            except BadHeaderError:
                # ヘッダインジェクションを防止
                return HttpResponse('Invalid header found.')

            return HttpResponseRedirect(reverse('corporate:inquiry_add_success'))

    context = {'form': form}
    return render(request, 'corporate/inquiry/inquiry.html', context)


@require_http_methods(['GET'])
def inquiry_add_success(request):
    """問い合わせ送信成功
    """
    return render(request, 'corporate/inquiry/inquiry_add_success.html')


@require_http_methods(['GET', 'POST'])
def post_testimonials(request):
    """合格体験記の投稿
    """
    client_ip = _get_client_ip(request)

    if request.method != 'POST':
        form = TestimonialsForm()
    else:
        form = TestimonialsForm(request.POST)
        if not form.is_valid():
            # バリデーションエラーの発火
            pass
        elif form.is_valid():

            @transaction.atomic
            def save_obj_and_send_email(request):
                """ オブジェクトの保存とメールの送信
                """
                exam_subject = form.cleaned_data['exam_subject']
                payment_course = form.cleaned_data['payment_course']
                payment_plan = form.cleaned_data['payment_plan']
                pen_name = form.cleaned_data['pen_name']
                email = form.cleaned_data['email']
                title = form.cleaned_data['title']
                exam_date = form.cleaned_data['exam_date']
                points = form.cleaned_data['points']
                times = form.cleaned_data['times']
                learning_time = form.cleaned_data['learning_time']
                referenced_site = form.cleaned_data['referenced_site']
                learning_method = form.cleaned_data['learning_method']
                impression = form.cleaned_data['impression']
                advice = form.cleaned_data['advice']
                next_exam = form.cleaned_data['next_exam']
                improvements = form.cleaned_data['improvements']

                corporate_logics.create_testimonials(
                    exam_subject=exam_subject,
                    payment_course=payment_course,
                    payment_plan=payment_plan,
                    pen_name=pen_name,
                    email=email,
                    title=title,
                    exam_date=exam_date,
                    points=points,
                    times=times,
                    learning_time=learning_time,
                    referenced_site=referenced_site,
                    learning_method=learning_method,
                    impression=impression,
                    advice=advice,
                    next_exam=next_exam,
                    improvements=improvements)

                # 管理人にメールを送信
                # HACK
                exam_list = ["",
                        "食品表示検定・初級",
                        "食品表示検定・中級"]
                if exam_subject == 1:
                    exam_subject = exam_list[1]
                elif exam_subject == 2:
                    exam_subject = exam_list[2]
                else:
                    raise RuntimeError

                # HACK
                user_existence = False
                if User.objects.filter(email=email).exists():
                    user_existence = True

                context = {
                    'client_ip': client_ip,
                    'user_agent': request.META.get('HTTP_USER_AGENT', None),
                    'exam_subject': exam_subject,
                    'payment_course': PaymentCourse.payment_course_as_str(payment_course),
                    'payment_plan': PaymentPlan.payment_plan_as_str(payment_plan),
                    'pen_name': pen_name,
                    'email': email,
                    'user_existence': user_existence,
                    'title': title,
                    'exam_date': exam_date,
                    'points': points,
                    'times': times,
                    'learning_time': learning_time,
                    'referenced_site': referenced_site,
                    'learning_method': learning_method,
                    'impression': impression,
                    'advice': advice,
                    'next_exam': next_exam,
                    'improvements': improvements,
                }
                try:
                    send_mail(subject=render_to_string(
                                'corporate/testimonials/testimonials_subject.txt'),
                                message=render_to_string(
                                'corporate/testimonials/testimonials_message.txt', context),
                                from_email=email,
                                recipient_list=[settings.EMAIL_HOST_USER])
                except BadHeaderError:
                    # ヘッダインジェクションを防止
                    return HttpResponse('Invalid header found.')

            save_obj_and_send_email(request=request)
            return HttpResponseRedirect(reverse('corporate:post_testimonials_success'))

    context = {'form': form}
    return render(request, 'corporate/testimonials/post_testimonials.html', context)


@require_http_methods(['GET'])
def post_testimonials_success(request):
    """合格体験記の投稿の成功
    """
    return render(request, 'corporate/testimonials/post_testimonials_success.html')
