"""
jrfoodadv
正式名:食品表示検定・初級
英語:Junior Food Labeling Adviser

記法
TODO:あとで手をつける
FIXME:既知の不具合があるコード
HACK:あまりキレイじゃない解決案
XXX:危険!大きな問題がある
"""
import re
import datetime

import urllib.parse
import jrfoodadv.logics as jrfoodadv_logics

from common.messages import FormMessages
from utils import validator

from datetime import timezone

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.timezone import make_aware

from corporate.forms import SigninForm
from corporate.models import UserCourse
from corporate.views import _check_plan

from jrfoodadv.forms import DelRecordForm, SelectQuestions, SelectQuestionForm, \
    SelectPracticeTestForm, SearchQuestionForm, GetPageNumForm, SelectAnswerForm, \
    SearchRecord, _make_choice_combination
from jrfoodadv.models import AnswerResult, Record, JrFoodLabelingAdviseQuestion, \
    TimeLeft, TextbookChapter


User = get_user_model()

# sessionの中身確認で利用
# for key, value in request.session.items():
#     print('{} => {}'.format(key, value))


def check_auth(func):
    # """"未支払いユーザーの検知
    # 0. @login_requiredが先頭に来ることが前提
    # 1. 登録済みだが、未支払い
    # 2. 登録済みで支払い済みだが、期限切れ
    # """
    # def checker(request, *args, **kwargs):
    #     user_course = UserCourse.get_user_course_by_id(user_id=request.user.id)
    #     # 登録済みだが、未支払い：payment_courseが0ではないことを確認
    #     if user_course.payment_course != PaymentCourse.JRFOODADV:
    #         return HttpResponseRedirect(reverse('corporate:jrfoodadv_plan'))
    #     # 登録済みで支払い済みだが、期限切れ->payment_courseが1でも期限切れを想定
    #     if user_course.expired_at < datetime.datetime.now(timezone.utc):
    #         return HttpResponseRedirect(reverse('corporate:jrfoodadv_plan'))
    #     return func(request, *args, **kwargs)
    # return checker
    """"未登録会員ユーザーの検知
    今までは上のコメントアウトの月額1本を採用していたけど、
    無料プランでもログインできるようにしたので無用の長物になってしまった。
    なのでとりあえず存在するだけのコードを書いておく。
    """
    def checker(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return checker


def permission(func):
    """非ログインユーザーがアクセスしたら403を排出
    @permission
    """
    def checker(request, *args, **kwargs):
        func(request)
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied()
    return checker


@require_http_methods(['GET', 'POST'])
def signin(request):
    """ログイン"""

    if request.method == 'GET':
        if str(request.user) != 'AnonymousUser':
            form = ''
        else:
            form = SigninForm()
    else:
        form = SigninForm(request.POST)
        if form.is_valid():
            # email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('jrfoodadv:index'))
            else:
                pass
    context = {
        'form': form
    }
    return render(request, 'corporate/signin/signin.html', context)


@login_required
@check_auth
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
    }
    # ログアウト処理
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('corporate:user_logout'))

    context = {
        'user_info': user_info_dict,
    }
    return render(request, 'jrfoodadv/profile/profile.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def setting(request):
    """設定"""
    return render(request, 'jrfoodadv/jrfoodadv_setting/setting.html')


@permission
@login_required
@check_auth
@require_http_methods(['GET', 'POST'])
def del_record(request):
    """学習履歴の削除"""
    # 無料会員か有料会員か確認
    plan = _check_plan(request)

    if request.method == 'GET':
        form = DelRecordForm(user=request.user)
    elif request.method == 'POST':
        form = DelRecordForm(user=request.user, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if username != request.user.username:
                raise RuntimeError()
            jrfoodadv_logics.delete_record_by_user_id(user_id=request.user.id)
            return HttpResponseRedirect(reverse('jrfoodadv:del_record_success'))
    context = {
        'form': form,
        'plan': plan,
    }
    return render(request, 'jrfoodadv/jrfoodadv_setting/del_record.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def del_record_success(request):
    """学習履歴の削除の成功"""
    return render(request, 'jrfoodadv/jrfoodadv_setting/del_record_success.html')


@login_required
@check_auth
@require_http_methods(['GET'])
def count_question_ajax(request):
    """問題総数を返す
    _create_questions にも同様のロジックがあるのでイコールにしておく
    """
    if not request.headers.get('x-requested-with'):
        raise PermissionDenied()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # user_id
        user_id = request.user.id
        # 全問題数カウント
        question_qs = JrFoodLabelingAdviseQuestion.objects.all()
        record_qs = Record.objects.filter(user_id=user_id)
        # ajax側から'true'が届くので'true'の書き方

        # 1. 未出題のみにチェック→レコードに存在する問題IDだけ排除
        if request.GET.get('unquestioned') == 'true':
            # all()でもいけるが、念のためにuser_idから拾う
            record_qs_ids = [record.question_id for record in record_qs]
            question_qs = question_qs.exclude(question_id__in=record_qs_ids)

        # 2. ミスのみにチェック→ミスだけ抽出して検索
        if request.GET.get('miss') == 'true':
            record_qs = record_qs.filter(current_answer=AnswerResult.INCORRECT)
            record_qs_ids = [record.question_id for record in record_qs]
            question_qs = question_qs.filter(question_id__in=record_qs_ids)

        # 3. 未出題とミスの両方にチェック→レコードから「ミス」だけ抽出して全問題から排除
        # もしくは「未解答」と「正解」を抽出して全問題から排除
        if request.GET.get('unquestioned') == 'true' and request.GET.get('miss') == 'true':
            # 必ず先に未出題かミスをチェックしてから両方チェックになる過程を踏むので
            # 改めてall()で、questionもrecordも全問取得する必要がある
            question_qs = JrFoodLabelingAdviseQuestion.objects.all()
            record_qs = Record.objects.filter(user_id=user_id)
            # record_qs = record_qs.exclude(current_answer__in=[AnswerResult.INCORRECT])
            # ↑コードとイコール↓
            record_qs = record_qs.filter(current_answer__in=[AnswerResult.UNANSWERED,
                                                                AnswerResult.CORRECT])
            record_qs_ids = [record.question_id for record in record_qs]
            question_qs = question_qs.exclude(question_id__in=record_qs_ids)

        questions_dict = {'LABELING_BRIDGE': 0,
                            'FRESH_FOOD': 0,
                            'PROCESSED_FOOD': 0,
                            'VARIOUS_FOOD': 0,
                            'OTHER_FOOD': 0,
                            'THINK_FOOD': 0,
                            'all_questions': 0}

        for question in question_qs:
            if question.textbook_chapter == TextbookChapter.LABELING_BRIDGE:
                questions_dict['LABELING_BRIDGE'] += 1
            elif question.textbook_chapter == TextbookChapter.FRESH_FOOD:
                questions_dict['FRESH_FOOD'] += 1
            elif question.textbook_chapter == TextbookChapter.PROCESSED_FOOD:
                questions_dict['PROCESSED_FOOD'] += 1
            elif question.textbook_chapter == TextbookChapter.VARIOUS_FOOD:
                questions_dict['VARIOUS_FOOD'] += 1
            elif question.textbook_chapter == TextbookChapter.OTHER_FOOD:
                questions_dict['OTHER_FOOD'] += 1
            elif question.textbook_chapter == TextbookChapter.THINK_FOOD:
                questions_dict['THINK_FOOD'] += 1
            else:
                raise RuntimeError()
            questions_dict['all_questions'] += 1

        return JsonResponse(data=questions_dict)


def _del_session(request, except_ids_list=False, except_url_param=False):
    """セッションの削除
    1. formセッションとurlセッションの削除
    2. session_question_ids_listの削除
    3. review_flgのセッションの削除
    4. practice_finish_confirm_sessionの削除
    5. except_url_paramの削除
    6. unquestioned_and_mistakes_flgの削除
    """
    # 1. formセッションとurlセッションの削除
    for session in list(request.session.items()):
        if re.search(r'formj(\d{1,6})', session[0]):
            form_session_key = re.search(r'formj(\d{1,6})', session[0])
            del request.session[form_session_key.group()]
        elif re.search(r'urlj(\d{1,6})', session[0]):
            url_session_key = re.search(r'urlj(\d{1,6})', session[0])
            del request.session[url_session_key.group()]
        else:
            pass

    # 2. session_question_ids_listの削除
    # except_ids_list is Trueなら除外する(削除しない)
    if except_ids_list is False:
        if 'session_question_ids_list' in request.session:
            del request.session['session_question_ids_list']

    # 3. list_review_flg(リストレビューフラグ)のsessionの削除
    # question_id_review_flg(IDレビューフラグ)のsession削除
    if 'list_review_flg' in request.session:
        del request.session['list_review_flg']
    if 'question_id_review_flg' in request.session:
        del request.session['question_id_review_flg']

    # 4. practice_finish_confirm_session(練習モード終了直前の確認の到達確認のsession)のsessionの削除
    if 'practice_finish_confirm_session' in request.session:
        del request.session['practice_finish_confirm_session']

    # 5. except_url_paramの削除 -> 未解答とミスに再挑戦で利用
    if except_url_param is False:
        if 'session_url_param' in request.session:
            del request.session['session_url_param']

    # 6. unquestioned_and_mistakes_flgの削除
    if 'unquestioned_and_mistakes_flg' in request.session:
        del request.session['unquestioned_and_mistakes_flg']

def _del_review_flg_session(request):
    """review_flgのみのsession削除"""
    # list_review_flg(リストレビューフラグ)のsessionの削除
    # session_question_id_review_flg(IDレビューフラグ)のsession削除
    if 'list_review_flg' in request.session:
        del request.session['list_review_flg']
    if 'question_id_review_flg' in request.session:
        del request.session['question_id_review_flg']


def _get_latest_record(request):
    """前回の演習記録取得"""
    latest_record = False
    if Record.objects.filter(user_id=request.user.id).exists():
        latest_record = Record.objects.filter(user_id=request.user.id).latest('saved_at')
    return latest_record


def _check_one_question_a_day(request, plan):
    """無料プランは1日1問しか実行できない判定
    先に_check_plan でプラン判定をしてplanにTrue or Falseの引数をもつ
    recordのcurrent_answerが今日中のものがあるか判定する
    """
    one_question_a_day = False
    if not plan:
        # 無料プラン
        # もしくは過去に有料プランで期限が切れている
        if Record.objects.filter(user_id=request.user.id).exists():
            # 無料プランでrecordのcurrent_answerがあること
            if Record.objects.filter(user_id=request.user.id)\
                                .filter(Q(current_answer=AnswerResult.UNANSWERED)\
                                        |Q(current_answer=AnswerResult.INCORRECT)\
                                        |Q(current_answer=AnswerResult.CORRECT)
                                        ).exists():
                # recordが本日中のものか判定
                record_qs = Record.objects.filter(user_id=request.user.id)\
                                    .filter(Q(current_answer=AnswerResult.UNANSWERED)\
                                        |Q(current_answer=AnswerResult.INCORRECT)\
                                        |Q(current_answer=AnswerResult.CORRECT)
                                        ).latest('updated_at')

                # 日本時間に変換
                saved_at = record_qs.saved_at + datetime.timedelta(hours=9)
                # timezoneの除去
                # ここではsaveせずにあくまで判定で使用するので許容
                saved_at = saved_at.replace(tzinfo=None)

                # 現在時刻
                dt_now = datetime.datetime.now()
                target_days = dt_now + datetime.timedelta(days=0)
                basetime = datetime.time(00, 00, 00)
                # 今日の00:00（午前0時）
                started_at = datetime.datetime.combine(target_days, basetime) \
                                + datetime.timedelta(seconds=0)
                # 今日の23:59
                ended_at = datetime.datetime.combine(target_days, basetime) \
                                + datetime.timedelta(days=1, seconds=-1)

                if started_at < saved_at < ended_at:
                    # 今日は1問とき終わった
                    one_question_a_day = True
                else:
                    # 今日は1問も解いていない
                    pass

            else:
                # 無料プラン
                # 一度も問題を解いていない
                # お気に入りorメモは実行済み
                pass
        else:
            # 無料プラン
            # 一度も問題を解いていない
            pass

    else:
        # 有料プラン
        pass

    return one_question_a_day


@login_required
@check_auth
@require_http_methods(['GET'])
def index(request):
    """トップページ&練習モード
    """
    # セッションの削除
    _del_session(request=request)

    # 前回の演習記録取得
    latest_record = _get_latest_record(request)

    # 無料会員か有料会員か確認
    plan = _check_plan(request)

    # 無料会員なら1日1問判定
    one_question_a_day = False
    if not plan:
        # ここでフラグを立てることで、templateのselectタグにdisabledプロパティが立ち
        # formがinvalidとなり、postできなくなる
        one_question_a_day = _check_one_question_a_day(request, plan)

    form = SelectQuestionForm(request.GET)
    # 初回GET->何も入力がないと空のフォームを返す
    if not form.is_valid():
        form = SelectQuestionForm()

    # 何か入力があった時->302
    if form.is_valid():
        target = form.cleaned_data['target']
        chapter = form.cleaned_data['chapter']
        answers = form.cleaned_data['answers']
        # get_params = '?' + request.GET.urlencode()
        get_params = _make_query_param(target=target,
                                        chapter=chapter,
                                        answers=answers)

        # 未解答とミスに再挑戦で使用のためsessionに保存
        if not 'session_url_param' in request.session:
            request.session['session_url_param'] = get_params


        return HttpResponseRedirect(reverse(
            'jrfoodadv:practice',
            args=(get_params,))
        )

    context = {
        'form': form,
        'latest_record': latest_record, # 前回の演習
        'plan': plan, # 無料プラン
        'one_question_a_day': one_question_a_day, # 1日1問判定
    }
    return render(request, 'jrfoodadv/index.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def select_test(request):
    """トップページ&模擬試験選択
    """
    # セッションの削除
    _del_session(request=request)

    # 前回の演習記録取得
    latest_record = _get_latest_record(request)
    form = SelectPracticeTestForm(request.GET)

    # 無料会員か有料会員か確認
    plan = _check_plan(request)

    if form.is_valid():
        unquestioned_and_mistakes = form.cleaned_data['unquestioned_and_mistakes']
        # start_buttonクリック時
        if 'start_button' in request.GET:
            if unquestioned_and_mistakes:
                # sessionフラグを立てておく
                if not 'unquestioned_and_mistakes_flg' in request.session:
                    request.session['unquestioned_and_mistakes_flg'] = True
                else:
                    raise RuntimeError()

            # 残り時間作成
            time_left_qs = TimeLeft.objects.filter(user_id=request.user.id)
            dt_now = datetime.datetime.now()
            # 世界標準とJST一致で+9h,テスト時間が90分なので+90m
            time_limit = make_aware(dt_now + datetime.timedelta(hours=9, minutes=90))
            if time_left_qs:
                # 過去に模擬試験を実施済みの場合は、既存のtime_leftのレコードを使用する
                time_left = time_left_qs[0]
                time_left.time_left_at = time_limit
            else:
                # 初めて模擬試験を受ける場合は、新規オブジェクト作成
                time_left = TimeLeft(user_id=request.user.id,
                                        time_left_at=time_limit,)

            # 未解答とミスに再挑戦で使用のためsessionに保存
            # target,chapterはindexのようにformがないので空設定
            if not 'session_url_param' in request.session:
                target = []
                chapter = []
                answers = 75
                get_params = _make_query_param(target=target,
                                                chapter=chapter,
                                                answers=answers)
                request.session['session_url_param'] = get_params

            return HttpResponseRedirect(reverse(
                'jrfoodadv:practice_test'))
    context = {
        'form': form,
        'latest_record': latest_record,
        'plan': plan
    }
    return render(request, 'jrfoodadv/select_test.html', context)


def _make_paginator(page_num, question_qs, number_of_display=20):
    """ページング"""
    # Paginator(オブジェクト, ページに表示するデータの数)
    paginator = Paginator(question_qs, number_of_display)

    # 指定ページのオブジェクトを返す。page_num=1はformsで初回get時に指定
    try:
        question_page = paginator.page(page_num)
    # ?page=999や?page=0など存在しない値でアクセスされた場合は404で制御
    except EmptyPage:
        raise Http404('Page does not exist') from EmptyPage()

    return question_page # <Page 1 of 10>

def _create_select_question_form_params(get_params):
    """request.getで取得したパラメーターを分解。
    formのようにリスト化して、2つのリストと1つのintで返す
    """
    target = []
    chapter = []
    answers = ''
    list_params = get_params[1:].split('&')
    for params in list_params:
        params = params.split('=')
        if params[0] == 'target':
            target.append(params[1])
        elif params[0] == 'chapter':
            chapter.append(params[1])
        elif params[0] == 'answers':
            answers = params[1]
        else:
            raise Http404()

    return target, chapter, answers


def _create_questions(request, target, chapter, answers):
    """formの入力値を与えるとquestionsを生成する
    def count_question_ajaxにも同様のロジックがあるのでイコールにしておく
    """
    record_qs = Record.objects.filter(user_id=request.user.id)
    # 出題対象(未出題・ミス)が選択された場合
    if target:
        # 1. 未出題のみにチェック→レコードに存在する問題IDだけ排除
        # if str(SelectQuestions.UNQUESTIONED) == target[0]:
        if str(SelectQuestions.UNQUESTIONED) in target and \
                not str(SelectQuestions.MISS) in target:
            record_question_ids = [record.question_id for record in record_qs]
            question_qs = JrFoodLabelingAdviseQuestion.objects.exclude(
                question_id__in=record_question_ids)

        # 2. ミスのみにチェック→ミスだけ抽出して検索
        elif not str(SelectQuestions.UNQUESTIONED) in target and \
                str(SelectQuestions.MISS) in target:
            record_qs = record_qs.filter(current_answer=AnswerResult.INCORRECT)
            record_question_ids = [record.question_id for record in record_qs]
            question_qs = JrFoodLabelingAdviseQuestion.objects.filter(
                question_id__in=record_question_ids)


        # 3. 未出題とミスの両方にチェック→レコードから「ミス」だけ抽出して全問題から排除
        # もしくは「未解答」と「正解」を抽出して全問題から排除
        elif str(SelectQuestions.UNQUESTIONED) in target and \
            str(SelectQuestions.MISS) in target:
            record_qs = record_qs.filter(current_answer__in=[AnswerResult.UNANSWERED,
                                                                AnswerResult.CORRECT])
            record_question_ids = [record.question_id for record in record_qs]
            question_qs = JrFoodLabelingAdviseQuestion.objects.exclude(
                question_id__in=record_question_ids)

        else:
            RuntimeError('invalid')

        # 最後に出題対象と出題数を付与
        question_qs = question_qs.filter(textbook_chapter__in=chapter)
        question_qs = question_qs.order_by('?')[:int(answers)]


    # 出題対象(未出題・ミス)が何も選択されていない、出題分野だけ選択された場合
    else:
        question_qs = JrFoodLabelingAdviseQuestion.objects\
            .filter(textbook_chapter__in=chapter).order_by('?')[:int(answers)]

    return question_qs


def _arbitrary_sequence(session_question_ids_list):
    """並びをsession_question_ids_listで任意順序にし直して返すコード
    書かないとfilterを発動した時にidの昇順になってしまう
    """
    question_qs = JrFoodLabelingAdviseQuestion.objects.filter(
        question_id__in=session_question_ids_list)
    questions = dict([(question.question_id, question) for question in question_qs])
    sorted_questions = [questions[id] for id in session_question_ids_list]
    return sorted_questions


@login_required
@check_auth
@require_http_methods(['GET'])
def make_review_flg_ajax(request):
    """2つのフラグの作成
    1. list_review_flg
    2. question_id_review_flg
    """
    if not request.headers.get('x-requested-with'):
        raise PermissionDenied()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        review_flg = request.GET.get('review_flg')

        if review_flg == 'list_review_flg':
            if not 'list_review_flg' in request.session:
                request.session['list_review_flg'] = True
        elif review_flg == 'question_id_review_flg':
            if not 'question_id_review_flg' in request.session:
                request.session['question_id_review_flg'] = True
        else:
            raise RuntimeError()

        return JsonResponse(data={'success': 'ajax success!',})


@login_required
@check_auth
@require_http_methods(['GET'])
def back_to_last_page(request, question_id):
    """メイン処理2つ
    1. practice_finish_confirm_sessionをFalse
    2. 302でラストページへ
    """
    # 指定のbuttonのgetからか確認
    if not 'back_button' in request.GET:
        raise Http404()
    # 正しいquestion_idか確認
    if not re.search(r'j(\d{1,6})', question_id):
        raise RuntimeError('invalid')

    _check_form_and_url_session(request)

    # 1. practice_finish_confirm_sessionをFalse
    if 'practice_finish_confirm_session' in request.session:
        request.session['practice_finish_confirm_session'] = False

    # 2. question_idからラストページを生成
    last_page_url = request.session.get('url'+question_id)

    return HttpResponseRedirect(last_page_url)


def _check_paging(request):
    """ページングが存在するページ専用
    ページングのページチェックと1ページ目の設置
    """
    get_page_num_form = GetPageNumForm(request.GET)
    # form側にpage=1を仕込んでおく
    if not get_page_num_form.is_valid():
        raise Http404()
    if get_page_num_form.is_valid():
        page_num = get_page_num_form.cleaned_data['page']
    return page_num


@login_required
@check_auth
@require_http_methods(['GET', 'POST'])
def practice(request, get_params):
    """練習モード"""
    _check_form_and_url_session(request)

    # 1. 最初のページングバリデーション
    page_num = _check_paging(request)

    # 2. practice_fnish_confirm_sessionがTrueは、practice_finish_confirmを訪れた時にflgをTrueにしている
    # つまりpractice_finish_confirmから来たことを意味している
    # 結果、「もどる」ボタンが表示されない
    practice_finish_confirm_session = False
    if 'practice_finish_confirm_session' in request.session:
        if request.session['practice_finish_confirm_session'] is False:
            pass
        else:
            # もしくは、request.session がfalseの時の条件も書く
            practice_finish_confirm_session = True

    # 3. sessionでquestion_ids_listを保持
    # 初回get時にquestion_ids_listをセッションに保存しておく
    if not 'session_question_ids_list' in request.session:
        # getパラメータを分解してformの取得状態に戻す
        target, chapter, answers = _create_select_question_form_params(get_params)
        # questionのクエリーセットを生成
        question_qs = _create_questions(request=request,
                                        target=target,
                                        chapter=chapter,
                                        answers=answers)
        # 対象のquestionのidのみを取得してリストに格納
        question_ids_list = [question.question_id for question in question_qs]
        request.session['session_question_ids_list'] = question_ids_list
        # 未解答とミスに再挑戦してきた時
        if 'rechallenge_question_ids_list' in request.session:
            question_ids_list = request.session['rechallenge_question_ids_list']
            request.session['session_question_ids_list'] = question_ids_list
            del request.session['rechallenge_question_ids_list']

    # session読み込み
    session_question_ids_list = request.session['session_question_ids_list']


    # 4. 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)


    # 5. 取得したquestion_ids_listからrecordを取得
    record_qs = Record.objects.filter(user_id=request.user.id,
                            question_id__in=session_question_ids_list)
    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    # 6. questionとrecordを合体して辞書型オブジェクトをリストに格納
    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'textbook_chapter': question.textbook_chapter,
            'question_title': question.question_title,
            'sub_question_title': question.sub_question_title,
            'question_type': question.question_type,
            'question_img': question.question_img,
            'choice_a': question.choice_a,
            'choice_b': question.choice_b,
            'choice_c': question.choice_c,
            'choice_d': question.choice_d,
            'correct_answer': question.correct_answer,
            'commentary': question.commentary,
            'record': record_dict.get(question.question_id, None)
        }
        question_info.append(question_info_dict)


    # 7. (6.を使って)ページング処理
    question_info_page = _make_paginator(page_num=page_num,
                                        question_qs=question_info,
                                        number_of_display=1)
    # そもそもqsの問題数がない場合はindexに返す
    if not question_info_page:
        return HttpResponseRedirect(reverse('jrfoodadv:index'))
    # qsの問題数がきちんと存在する場合はid生成
    elif question_info_page:
        question_id = question_info_page[0]['question_id']


    # 8. formにセッションを保存する
    if not 'form'+question_id in request.session:
        form = SelectAnswerForm(question_id, request.GET)
    else:
        form = SelectAnswerForm(question_id, request.session.get('form'+question_id))


    # 9. urlをセッションに保存しておく
    protocol = '://'
    if not 'url'+question_id in request.session:
        url =  '%s%s%s%s%s%s' % (request.scheme,
                                protocol,
                                request.get_host(),
                                request.path.replace('?', '%3F'),
                                '?page=',
                                str(page_num))
        request.session['url'+question_id] = url


    if request.method == 'POST':
        form = SelectAnswerForm(question_id, request.POST)
        if form.is_valid():
            select_answer = form.cleaned_data['select_answer']

            # formにsessionを保存
            request.session['form'+question_id] = request.POST

            # 次の画面遷移先作成
            get_params = request.path.replace('?', '%3F')

            # ページ番号作成
            page_param = request.GET.urlencode()
            if not request.GET.urlencode():
                page_param = 'page=1'

            # 1. session_question_id_review_flgがある場合
            # →　practice_finish_confirm/のquestion_idのaタグから来た場合
            if 'question_id_review_flg' in request.session:
                return HttpResponseRedirect(reverse('jrfoodadv:practice_finish_confirm'))

            # 2. list_review_flgがある場合
            # practice_finish_confirmの「未解答の問題を見直す」から飛んできた時
            # list_review_flgがある時に発動
            # 未解答の問題を解答した際には、次の未解答の問題番号へのURLリンクを生成する
            if 'list_review_flg' in request.session:
                if request.session['form'+question_id]:
                    # ids_listのn番目からスタートさせて不要なforを避ける
                    page_num = session_question_ids_list.index(question_id)
                    for session_question_id in session_question_ids_list:
                        # session_question_ids_listの数よりnumが大きくならなければ続く
                        if page_num < len(session_question_ids_list):
                            # 最後のページならばnext_pageはpractice_finish_confirmへ302
                            if page_num+1 == len(session_question_ids_list):
                                return HttpResponseRedirect(
                                    reverse('jrfoodadv:practice_finish_confirm'))

                            # 次のページのform_sessionを用意
                            next_session_question_id= session_question_ids_list[page_num+1]
                            form_dict = request.session.get('form'+next_session_question_id)

                            # formのsessionがあることが前提
                            if form_dict:
                                # 次のページのform_sessionが解答済の時->loopに+1
                                # if 'select_answer' in form_dict and form_dict['select_answer']:
                                if 'select_answer' in form_dict:
                                    # 未回答:select_answerのkeyはあるけど、valueは''の時
                                    if not form_dict['select_answer']:
                                        url = request.session['url'+next_session_question_id]
                                        return HttpResponseRedirect(url)
                                    # 回答済みの時
                                    page_num += 1
                                # 未回答:'select_answer'がない時
                                elif not 'select_answer' in form_dict:
                                    url = request.session['url'+next_session_question_id]
                                    return HttpResponseRedirect(url)
                                # ありえないが例外
                                else:
                                    raise RuntimeError()
                            # ありえないが例外
                            else:
                                raise RuntimeError('form_dictがありません')
                        else:
                            # page_num > len(session_question_ids_list)
                            pass

            # 3. 最終ページなら画面遷移させる
            list_page_param = page_param.split('=')
            current_page_num = int(list_page_param[1])
            if len(session_question_ids_list) == current_page_num:
                return HttpResponseRedirect(reverse('jrfoodadv:practice_finish_confirm'))

            # 4. 通常の画面遷移:最終ページとreview_flgがない以外はnext_pageのurl作成
            else:
                list_page_param[1] = str(current_page_num + 1)
                page_params = '?' + ('='.join(list_page_param))
                url = '%s%s%s%s%s' % (
                    request.scheme,
                    protocol,
                    request.get_host(),
                    get_params,
                    page_params
                )
                return HttpResponseRedirect(url)

    context = {
        'question_page': question_info_page,
        'form': form,
        'practice_finish_confirm_session': practice_finish_confirm_session,
    }
    return render(request, 'jrfoodadv/practice/practice.html', context)


def _save_memo(user_id, question_id, memo):
    """メモの保存
    idなし→新規保存
    idあり→更新
    """
    record_qs = Record.objects.filter(question_id=question_id,
                                    user_id=user_id,)
    if not record_qs: # 新規
        memo_record = Record(question_id=question_id,
                                user_id=user_id,
                                memo=memo,)
    elif record_qs: # 更新
        memo_record = record_qs[0]
        memo_record.memo = memo
    else:
        raise RuntimeError()



@login_required
@check_auth
@require_http_methods(['POST'])
def memo_ajax(request):
    """メモの保存"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_id = request.user.id
        question_id = request.POST.get('question_id')
        memo = request.POST.get('memo')

        # Formで扱いたいが。
        if not validator.validate_emoji(memo):
            data = {
                'memo' : False,
                'message': FormMessages.CANT_USE_EMOJI,}
            return JsonResponse(data)

        _save_memo(user_id=user_id,
                    question_id=question_id,
                    memo=memo)

        data = {
            'memo': bool(memo), # True
        }
        return JsonResponse(data=data)


def _save_favorite(user_id, question_id):
    """お気に入りの登録
    idなし→新規登録
    idあり→真偽判定の後に反転
    """
    record_qs = Record.objects.filter(question_id=question_id,
                                    user_id=user_id,)
    if not record_qs: # 新規
        favorite_record = Record(question_id=question_id,
                                    user_id = user_id,
                                    favorite = True,)

    elif record_qs: # 真偽判定
        favorite_record = record_qs[0]
        if favorite_record.favorite is True:
            favorite_record.favorite = False
        elif favorite_record.favorite is False:
            favorite_record.favorite = True
        else:
            raise RuntimeError()

    return favorite_record.favorite # True or False


@login_required
@check_auth
@require_http_methods(['POST'])
def favorite_ajax(request):
    """お気に入り登録"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_id = request.user.id
        question_id = request.POST.get('question_id')
        record_favorite = _save_favorite(user_id=user_id,
                                            question_id=question_id)
        data = {
            'favorite': record_favorite,
        }
        return JsonResponse(data=data)


def _save_later(user_id, question_id):
    """あとでやるの登録
    idなし→新規登録
    idあり→真偽判定の後に反転
    """
    record_qs = Record.objects.filter(question_id=question_id,
                                    user_id=user_id,)
    if not record_qs: # 新規
        later_record = Record(question_id=question_id,
                                user_id = user_id,
                                later = True,)

    elif record_qs: # 真偽判定
        later_record = record_qs[0]
        if later_record.later is True:
            later_record.later = False
        elif later_record.later is False:
            later_record.later = True
        else:
            raise RuntimeError()

    return later_record.later # True or False


@login_required
@check_auth
@require_http_methods(['POST'])
def later_ajax(request):
    """お気に入り登録"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_id = request.user.id
        question_id = request.POST.get('question_id')
        record_later = _save_later(user_id=user_id,
                                            question_id=question_id)
        data = {
            'later': record_later,
        }
        return JsonResponse(data=data)


def _answer_result(question_id, select_answer):
    """正誤判断"""
    question_qs = JrFoodLabelingAdviseQuestion.objects.get(question_id=question_id)
    if select_answer == '':
        answer_result = AnswerResult.UNANSWERED # 未解答 0
    elif question_qs.correct_answer != select_answer:
        answer_result = AnswerResult.INCORRECT # 不正解 1
    elif question_qs.correct_answer == select_answer:
        answer_result = AnswerResult.CORRECT # 正解 2
    else:
        raise RuntimeError('invalid')
    return answer_result


def _check_form_and_url_session(request):
    """ もし /practice/result からbackして戻ってきた場合は403で表示させない。
    正規表現でsession中のformとurlを探してなければ404にする。
    基本的にはformとurlは2つで1つ。
    このページの後のpractice/resultで、session_question_ids_listを除く、formとurlは削除を実行している。
    """
    url_indicator = re.compile('url'+r'j(\d{1,6})')
    form_indicator = re.compile('form'+r'j(\d{1,6})')

    # リスト内の文字列が正規表現に一致しない(存在しない=form/urlのsessionが削除されている)場合
    if 'session_question_ids_list' in request.session:
        if not [session[0] for session in request.session.items() \
                if url_indicator.match(session[0])]:
            if not [session[0] for session in request.session.items() \
                if form_indicator.match(session[0])]:
                raise Http404()


def _check_form_session(request):
    """この処理が抜けると500が起きるので作成
    practice_finish_confirm でしか使用していない
    500の発生手順
    1. 演習結果のページから、「未解答とミスに再挑戦」をクリック
    2. practice/ のurlにアクセス(->ここでurl sessionが作成される)した状態からback
    3. 演習結果のページに戻っているので、そこから更にback
    4. 500error
    """
    url_indicator = re.compile('url'+r'j(\d{1,6})')
    form_indicator = re.compile('form'+r'j(\d{1,6})')
    if [session[0] for session in request.session.items() \
            if url_indicator.match(session[0])]:
        if not [session[0] for session in request.session.items() \
            if form_indicator.match(session[0])]:
                raise Http404()


def _make_question_content(question):
    """ qsの単体question_contentsを渡すとquestion_contentsを作成する
    ・formsからその日の選択肢の並びを作成するロジックをimportして利用
    """
    # formsにあるロジックを使用するため準備から
    choices = []
    choices.append(('choice_a', question.choice_a))
    choices.append(('choice_b', question.choice_b))
    choices.append(('choice_c', question.choice_c))
    # choice_dは問題によって存在しないものがあるので存在しなければlistに追加しない
    if question.choice_d:
        choices.append(('choice_d', question.choice_d))
    choices_daily = _make_choice_combination(choices)

    str_choices = ''
    for choice in choices_daily:
        str_choices += choice[1]

    question_contents = '%s%s%s' % (question.question_title,
                                    question.sub_question_title,
                                    str_choices)
    truncatechars = 80
    if len(question_contents) < truncatechars:
        return question_contents[:truncatechars]
    else:
        return question_contents[:truncatechars] + '…'


def _make_question_info(request, sorted_questions):
    """終了直前の確認でのquestion_infoの作成"""
    question_info = []
    unanswerd_flg = False
    first_unanswerd_url = ''
    loop_count = 1
    first_page_url = ''
    for question in sorted_questions:
        # 1. urlの作成
        url_dict = request.session.get('url'+question.question_id)

        if url_dict:
            if not first_page_url:
                first_page_url = url_dict
        elif url_dict is None:
            page_url= first_page_url.split('?page=')
            page_num = str(loop_count)
            url_dict = page_url[0]+'?page='+page_num

        #2. form(解答番号)の作成
        form_dict = request.session.get('form'+question.question_id)

        # 未解答の問題がある場合のフラグ
        if form_dict:
            # not form_dict['select_answer']-> select_answerのkeyはあるけど、valueは''の時
            if not 'select_answer' in form_dict or \
                not form_dict['select_answer'] or \
                    form_dict is None:
                form_dict['select_answer'] = ''
                # 未解答の問題一覧
                unanswerd_flg = True
                # practice_finish_confirmで「未解答の問題を見直す」のurl
                if first_unanswerd_url == '':
                    first_unanswerd_url = url_dict
            select_info_dict  = {
                'question_id': question.question_id,
                'question_content': _make_question_content(question),
                'select_answer': form_dict['select_answer'],
                'url': url_dict,
            }
            question_info.append(select_info_dict)

        elif not form_dict:
            # URLの直入力(?page=xxx)してきた時の処理
            unanswerd_flg = True
            select_info_dict  = {
                'question_id': question.question_id,
                'question_content': _make_question_content(question),
                'select_answer': '',
                'url': url_dict,
            }
            first_unanswerd_url = url_dict
            question_info.append(select_info_dict)

        else:
            raise RuntimeError()

        # ラストページを取得
        if loop_count == len(sorted_questions):
            last_page_question_id = select_info_dict['question_id']

        loop_count += 1

    return unanswerd_flg, first_unanswerd_url, last_page_question_id, question_info


def _save_record(request, question_info):
    """終了直前の確認でのpost時のsave"""
    record_qs = Record.objects.filter(user_id=request.user.id)
    record_qs_ids = [record.question_id for record in record_qs] 
    for question in question_info:
        # 初めて(未出題)の問題
        if question['question_id'] not in record_qs_ids:
            # 以下が想定されるのは、上で想定した question['question_id'] not in record_qs_ids とは別
            # ここのfor文を回す間に新しくRecordを作成した場合にexists()チェックをせずに生成してしまうので
            # ここでわざわざexists()チェックを入れている。
            if not Record.objects.filter(user_id=request.user.id,
                                            question_id=question['question_id']).exists():
                new_record = Record(question_id=question['question_id'],
                                    user_id=request.user.id,
                                    current_answer = _answer_result(question_id=question['question_id'],
                                                                    select_answer=question['select_answer']),
                                    current_choice = question['select_answer'],
                                    first_answer =_answer_result(question_id=question['question_id'],
                                                                    select_answer=question['select_answer']),
                                    saved_at = make_aware(datetime.datetime.now()),)

            else:
                # 過去実施済みの場合
                # もしくはfor文で新しいRecordができたケース
                # 以下のコードはこの先の # 過去実施済みの場合 以下と同じコード
                get_record = record_qs.get(question_id=question['question_id'])
                get_record.question_id = question['question_id']
                get_record.user_id = request.user.id
                get_record.current_answer =_answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                get_record.current_choice = question['select_answer']
                get_record.saved_at = make_aware(datetime.datetime.now())
                if not get_record.first_answer:
                    get_record.first_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                elif not get_record.second_answer:
                    get_record.second_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                elif not get_record.third_answer:
                    get_record.third_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                elif not get_record.fourth_answer:
                    get_record.fourth_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                elif not get_record.fifth_answer:
                    get_record.fifth_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                elif get_record.fifth_answer:
                    get_record.first_answer = get_record.second_answer
                    get_record.second_answer = get_record.third_answer
                    get_record.third_answer = get_record.fourth_answer
                    get_record.fourth_answer = get_record.fifth_answer
                    get_record.fifth_answer = _answer_result(question_id=question['question_id'],
                                                            select_answer=question['select_answer'])
                else:
                    raise RuntimeError()


        # 過去実施済みの場合
        elif question['question_id'] in record_qs_ids:
            get_record = record_qs.get(question_id=question['question_id'])
            get_record.question_id = question['question_id']
            get_record.user_id = request.user.id
            get_record.current_answer =_answer_result(question_id=question['question_id'],
                                                    select_answer=question['select_answer'])
            get_record.current_choice = question['select_answer']
            get_record.saved_at = make_aware(datetime.datetime.now())
            if not get_record.first_answer:
                get_record.first_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            elif not get_record.second_answer:
                get_record.second_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            elif not get_record.third_answer:
                get_record.third_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            elif not get_record.fourth_answer:
                get_record.fourth_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            elif not get_record.fifth_answer:
                get_record.fifth_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            elif get_record.fifth_answer:
                get_record.first_answer = get_record.second_answer
                get_record.second_answer = get_record.third_answer
                get_record.third_answer = get_record.fourth_answer
                get_record.fourth_answer = get_record.fifth_answer
                get_record.fifth_answer = _answer_result(question_id=question['question_id'],
                                                        select_answer=question['select_answer'])
            else:
                raise RuntimeError()

        else:
            raise RuntimeError()


@login_required
@check_auth
@require_http_methods(['GET', 'POST'])
def practice_finish_confirm(request):
    """練習モード終了直前の確認"""
    _check_form_and_url_session(request)
    _check_form_session(request)
    _del_review_flg_session(request)
    if not 'practice_finish_confirm_session' in request.session:
        request.session['practice_finish_confirm_session'] = True

    # 最初のページングバリデーション
    page_num = _check_paging(request)

    # セッションsession_question_ids_listの読み込み
    # そもそもなければ404
    if not 'session_question_ids_list' in request.session:
        raise Http404()
    else:
        session_question_ids_list = request.session['session_question_ids_list']

    # 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)
    unanswerd_flg, first_unanswerd_url, last_page_question_id, question_info \
        = _make_question_info(request=request,
                                sorted_questions=sorted_questions)

    if request.method == 'POST':
        _save_record(request=request,
                        question_info=question_info)
        return HttpResponseRedirect(reverse('jrfoodadv:practice_result'))

    # question_infoから、select_answerがFalseのみを取り出してページング準備
    select_answer_is_false = []
    for question in question_info:
        if not question['select_answer']:
            select_answer_is_false.append(question)
    question_info_page = _make_paginator(page_num=page_num,
                                        question_qs=select_answer_is_false)

    # ページ番号を取得して、question_info_pageに保存する
    for question in question_info_page:
        page_num = re.findall(r'page=(\d+)', question['url'])
        question['page_num'] = page_num[0]

    context = {
        'question_page' : question_info_page,
        'unanswerd_flg': unanswerd_flg,
        'first_unanswerd_url': first_unanswerd_url,
        'last_page_question_id': last_page_question_id,
    }
    return render(request, 'jrfoodadv/practice/practice_finish_confirm.html', context)

@login_required
@check_auth
@require_http_methods(['GET'])
def practice_result(request):
    """演習結果"""
    # 無料会員か有料会員か確認
    plan = _check_plan(request)

    # そもそもsession_question_ids_listセッションがなければ403
    # 例えばブラウザで2つの画面を開いていて削除フラグがある画面を踏んだ時を想定
    if not 'session_question_ids_list' in request.session:
        raise PermissionDenied()

    # formのセッションのみ消す
    _del_session(request=request,
                    except_ids_list=True,
                    except_url_param=True,)

    # ページングバリデーション
    page_num = _check_paging(request)

    # セッションに残っているリスト抽出
    session_question_ids_list = request.session['session_question_ids_list']
    record_qs = Record.objects.filter(user_id=request.user.id,
                                    question_id__in=session_question_ids_list)

    # 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)

    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    # questionとrecordを合体して辞書型オブジェクトをリストに格納
    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'question_content': _make_question_content(question),
            'textbook_chapter': question.textbook_chapter_as_str(),
            'current_answer': record_dict.get(question.question_id).current_answer,
            'memo': record_dict.get(question.question_id).memo,
            'favorite': record_dict.get(question.question_id).favorite,
        }
        question_info.append(question_info_dict)

    # 正解総数を取り出す
    total_number_of_correct_answers_list = [question['current_answer'] \
                                            for question in question_info \
                                            if question['current_answer'] == AnswerResult.CORRECT]
    total_number_of_correct_answers = len(total_number_of_correct_answers_list)

    # 1ページに表示するデータの数
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=question_info)

    # 全問正解なら未解答とミスに再挑戦ボタンを表示する必要はない
    rechallenge_mistakes_btn = False
    if len(question_info_page) != total_number_of_correct_answers:
        rechallenge_mistakes_btn = True

    context = {
        'total_number_of_correct_answers': total_number_of_correct_answers,
        'count_all_questions': len(question_info),
        'question_page': question_info_page,
        'rechallenge_mistakes': rechallenge_mistakes_btn,
        'plan': plan,
    }
    return render(request, 'jrfoodadv/practice/result.html', context)


def _integrate_question_and_record(get_question, get_record):
    """questionとrecordを結合して辞書型で返す
    """
    question_info_dict = {
        'question_id': get_question.question_id,
        'textbook_chapter': get_question.textbook_chapter,
        'textbook_chapter_as_str': get_question.textbook_chapter_as_str(),
        'question_title': get_question.question_title,
        'sub_question_title': get_question.sub_question_title,
        'question_type': get_question.question_type,
        'question_img': get_question.question_img,
        'choice_a': get_question.choice_a,
        'choice_b': get_question.choice_b,
        'choice_c': get_question.choice_c,
        'choice_d': get_question.choice_d,
        'correct_answer': get_question.correct_answer,
        'commentary': get_question.commentary,
        'favorite': get_record.favorite,
        'memo': get_record.memo,
        'current_answer': get_record.current_answer,
        'current_answer_as_str': get_record.current_answer_as_str(),
        'current_choice': get_record.current_choice,
        'first_answer': get_record.first_answer,
        'second_answer': get_record.second_answer,
        'third_answer': get_record.third_answer,
        'fourth_answer': get_record.fourth_answer,
        'fifth_answer': get_record.fifth_answer,
        'saved_at': get_record.saved_at,
    }
    return question_info_dict


@login_required
@check_auth
@require_http_methods(['GET'])
def practice_result_individual(request, question_id):
    """演習結果個別"""
    # get_object_or_404 で値を1件だけ取得する
    get_question = get_object_or_404(JrFoodLabelingAdviseQuestion, question_id=question_id)
    get_record = get_object_or_404(Record, user_id=request.user.id, question_id=question_id, )

    # 結合
    question_info_dict = _integrate_question_and_record(get_question=get_question,
                                                        get_record=get_record)

    form = SelectAnswerForm(question_id, request.GET)

    context = {
        'question': question_info_dict,
        'form': form,
        'model_answer_result': AnswerResult,
    }
    return render(request, 'jrfoodadv/practice/result_individual.html', context)


def _create_test_questions(request):
    question_qs = JrFoodLabelingAdviseQuestion.objects.all()
    record_qs = Record.objects.filter(user_id=request.user.id)
    ANSWERS = 75

    # 未出題・ミスを優先表示にチェックがある場合
    if 'unquestioned_and_mistakes_flg' in request.session:
        # 未解答・正答済みをfilter
        record_qs = record_qs.filter(current_answer__in=[AnswerResult.UNANSWERED,
                                                                    AnswerResult.CORRECT])
        # 未解答・正答済みのid一覧をexclude(排除)して、未出題・ミスを抽出
        record_question_ids = [record.question_id for record in record_qs]
        question_qs = question_qs.exclude(
            question_id__in = record_question_ids)

        # 75より少ない時はランダムにqsを取得して後方に連結する
        if question_qs.count() < ANSWERS:
            # 75より少ないidを不足するときに、排除すべきid
            excluded_ids = [record.question_id for record in question_qs]
            # sufficient_numberは足りない数
            sufficient_number = ANSWERS - question_qs.count()

            # 足りない不足分の問題を抽出する
            # excluded_idsを先に排除。排除されたidsは最後に挿入する
            # order_by('?')でランダムで75問を抽出
            sufficient_qs = JrFoodLabelingAdviseQuestion.objects\
                                .exclude(question_id__in = excluded_ids)\
                                .order_by('?')[:sufficient_number] 
            sufficient_ids_list = [question.question_id for question in sufficient_qs]

            # 元のquestion_qsをランダムに並び替える
            question_qs = question_qs.order_by('?')[:ANSWERS]
            question_ids_list = [question.question_id for question in question_qs]

            # extendで追加する
            question_ids_list.extend(sufficient_ids_list)
            # ちゃんと75問か確認
            if len(question_ids_list) != ANSWERS:
                raise RuntimeError('Not enough questions')
            return question_ids_list

    question_qs = question_qs.order_by('?')[:ANSWERS]
    question_ids_list = [question.question_id for question in question_qs]
    return question_ids_list


def _make_strftime_time_left(request):
    get_time_left = get_object_or_404(TimeLeft, user_id=request.user.id)
    strftime_time_left = get_time_left.time_left_at.strftime('%B %d,%Y %H:%M:%S')
    return strftime_time_left

@login_required
@check_auth
@require_http_methods(['GET', 'POST'])
def practice_test(request):
    """模擬試験"""
    _check_form_and_url_session(request)
    get_object_or_404(TimeLeft, user_id=request.user.id)


    # 1. 最初のページングバリデーション
    page_num = _check_paging(request)

    # 2. practice_fnish_confirm_sessionがTrueは、practice_finish_confirmを訪れた時にflgをTrueにしている
    # つまりpractice_finish_confirmから来たことを意味している
    # 結果、「もどる」ボタンが表示されない
    practice_finish_confirm_session = False
    if 'practice_finish_confirm_session' in request.session:
        if request.session['practice_finish_confirm_session'] is False:
            pass
        else:
            # もしくは、request.session がfalseの時の条件も書く
            practice_finish_confirm_session = True

    # 3. sessionでquestion_ids_listを保持
    # 初回get時にquestion_ids_listをセッションに保存しておく
    if not 'session_question_ids_list' in request.session:
        question_ids_list = _create_test_questions(request)
        # sessionに保存
        request.session['session_question_ids_list'] = question_ids_list

        # recordが存在する場合、laterをFalseに一括更新する
        record_qs = Record.objects.filter(user_id=request.user.id,
                                            question_id__in=question_ids_list)
        for record in record_qs:
            record.later = False

    # session読み込み
    session_question_ids_list = request.session['session_question_ids_list']

    # 4. 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)

    # 5. 取得したquestion_ids_listからrecordを取得
    record_qs = Record.objects.filter(user_id=request.user.id,
                            question_id__in=session_question_ids_list)
    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    # 6. questionとrecordを合体して辞書型オブジェクトをリストに格納
    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'textbook_chapter': question.textbook_chapter,
            'question_title': question.question_title,
            'sub_question_title': question.sub_question_title,
            'question_type': question.question_type,
            'question_img': question.question_img,
            'choice_a': question.choice_a,
            'choice_b': question.choice_b,
            'choice_c': question.choice_c,
            'choice_d': question.choice_d,
            'correct_answer': question.correct_answer,
            'commentary': question.commentary,
            'record': record_dict.get(question.question_id, None)
        }
        question_info.append(question_info_dict)

    # 7. (6.を使って)ページング処理
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=question_info,
                                            number_of_display=1)
    question_id = question_info_page[0]['question_id']

    # 8. formにセッションを保存
    if not 'form'+question_id in request.session:
        form = SelectAnswerForm(question_id, request.GET)
    else:
        form = SelectAnswerForm(question_id, request.session.get('form'+question_id))

    # 9. urlをセッションに保存しておく
    protocol = '://'
    if not 'url'+question_id in request.session:
        url =  '%s%s%s%s%s%s' % (request.scheme,
                                protocol,
                                request.get_host(),
                                request.path,
                                '?page=',
                                str(page_num))
        request.session['url'+question_id] = url


    if request.method == 'POST':
        form = SelectAnswerForm(question_id, request.POST)
        if form.is_valid():
            select_answer = form.cleaned_data['select_answer']

            # formにsessionを保存
            request.session['form'+question_id] = request.POST

            # ページ番号作成
            page_param = request.GET.urlencode()
            if not request.GET.urlencode():
                page_param = 'page=1'

            # 1. session_question_id_review_flgがある場合
            # →　practice_finish_confirm/のquestion_idのaタグから来た場合
            if 'question_id_review_flg' in request.session:
                return HttpResponseRedirect(reverse('jrfoodadv:practice_test_finish_confirm'))

            # 2. list_review_flgがある場合
            # practice_finish_confirmの「未解答の問題を見直す」から飛んできた時
            # list_review_flgがある時に発動
            # 未解答の問題を解答した際には、次の未解答の問題番号へのURLリンクを生成する
            if 'list_review_flg' in request.session:
                if request.session['form'+question_id]:
                    # ids_listのn番目からスタートさせて不要なforを避ける
                    page_num = session_question_ids_list.index(question_id)
                    for session_question_id in session_question_ids_list:
                        # session_question_ids_listの数よりnumが大きくならなければ続く
                        if page_num < len(session_question_ids_list):
                            # 最後のページならばnext_pageはpractice_finish_confirmへ302
                            if page_num+1 == len(session_question_ids_list):
                                return HttpResponseRedirect(
                                    reverse('jrfoodadv:practice_test_finish_confirm'))

                            # 次のページのform_sessionを用意
                            next_session_question_id= session_question_ids_list[page_num+1]
                            form_dict = request.session.get('form'+next_session_question_id)

                            # formのsessionがあることが前提
                            if form_dict:
                                # 次のページのform_sessionが解答済の時->loopに+1
                                # if 'select_answer' in form_dict and form_dict['select_answer']:
                                if 'select_answer' in form_dict:
                                    # 未回答:select_answerのkeyはあるけど、valueは''の時
                                    if not form_dict['select_answer']:
                                        url = request.session['url'+next_session_question_id]
                                        return HttpResponseRedirect(url)
                                    # 回答済みの時
                                    page_num += 1
                                # 未回答:'select_answer'がない時
                                elif not 'select_answer' in form_dict:
                                    url = request.session['url'+next_session_question_id]
                                    return HttpResponseRedirect(url)
                                # ありえないが例外
                                else:
                                    raise RuntimeError()
                            # ありえないが例外
                            else:
                                raise RuntimeError('form_dictがありません')
                        else:
                            # page_num > len(session_question_ids_list)
                            pass

            # 3. 最終ページなら画面遷移させる
            list_page_param = page_param.split('=')
            current_page_num = int(list_page_param[1])
            if len(session_question_ids_list) == current_page_num:
                return HttpResponseRedirect(reverse('jrfoodadv:practice_test_finish_confirm'))

            # 4. 通常の画面遷移:最終ページとreview_flgがない以外はnext_pageのurl作成
            else:
                list_page_param[1] = str(current_page_num + 1)
                page_params = '?' + ('='.join(list_page_param))
                url = '%s%s%s%s%s' % (
                    request.scheme,
                    protocol,
                    request.get_host(),
                    request.path,
                    page_params,
                )
                return HttpResponseRedirect(url)

    context = {
        'question_page': question_info_page,
        'form': form,
        'time_left': _make_strftime_time_left(request),
        'practice_finish_confirm_session': practice_finish_confirm_session,
    }
    return render(request, 'jrfoodadv/practice_test/practice_test.html', context)


@login_required
@check_auth
@require_http_methods(['GET', 'POST'])
def practice_test_finish_confirm(request):
    """模擬試験終了直前の確認
    def practice_finish_confirmとロジックもコードも同じ
    """
    _check_form_and_url_session(request)
    _check_form_session(request)
    _del_review_flg_session(request)
    if not 'practice_finish_confirm_session' in request.session:
        request.session['practice_finish_confirm_session'] = True

    # 最初のページングバリデーション
    page_num = _check_paging(request)

    # セッションsession_question_ids_listの読み込み
    # そもそもなければ404
    if not 'session_question_ids_list' in request.session:
        raise Http404()
    else:
        session_question_ids_list = request.session['session_question_ids_list']

    # 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)
    unanswerd_flg, first_unanswerd_url, last_page_question_id, question_info \
        = _make_question_info(request=request,
                                sorted_questions=sorted_questions)
    
    if request.method == 'POST':
        _save_record(request=request,
                        question_info=question_info)
        return HttpResponseRedirect(reverse('jrfoodadv:practice_result'))

    # question_infoから、select_answerがFalseのみを取り出してページング準備
    select_answer_is_false = []
    for question in question_info:
        if not question['select_answer']:
            select_answer_is_false.append(question)
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=select_answer_is_false)

    # ページ番号を取得して、question_info_pageに保存する
    for question in question_info_page:
        page_num = re.findall(r'page=(\d+)', question['url'])
        question['page_num'] = page_num[0]

    context = {
        'question_page' : question_info_page,
        'unanswerd_flg': unanswerd_flg,
        'first_unanswerd_url': first_unanswerd_url,
        'last_page_question_id': last_page_question_id,
        'time_left': _make_strftime_time_left(request),
    }
    return render(request, 'jrfoodadv/practice_test/practice_test_finish_confirm.html', context)


def forced_termination_ajax(request):
    """カウントダウンタイマー0の時の強制終了"""
    if not request.headers.get('x-requested-with'):
        raise PermissionDenied()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # session読み込み
        session_question_ids_list = request.session['session_question_ids_list']
        # 並びをsession_question_ids_listで任意順序にし直して返す
        sorted_questions = _arbitrary_sequence(session_question_ids_list)
        unanswerd_flg, first_unanswerd_url, last_page_question_id, question_info \
            = _make_question_info(request, sorted_questions)

        if request.method == 'POST':
            _save_record(request=request,
                            question_info=question_info)
            return JsonResponse(data={'url': reverse('jrfoodadv:practice_result')})

    else:
        raise RuntimeError()


@login_required
@check_auth
@require_http_methods(['GET'])
def answer_status(request):
    """模擬試験中の解答状況
    """
    _check_form_and_url_session(request)
    get_object_or_404(TimeLeft, user_id=request.user.id)

    # 1. session読み込み
    if not 'session_question_ids_list' in request.session:
        # 直接 jrfoodadv/practice_test/answer_status を叩かれた時
        raise PermissionDenied()
    session_question_ids_list = request.session['session_question_ids_list']

    # 2. 並びをsession_question_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(session_question_ids_list)

    # 3. 全URLを取得する
    # _make_question_infoのquestion_infoにurlが格納されているのでquestion_info 変数だけ使用する
    unanswerd_flg, first_unanswerd_url, last_page_question_id, question_info \
        = _make_question_info(request=request,
                                sorted_questions=sorted_questions)
    # idに対応するurlを紐付けたdictを作成
    url_dict = {}
    for question in question_info:
        url_dict[question['question_id']] = question['url']

    # 4. 取得したquestion_ids_listからrecordを取得
    record_qs = Record.objects.filter(user_id=request.user.id,
                            question_id__in=session_question_ids_list)
    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    # 5. questionとrecordを合体して辞書型オブジェクトをリストに格納
    question_info = []
    for question in sorted_questions:
        # 解答済み判定
        # sessionのformの有無で判定
        form_dict = request.session.get('form'+question.question_id)
        answer = False
        if form_dict:
            if form_dict['select_answer']:
                # 解答済み
                answer = True
            elif not form_dict['select_answer']:
                # 問題に遭遇したが未解答
                answer = False
            else:
                raise RuntimeError()

        question_info_dict = {
            'question_id': question.question_id,
            'url': url_dict[question.question_id],
            'answer': answer, # 解答状況
            'record': record_dict.get(question.question_id, None)
        }
        question_info.append(question_info_dict)
    context = {
        'question_info': question_info,
        'time_left': _make_strftime_time_left(request),
    }
    return render(request, 'jrfoodadv/practice_test/answer_status.html', context)


def _make_query_param(target, chapter, answers):
    """urlクエリパラメーター作成"""
    get_params = []
    if target:
        for param in target:
            get_params.append('target=%s' % urllib.parse.quote(param))
    if chapter:
        for param in chapter:
            get_params.append('chapter=%s' % urllib.parse.quote(param))
    if answers:
        get_params.append('answers=%s' % int(answers))

    return '?' + '&'.join(get_params)


@login_required
@check_auth
@require_http_methods(['GET'])
def rechallenge_mistakes(request):
    """ミスに再挑戦へリダイレクトするパラメーター作成"""
    if not 'rechallenge_mistakes' in request.GET:
        raise Http404()

    # sessionリスト読み込む
    if 'session_question_ids_list' in request.session:
        session_question_ids_list = request.session['session_question_ids_list']
    else:
        raise Http404()

    # session_url_param読み込む
    if 'session_url_param' in request.session:
        session_url_param = request.session['session_url_param']
    else:
        raise Http404()

    # current_answerが未解答もしくはミスにマッチするものを取得
    record_qs = Record.objects.filter(question_id__in=session_question_ids_list,
                                        user_id=request.user.id)
    # 念の為、sessionに残っているlistの数と、それを利用して取得したqsの数がイコールであることを確認
    if len(session_question_ids_list) != record_qs.count():
        raise RuntimeError('not equal')
    rechallenge_question_ids_list = []
    for record in record_qs:
        if record.current_answer != AnswerResult.CORRECT:
            rechallenge_question_ids_list.append(record.question_id)

    # rechallenge_question_ids_listを用意
    request.session['rechallenge_question_ids_list'] = rechallenge_question_ids_list

    # パラメーター作成
    target, chapter, answers = _create_select_question_form_params(session_url_param)
    answers = len(rechallenge_question_ids_list)
    get_params = _make_query_param(target=target,
                                    chapter=chapter,
                                    answers=answers)

    # session_question_ids_listを削除
    del request.session['session_question_ids_list']
    # 新しいsession_url_paramを保存
    request.session['session_url_param'] = get_params

    return HttpResponseRedirect(reverse(
        'jrfoodadv:practice',
        args=(get_params,))
    )


def _make_search_query_param(page_num=1,
                            question_id=None,
                            chapter=None,
                            word=None,
                            target=None,
                            favorite=None,
                            memo=None):
    """search専用
    ページングパラメーターの作成
    """
    params = []
    if question_id:
        params.append('question_id=%s' % urllib.parse.quote(str(question_id)))
    if chapter:
        for chapter_num in chapter:
            params.append('chapter=%s' % urllib.parse.quote(chapter_num))
    if word:
        params.append('word=%s' % urllib.parse.quote(word))
    if target:
        for target_num in target:
            params.append('target=%s' % urllib.parse.quote(target_num))
    if favorite:
        # favoriteはリストで入ってくるので、処理はfavorite[0]となるので以下の書き方
        if str(SearchRecord.FAVORITE) in favorite:
            params.append('favorite=%s' % urllib.parse.quote(str(SearchRecord.FAVORITE)))
    if memo:
        # memoはリストで入ってくるので、処理はmemo[0]となるので以下の書き方
        if str(SearchRecord.MEMO):
            params.append('memo=%s' % urllib.parse.quote(str(SearchRecord.MEMO)))
    if page_num:
        params.append('page=%s' % urllib.parse.quote(str(page_num)))
    return '?' + '&'.join(params)


@login_required
@check_auth
@require_http_methods(['GET'])
def search(request):
    """検索
    検索結果も同じページで表示させる
    """
    question_info_page = None
    #　初回GET
    form = SearchQuestionForm(request.GET)
    # 最初のページングバリデーション
    page_num = _check_paging(request)

    # 無料会員か有料会員か確認
    plan = _check_plan(request)

    if form.is_valid():
        question_id = form.cleaned_data['question_id']
        chapter = form.cleaned_data['chapter']
        word = form.cleaned_data['word']
        target = form.cleaned_data['target']
        favorite = form.cleaned_data['favorite']
        memo = form.cleaned_data['memo']

        # 初回get
        # SearchQuestionFormではfield全てTrueなので、必然的にSearchQuestionFormはTrueになる。
        # なので値が全て空の初回は空のオブジェクトを返す
        input_list = [question_id, chapter, word, target, favorite, memo]
        true_count = 0
        for input_data in input_list:
            if input_data:
                true_count += 1
        if true_count == 0:
            # 全て空なら、空の要素を返す
            question_info = []

        # 検索実行時
        else:
            # HACK: SQLに書き直す
            question_qs = JrFoodLabelingAdviseQuestion.objects.all()
            record_qs = Record.objects.filter(user_id=request.user.id)
            if question_id:
                question_qs = question_qs.filter(question_id=question_id)
            if chapter:
                question_qs = question_qs.filter(textbook_chapter__in=chapter)
            if word:
                question_qs = question_qs.filter(
                    Q(question_title__contains=word)|
                    Q(choice_a__contains=word)|
                    Q(choice_b__contains=word)|
                    Q(choice_c__contains=word)|
                    Q(choice_d__contains=word)|
                    Q(commentary__contains=word),)

            if target:
                # 1. 未出題のみにチェック→レコードに存在する問題IDだけ排除
                # if str(SelectQuestions.UNQUESTIONED) == target[0]:
                if str(SelectQuestions.UNQUESTIONED) in target and \
                        not str(SelectQuestions.MISS) in target:
                    record_question_ids = [record.question_id for record in record_qs]
                    question_qs = question_qs.exclude(
                        question_id__in=record_question_ids)

                # 2. ミスのみにチェック→ミスだけ抽出して検索
                elif not str(SelectQuestions.UNQUESTIONED) in target and \
                        str(SelectQuestions.MISS) in target:
                    record_qs = record_qs.filter(current_answer=AnswerResult.INCORRECT)
                    record_question_ids = [record.question_id for record in record_qs]
                    question_qs = question_qs.filter(
                        question_id__in=record_question_ids)

                # 3. 未出題とミスの両方にチェック→レコードから「ミス」だけ抽出して全問題から排除
                # もしくは「未解答」と「正解」を抽出して全問題から排除
                elif str(SelectQuestions.UNQUESTIONED) in target and \
                    str(SelectQuestions.MISS) in target:
                    record_qs = record_qs.filter(current_answer__in=[AnswerResult.UNANSWERED,
                                                                        AnswerResult.CORRECT])
                    record_question_ids = [record.question_id for record in record_qs]
                    question_qs = question_qs.exclude(
                        question_id__in = record_question_ids)
                else:
                    RuntimeError('invalid')

            if favorite:
                record_qs = record_qs.filter(favorite=True)
                record_question_ids = [record.question_id for record in record_qs]
                question_qs = question_qs.filter(
                    question_id__in = record_question_ids)
            if memo:
                record_qs = record_qs.exclude(memo__exact='')
                record_question_ids = [record.question_id for record in record_qs]
                question_qs = question_qs.filter(
                    question_id__in = record_question_ids)

            # 0. リスト化
            question_ids_list = [question.question_id for question in question_qs]
            # 1. 並びをsession_question_ids_listで任意順序にし直して返す
            sorted_questions = _arbitrary_sequence(question_ids_list)
            # 2. 取得したquestion_ids_listからrecordを取得
            record_qs = Record.objects.filter(user_id=request.user.id,
                                    question_id__in=question_ids_list)
            record_dict = {}
            for question_record in record_qs:
                record_dict[question_record.question_id] = question_record
            # 3. questionとrecordを合体して辞書型オブジェクトをリストに格納
            question_info = []
            for question in sorted_questions:
                question_info_dict = {
                    'question_id': question.question_id,
                    'textbook_chapter': question.textbook_chapter_as_str(),
                    'question_content': _make_question_content(question),
                    'commentary': question.commentary,
                }
                question_info.append(question_info_dict)

            question_info_page = _make_paginator(page_num=page_num,
                                                    question_qs=question_info,)

    prev_page_href = _make_search_query_param(page_num=page_num-1,
                                                question_id=question_id,
                                                chapter=chapter,
                                                word=word,
                                                target=target,
                                                favorite=favorite,
                                                memo=memo)
    # page_numがTrueだと末尾に?page=が生成されるのでFalseにしておく
    current_page_href = _make_search_query_param(page_num=False,
                                                question_id=question_id,
                                                chapter=chapter,
                                                word=word,
                                                target=target,
                                                favorite=favorite,
                                                memo=memo)
    next_page_href = _make_search_query_param(page_num=page_num+1,
                                                question_id=question_id,
                                                chapter=chapter,
                                                word=word,
                                                target=target,
                                                favorite=favorite,
                                                memo=memo)
    context = {
        'form': form,
        'all_questions': len(question_info),
        'question_page': question_info_page,
        'prev_page_href': prev_page_href,
        'current_page_href': current_page_href,
        'next_page_href': next_page_href,
        'plan': plan
    }
    return render(request, 'jrfoodadv/search/search.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def search_question_id(request, question_id):
    """検索ID個別"""
    # get_object_or_404 で値を1件だけ取得する
    get_question = get_object_or_404(JrFoodLabelingAdviseQuestion, question_id=question_id)
    record_qs = Record.objects.filter(user_id=request.user.id)

    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    question_info_dict = {
        'question_id': get_question.question_id,
        'textbook_chapter': get_question.textbook_chapter,
        'textbook_chapter_as_str': get_question.textbook_chapter_as_str(),
        'question_title': get_question.question_title,
        'sub_question_title': get_question.sub_question_title,
        'question_type': get_question.question_type,
        'question_img': get_question.question_img,
        'choice_a': get_question.choice_a,
        'choice_b': get_question.choice_b,
        'choice_c': get_question.choice_c,
        'choice_d': get_question.choice_d,
        'correct_answer': get_question.correct_answer,
        'commentary': get_question.commentary,
        'record': record_dict.get(get_question.question_id, None),
    }

    form = SelectAnswerForm(question_id, request.GET)

    context = {
        'question': question_info_dict,
        'form': form,
    }
    return render(request, 'jrfoodadv/search/search_question_id.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def record_question_id(request, question_id):
    """履歴ID個別"""
    # get_object_or_404 で値を1件だけ取得する
    get_question = get_object_or_404(JrFoodLabelingAdviseQuestion, question_id=question_id)
    get_record = get_object_or_404(Record, user_id=request.user.id, question_id=question_id, )

    # 結合
    question_info_dict = _integrate_question_and_record(get_question=get_question,
                                                        get_record=get_record)

    form = SelectAnswerForm(question_id, request.GET)

    context = {
        'question': question_info_dict,
        'form': form,
        'model_answer_result': AnswerResult,
    }
    return render(request, 'jrfoodadv/record/record_question_id.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def record_list(request):
    """学習履歴一覧"""
    # form側にpage=1を仕込んでおく
    page_num = _check_paging(request)

    # 全てのrecordをsaved_atの降順で取得
    record_qs = Record.objects.filter(user_id=request.user.id)\
                                .order_by('-saved_at')
    record_ids_list = [question.question_id for question in record_qs]
    # 並びをrecord_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(record_ids_list)

    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'current_answer': record_dict.get(question.question_id).current_answer,
            'question_content': _make_question_content(question),
            'textbook_chapter': question.textbook_chapter_as_str(),
            'memo': record_dict.get(question.question_id).memo,
            'favorite': record_dict.get(question.question_id).favorite,
        }
        # きちんとcurrent_answerがあるものを抽出
        # 検索からお気に入りだけチェックを入れた場合に、問題を一度も解答していないのに検出されるのを防ぐ
        if question_info_dict['current_answer']:
            question_info.append(question_info_dict)
    # 正解総数を取り出す
    total_number_of_correct_answers_list = [question['current_answer'] \
                                            for question in question_info \
                                            if question['current_answer'] == AnswerResult.CORRECT]
    total_number_of_correct_answers = len(total_number_of_correct_answers_list)
    # ページング処理
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=question_info)
    context = {
        'total_number_of_correct_answers': total_number_of_correct_answers,
        'count_all_questions': len(question_info),
        'question_page': question_info_page,
    }
    return render(request, 'jrfoodadv/record/record_list.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def memos(request):
    """履歴メモ一覧"""
    page_num = _check_paging(request)

    # 空のメモ以外のrecordをsaved_atの降順で取得
    record_qs = Record.objects.filter(user_id=request.user.id)\
                                .exclude(memo__exact='')\
                                .order_by('-saved_at')
    record_ids_list = [question.question_id for question in record_qs]
    # 並びをrecord_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(record_ids_list)

    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'memo': record_dict.get(question.question_id).memo,
            'question_content': _make_question_content(question),
            'textbook_chapter': question.textbook_chapter_as_str(),
        }
        question_info.append(question_info_dict)

    total_number_of_memos = len(question_info)
    # ページング処理
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=question_info)
    context = {
        'total_number_of_memos': total_number_of_memos,
        'question_page': question_info_page,
    }
    return render(request, 'jrfoodadv/record/memos.html', context)


@login_required
@check_auth
@require_http_methods(['GET'])
def favorites(request):
    """履歴お気に入り一覧"""
    page_num = _check_paging(request)

    record_qs = Record.objects.filter(user_id=request.user.id,
                                        favorite=True).order_by('-saved_at')
    record_ids_list = [question.question_id for question in record_qs]
    # 並びをrecord_ids_listで任意順序にし直して返す
    sorted_questions = _arbitrary_sequence(record_ids_list)

    record_dict = {}
    for question_record in record_qs:
        record_dict[question_record.question_id] = question_record

    # questionとrecordを合体して辞書型オブジェクトをリストに格納
    question_info = []
    for question in sorted_questions:
        question_info_dict = {
            'question_id': question.question_id,
            'favorite': record_dict.get(question.question_id).favorite,
            'question_content': _make_question_content(question),
            'textbook_chapter': question.textbook_chapter_as_str(),
        }
        question_info.append(question_info_dict)

    total_number_of_favorites = len(question_info)
    # ページング処理
    question_info_page = _make_paginator(page_num=page_num,
                                            question_qs=question_info)
    context = {
        'total_number_of_favorites': total_number_of_favorites,
        'question_page': question_info_page,
    }
    return render(request, 'jrfoodadv/record/favorites.html', context)
