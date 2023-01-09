"""breadcrumbsを作成
・JavaScriptでの作成は、遅延に繋がる且つgoogle rich-resultsに反映されない可能性があるのでpythonで作成
・HACK:20220606:全体的にコードが汚いのでやり直したい
"""
import re

from django import template
from django.utils.safestring import mark_safe

from corporate.models import Information, Testimonials

# Djangoテンプレートタグライブラリ
register = template.Library()


class CorporateUrl():
    """ 階層番号とそれに紐づく前階層番号を付与?

    """
    INDEX = 0
    INFO_LIST = 1
    COLUMN = 2
    TESTIMONIALS = 3
    INFO_INDIVIDUAL = 4
    COLUMN_INDIVIDUAL = 5
    TESTIMONIALS_INDIVIDUAL = 6 
    MAINTENANCE = 7
    SIGNUP = 8
    SIGNUP_SENT = 9
    SIGNUP_COMPLETE = 10
    INTRODUCTION = 11
    COURSE = 12
    COURSE_JRFOODADV = 13
    COURSE_JRFOODADV_MONTHLY = 14
    COURSE_JRFOODADV_TEN_DAYS = 15
    COURSE_JRFOODADV_THREE_DAYS = 16
    PAY_JRFOODADV = 17
    PAY_SUCCESS = 18
    SIGNIN = 19
    PASSWORD_RESET = 20
    PASSWORD_RESET_SENT = 21
    PASSWORD_RESET_CONFIRM = 22
    PASSWORD_RESET_COMPLETE = 23
    SETTING = 24
    WITHDRAWAL = 25
    PROFILE = 26
    EDIT_USERNAME = 27
    CHANGE_EMAIL = 28
    CHANGE_PASSWORD = 29
    EDIT_SUCCESS = 30
    DEL_PROFILE_SUCCESS = 31
    USER_LOGOUT = 32
    ADD_INFO = 33
    ADD_INFO_SUCCESS = 34
    TERMS = 35
    POLICY = 36
    LAW = 37
    INQUIRY = 38
    INQUIRY_ADD_SUCCESS = 39
    COURSE_FOODADV = 40
    COURSE_FOODADV_MONTHLY = 41
    COURSE_FOODADV_TEN_DAYS = 41
    COURSE_FOODADV_THREE_DAYS = 43


    CORPORATE_URL_CHOICES = [
        [INDEX, '/', 'トップページ'],
        [INFO_LIST, '/info/', 'お知らせ一覧'],
        [COLUMN, '/column/', '学習コラム'],
        [TESTIMONIALS, '/testimonials/', '合格体験記一覧'],
        [INFO_INDIVIDUAL, '/info/<str:info_id>', ''],  
        [COLUMN_INDIVIDUAL, '/column/<str:info_id>', ''],
        [TESTIMONIALS_INDIVIDUAL, '/testimonials/<str:testimonials_id>', ''],
        [MAINTENANCE, '/maintenance/', 'メンテナンス'],
        [SIGNUP, '/signup/', '会員登録'],
        [SIGNUP_SENT, '/signup/sent', '会員仮登録'],
        # [SIGNUP_COMPLETE, '', ''], 
        [INTRODUCTION, '/introduction/', 'フードイグザムとは？'],
        [COURSE, '/course/', 'コース選択'],
        [COURSE_JRFOODADV, '/course/jrfoodadv/', '食品表示検定・初級のプラン選択'],
        [COURSE_JRFOODADV_MONTHLY, '/course/jrfoodadv/monthly', 'マンスリープラン'],
        [COURSE_JRFOODADV_MONTHLY, '/course/jrfoodadv/10days', '10days集中プラン'],
        [COURSE_JRFOODADV_THREE_DAYS, '/course/jrfoodadv/3days', '3days短期プラン'],
        [PAY_JRFOODADV, '/pay/jrfoodadv/', '食品表示検定・初級コース支払い'],
        [PAY_SUCCESS, '/pay/success', '支払い完了'],
        [SIGNIN, '/signin/', 'ログイン'],
        [PASSWORD_RESET, '/password_reset/', 'パスワードリセット'],
        [PASSWORD_RESET_SENT, '/password_reset/sent', 'パスワード変更用URL送信'],
        # [PASSWORD_RESET_CONFIRM, '',''],
        [PASSWORD_RESET_COMPLETE, '/password_reset/complete', '新パスワード設定完了'],
        [SETTING, '/setting/', '設定'],
        [WITHDRAWAL, '/setting/withdrawal/', '退会'],
        [PROFILE, '/profile/', 'プロフィール'],
        [EDIT_USERNAME, '/profile/edit/username/', 'アカウント名編集'],
        [CHANGE_EMAIL, '/profile/change/email/', 'メールアドレス変更'],
        [CHANGE_PASSWORD, '/profile/change/password/', 'パスワード変更'],
        [EDIT_SUCCESS, '/profile/edit/success/', '更新'],
        [DEL_PROFILE_SUCCESS, '/profile/del/success', 'アカウント削除完了'],
        [USER_LOGOUT, '/profile/logout', 'ログアウト'],
        [ADD_INFO, '/info/add/', 'お知らせ投稿'],
        [ADD_INFO_SUCCESS, '/info/add/success', 'お知らせ投稿完了'],
        [TERMS, '/terms', '利用規約'],
        [POLICY, '/policy', 'プライバシーポリシー'],
        [LAW, '/law', '特定商取引に基づく表記'],
        [INQUIRY, '/inquiry/', '問い合わせ'],
        [INQUIRY_ADD_SUCCESS, '/inquiry/success', '問い合わせ送信成功'],
        [COURSE_FOODADV, '/course/foodadv/', '食品表示検定・中級のプラン選択'],
        [COURSE_FOODADV_MONTHLY, '/course/foodadv/monthly', 'マンスリープラン'],
        [COURSE_FOODADV_MONTHLY, '/course/foodadv/10days', '10days集中プラン'],
        [COURSE_FOODADV_THREE_DAYS, '/course/foodadv/3days', '3days短期プラン'],
    ]


@register.simple_tag
def return_breadcrumbs(path):
    """request.pathを受け取って、breadcrumbsを返す
    """
    def _make_content(content_num, content_url, content_title):
        content = f'<li itemprop="itemListElement" itemscope itemtype="https://schema.org/Listitem">\
                <a itemprop="item" href="{content_url}"><span itemprop="name">{content_title}</span></a>\
                <meta itemprop="position" content="{content_num}">\
            </li>'
        return content

    def _make_breadcrumbs(content_2='', content_3='', content_4=''):
        content_1 = '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/Listitem"><a itemprop="item" href="/"><span itemprop="name">ホーム</span></a><meta itemprop="position" content="1"/></li>'
        breadcrumbs = f'<div class="breadcrumb-background-color">\
                            <div class="breadcrumb">\
                                <ul itemscope itemtype="https://schema.org/BreadcrumbList">\
                                    {content_1}{content_2}{content_3}{content_4}\
                                </ul>\
                            </div>\
                        </div>'
        return breadcrumbs

    def _get_info_title(info_id):
        if not info_id.isdigit():
            raise RuntimeError('invalid')
        info = Information.objects.get(id=info_id)
        return info.title

    def _get_testimonials_title(testimonials_id):
        if not testimonials_id.isdigit():
            raise RuntimeError('invalid')
        testimonials = Testimonials.objects.get(id=testimonials_id)
        return testimonials.title

    for corporate_url in CorporateUrl.CORPORATE_URL_CHOICES:
        if path == '/'\
            or path == '/maintenance':
            # トップページ or maintenance
            return ''

        elif re.match(r'/info/\d+', path):
            # お知らせ一覧
            # 階層:3
            content_num = 2
            content_url = '/info/'
            content_title = 'お知らせ一覧'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            # 数字だけ抽出
            content_num = 3
            # content_url = path
            info_id = re.sub(r'\D', '', path)
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=_get_info_title(info_id)
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))

        elif re.match(r'/column/\d+', path):
            # 学習コラム一覧
            # 階層:3
            content_num = 2
            content_url = '/column/'
            content_title = '学習コラム一覧'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            # 数字だけ抽出
            content_num = 3
            # content_url = path
            info_id = re.sub(r'\D', '', path)
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=_get_info_title(info_id)
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))

        elif re.match(r'/testimonials/\d+', path):
            # 合格体験記一覧
            # 階層:3
            content_num = 2
            content_url = '/testimonials/'
            content_title = '合格体験記一覧'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            # 数字だけ抽出
            content_num = 3
            # content_url = path
            testimonials_id = re.sub(r'\D', '', path)
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=_get_testimonials_title(testimonials_id)
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))

        elif path == '/course/jrfoodadv/':
            # コース選択直下にプラン選択（4階層）があるので場合わけせずに構築
            # コース選択
            # 階層:3
            content_num = 2
            content_url = '/course/'
            content_title = 'コース選択'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = path
            content_title = '食品表示検定・初級のプラン選択'
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=content_title
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))


        elif path == '/course/jrfoodadv/monthly'\
                or path == '/course/jrfoodadv/10days'\
                or path == '/course/jrfoodadv/3days':
            # プラン選択
            # 階層:4
            content_num = 2
            content_url = '/course/'
            content_title = 'コース選択'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = '/course/jrfoodadv/'
            content_title = '食品表示検定・初級のプラン選択'
            content_3 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            if path == '/course/jrfoodadv/monthly':
                content_num = 4
                content_url = path
                content_title = 'マンスリープラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))

            elif path == '/course/jrfoodadv/10days':
                content_num = 4
                content_url = path
                content_title = '10days集中プラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))

            elif path == '/course/jrfoodadv/3days':
                content_num = 4
                content_url = path
                content_title = '3days短期プラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))


        elif path == '/course/foodadv/':
            # コース選択直下にプラン選択（4階層）があるので場合わけせずに構築
            # コース選択
            # 階層:3
            content_num = 2
            content_url = '/course/'
            content_title = 'コース選択'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = path
            content_title = '食品表示検定・中級のプラン選択'
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=content_title
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))


        elif path == '/course/foodadv/monthly'\
                or path == '/course/foodadv/10days'\
                or path == '/course/foodadv/3days':
            # プラン選択
            # 階層:4
            content_num = 2
            content_url = '/course/'
            content_title = 'コース選択'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = '/course/foodadv/'
            content_title = '食品表示検定・中級のプラン選択'
            content_3 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            if path == '/course/foodadv/monthly':
                content_num = 4
                content_url = path
                content_title = 'マンスリープラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))

            elif path == '/course/foodadv/10days':
                content_num = 4
                content_url = path
                content_title = '10days集中プラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))

            elif path == '/course/foodadv/3days':
                content_num = 4
                content_url = path
                content_title = '3days短期プラン'
                content_4 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3,
                    content_4=content_4,
                ))


        elif path == '/profile/edit/username/'\
                or path == '/profile/change/password/'\
                or path == '/profile/edit/success/'\
                or path == '/profile/logout':
            # アカウント名編集 or パスワード編集 or ログアウト
            # 階層:3
            content_num = 2
            content_url = '/profile/'
            content_title = 'プロフィール'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            if path == '/profile/edit/username/':
                content_num = 3
                content_url = path
                content_title = 'アカウント名編集'
                content_3 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3
                ))

            elif path == '/profile/change/password/':
                content_num = 3
                content_url = path
                content_title = 'パスワード変更'
                content_3 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3
                ))

            elif path == '/profile/edit/success/':
                content_num = 3
                content_url = path
                content_title = '更新'
                content_3 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3
                ))


            elif path == '/profile/logout':
                content_num = 3
                content_url = path
                content_title = 'ログアウト'
                content_3 = _make_content(
                    content_num=content_num,
                    content_url=path,
                    content_title=content_title
                )
                return mark_safe(_make_breadcrumbs(
                    content_2=content_2,
                    content_3=content_3
                ))

        elif path == '/setting/withdrawal/':
            # 退会
            # 階層:3
            content_num = 2
            content_url = '/setting/'
            content_title = '設定'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = path
            content_title = '退会'
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=content_title
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))

        elif path == '/inquiry/success':
            # お問い合わせ送信成功
            # 階層:3
            content_num = 2
            content_url = '/inquiry/'
            content_title = '問い合わせ'
            content_2 = _make_content(
                content_num=content_num,
                content_url=content_url,
                content_title=content_title
            )

            content_num = 3
            content_url = path
            content_title = '問い合わせ送信成功'
            content_3 = _make_content(
                content_num=content_num,
                content_url=path,
                content_title=content_title
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
                content_3=content_3
            ))

        elif path == corporate_url[1]:
            # 階層:2
            content_2 = _make_content(
                content_num=2,
                content_url=corporate_url[1],
                content_title=corporate_url[2]
            )
            return mark_safe(_make_breadcrumbs(
                content_2=content_2,
            ))

    # 階層：3だけど演算子書いていない場合Noneになるので空文字を返す
    return ''
