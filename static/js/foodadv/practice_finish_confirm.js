'use strict';


// 「未解答の問題を見直す」か問題IDをクリックしたらフラグを立てる関数を呼び出す
$(function() {
    $('a#list_review_flg').on('click', function(){
        SendReviewFlgToServer('list_review_flg');
    });
    $('a#question_id_review_flg').on('click', function(){
        SendReviewFlgToServer('question_id_review_flg');
    });
});


// 未解答の問題を見直す と IDのリンクから入った場合わけをする
function SendReviewFlgToServer(review_flg){
    $.ajax({
        url: '/foodadv/make_review_flg_ajax/',
        type: 'get',
        data: {'review_flg': review_flg},
        dataType: 'json',
    })
    .done(function(data){
        console.log();
    })
    .fail(function(){
        // alert('fail!');
    })
};

// 中止
$(function() {
    $('.finish_practice_test').on('click', function() {
        var result = window.confirm('中止をするとこれまでの回答は保存されません。\n\nまた、試験を再開することはできません。');
        if(result) {
            window.location.href='/foodadv/';
        }
        else {
        }
    });
});