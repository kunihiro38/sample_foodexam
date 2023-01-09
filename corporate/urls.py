"""
トップページの管理画面
"""

from django.urls import path
from . import views

app_name = 'corporate'

urlpatterns = [
    # トップページ
    path('', views.index, name='index'),
    # お知らせ一覧
    path('info/', views.info_list, name='info_list'),
    # 学習コラム一覧
    path('column/', views.column, name='column'),
    # 合格体験記一覧
    path('testimonials/', views.testimonials_list, name='testimonials_list'),
    # お知らせ個別
    path('info/<str:info_id>', views.info_individual, name='info_individual'),
    # 学習コラム個別
    path('column/<str:info_id>', views.column_individual, name='column_individual'),
    # 合格体験記個別
    path('testimonials/<str:testimonials_id>', views.testimonials_individual, name='testimonials_individual'),
    # メンテナンス
    path('maintenance', views.maintenance, name='maintenance'),
    # 会員登録
    path('signup/', views.Signup.as_view(), name='signup'),
    # 会員仮登録
    path('signup/sent', views.SignupSent.as_view(), name='signup_sent'),
    # 会員登録完了
    path('signup/complete/<token>', views.SignupComplete.as_view(), name='signup_complete'),
    # 紹介
    path('introduction/', views.introduction, name='introduction'),
    # コース選択
    path('course/', views.course, name='course'),
    # 食品表示検定・初級コース支払い -> 20220629 -> 最初に作成した月額1100円の固定コース。案として残しておく
    # path('pay/jrfoodadv/', views.pay_jrfoodadv, name='pay_jrfoodadv'),
    # 食品表示検定・初級のプラン選択
    path('course/jrfoodadv/', views.jrfoodadv_plan, name='jrfoodadv_plan'),
    # マンスリープラン
    path('course/jrfoodadv/monthly', views.plan_monthly, name='plan_monthly'),
    # 10days集中プラン
    path('course/jrfoodadv/10days', views.plan_10days, name='plan_10days'),
    # 3days短期プラン
    path('course/jrfoodadv/3days', views.plan_3days, name='plan_3days'),
    # 支払い完了
    path('pay/success', views.pay_success, name='pay_success'),
    # 食品表示検定・中級のプラン選択
    path('course/foodadv/', views.foodadv_plan, name='foodadv_plan'),
    # 中級マンスリープラン
    path('course/foodadv/monthly', views.foodadv_plan_monthly, name='foodadv_plan_monthly'),
    # 中級10days集中プラン
    path('course/foodadv/10days', views.foodadv_plan_10days, name='foodadv_plan_10days'),
    # 中級3days短期プラン
    path('course/foodadv/3days', views.foodadv_plan_3days, name='foodadv_plan_3days'),
    # 中級支払い完了
    path('pay/foodadv/success', views.foodadv_pay_success, name='foodadv_pay_success'),
    # ログイン
    path('signin/', views.signin, name='signin'),
    # パスワードリセット
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    # パスワード変更用URL送信
    path('password_reset/sent', views.PasswordResetSent.as_view(), name='password_reset_sent'),
    # パスワード再設定
    path('password_reset/confirm/<uidb64>/<token>', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    # 新パスワード設定完了
    path('password_reset/complete', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    # 設定
    path('setting/', views.setting, name='setting'),
    # 退会
    path('setting/withdrawal/', views.withdrawal, name='withdrawal'),
    # プロフィール
    path('profile/', views.profile, name='profile'),
    # アカウント名編集
    path('profile/edit/username/', views.edit_username, name='edit_username'),
    # メールアドレス変更
    path('profile/change/email/', views.change_email, name='change_email'),
    # パスワード変更
    path('profile/change/password/', views.change_password, name='change_password'),
    # 更新
    path('profile/edit/success/', views.edit_success, name='edit_success'),
    # アカウント削除完了
    path('profile/del/success', views.del_profile_success, name='del_profile_success'),
    # ログアウト
    path('profile/logout', views.user_logout, name='user_logout'),
    # 利用規約
    path('terms', views.terms, name='terms'),
    # プライバシーポリシー
    path('policy', views.policy, name='policy'),
    # 特定商取引に基づく表記
    path('law', views.law, name='law'),
    # 問い合わせ
    path('inquiry/', views.inquiry, name='inquiry'),
    # 問い合わせ送信成功
    path('inquiry/success', views.inquiry_add_success, name='inquiry_add_success'),
    # 合格体験記の投稿
    path('testimonials/post/', views.post_testimonials, name='post_testimonials'),
    # 合格体験記の投稿の成功
    path('testimonials/post/success', views.post_testimonials_success, name='post_testimonials_success'),
]
