"""
食品表示検定・中級
・ログイン必須
・有料会員限定
"""
from . import views
from django.urls import path


app_name = 'foodadv'

urlpatterns = [
    # トップページ
    path('', views.index, name='index'),
    # 設定
    path('setting/', views.setting, name='setting'),
    # 学習記録の削除
    path('setting/del_record/', views.del_record, name='del_record'),
    # 学習記録の削除の成功
    path('setting/del_record/success', views.del_record_success, name='del_record_success'),
    # プロフィール
    path('profile/', views.profile, name='profile'),
    # 問題数のカウントajax
    path('count_question_ajax/', views.count_question_ajax, name='count_question_ajax'),
    # ログイン
    path('signin/', views.signin, name='signin'),
    # 検索
    path('search/', views.search, name='search'),
    # 検索ID個別
    path('search/question_id/<str:question_id>', views.search_question_id, name='search_question_id'),
    # 履歴ID個別
    path('record/question_id/<str:question_id>', views.record_question_id, name='record_question_id'),
    # 学習履歴一覧
    path('record/list/', views.record_list, name='record_list'),
    # 履歴メモ一覧
    path('record/memos/', views.memos, name='memos'),
    # 履歴お気に入り一覧
    path('record/favorites/', views.favorites, name='favorites'),
    # session処理してラストページへリダイレクトさせる
    path('back_to_last_page/<str:question_id>', views.back_to_last_page, name='back_to_last_page'),
    # 練習モード
    path('practice/<get_params>/', views.practice, name='practice'),
    # 未解答の問題見直しフラグ作成
    path('make_review_flg_ajax/', views.make_review_flg_ajax, name='make_review_flg_ajax'),
    # メモ保存
    path('memo_ajax/', views.memo_ajax, name='mamo_ajax'),
    # お気に入り登録
    path('favorite_ajax/', views.favorite_ajax, name='favorite_ajax'),
    # あとでやる登録
    path('later_ajax/', views.later_ajax, name='later_ajax'),
    # 練習モード終了直前の確認
    path('practice_finish_confirm/', views.practice_finish_confirm, name='practice_finish_confirm'),
    # 演習結果
    path('practice/result', views.practice_result, name='practice_result'),
    # ミスに再挑戦
    path('practice/rechallenge_mistakes', views.rechallenge_mistakes, name='rechallenge_mistakes'),
    # 演習結果個別
    path('practice/result/<str:question_id>', views.practice_result_individual, name='practice_result_individual'),
    # 模擬試験選択
    path('select_test/', views.select_test, name='select_test'),
    # 模擬試験
    path('practice_test/', views.practice_test, name='practice_test'),
    # 模擬試験終了直前の確認
    path('practice_test_finish_confirm/', views.practice_test_finish_confirm, name='practice_test_finish_confirm'),
    # カウントダウン終了
    path('forced_termination_ajax/', views.forced_termination_ajax, name='forced_termination_ajax'),
    # 解答状況
    path('practice_test/answer_status', views.answer_status, name='answer_status'),
]
