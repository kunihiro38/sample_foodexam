'use strict';


// targetsに含まれる文字列が問題文に出現した際は下線をつける
$(function() {
	var $question_title = $('.question_title');
    var question_title_txt = $question_title.html();
    var targets = ['最も不適切なもの',
                    '最も適切な語句',
                    '商品に表示すべき内容の範囲に該当するもの',
                    '生鮮食品に該当しないもの',
                    '加工食品に該当しないもの',
                    '最も不適切な表示',
                    '最も不適切な表示部分',
                    '最も適切な組み合わせ',
                    '最も適切な語句の組み合わせ',
                    'このマークの対象にならないもの',
                    '最も適切なもの',
                    '省略が可能な項目の組み合わせ']
    for (var target = 0; target < targets.length ; ++target) {
        if (!question_title_txt){
            // 解答状況(/jrfoodadv/practice_test/answer_status) でのconsoleエラーを表示させない
        } else if (question_title_txt.includes(targets[target]) === true) {
            var replaceTxt = question_title_txt.replace(targets[target],
                '<span style="border-bottom: 1px solid #000;">' + targets[target] + '</span>');
            $question_title.html(replaceTxt);
        }
    }
});


// 正解がクリックされたら、回答選択肢の正答にも色がつく
$(function(){
    $('summary').on('click', function(){
        var correct_answer = $('.correct_answer').attr('id');
        var choices = [];
        choices.push($('#id_select_answer_0').val());
        choices.push($('#id_select_answer_1').val());
        choices.push($('#id_select_answer_2').val());
        choices.push($('#id_select_answer_3').val());
        for (var choice = 0; choice < choices.length; ++choice) {
            if (correct_answer === choices[choice]) {
                $('[value=' + choices[choice] + ']').parent('label').addClass("like_skyblue strong");
                $('[value=' + choices[choice] + ']').parent('p').next('.choice_label').addClass("like_skyblue strong");
            }
        }
    });
});


// Djangoでformを使わないでpostする
// 公式参考→ https://docs.djangoproject.com/ja/2.2/ref/csrf/
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// メモの保存のAjax処理
function SendMemoToServer(question_id, textarea_val){
    var csrf_token = getCookie('csrftoken');
    $.ajax({
        url: '/jrfoodadv/memo_ajax/',
        type: 'POST',
        data: {'question_id': question_id, 'memo': textarea_val},
        dataType: 'json',
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    })
    .done(function(data) {
        console.log(data);
        if (data['memo'] === true) {
            $('#memo, #i_memo').addClass('memo_is_true');
        } else if(data['memo'] === false) {
            // 今のところ絵文字を保存した時にのみ発火するalert
            // 「絵文字を使用しないでください。」
            alert(data['message']); 
        }
    })
    .fail(function() {
        alert('メモの保存に失敗しました。通信状態の良いところで再度実行してください。');
    })
};

// クリックでメモのモーダルポップアップ
$(function() {
    $('button#memo').on('click', function() {
        popupMemo(this);
    });
});

// buttonクリック全体の挙動からtextareaの内容をサーバーに送信するまで
function popupMemo(obj) {
    var popup = document.getElementById('js-popup');
    if (!popup) return;

    $('#popup-btn').off('click');
    $('#popup-btn').on('click', function(){
        var question_id = $(obj).attr('data-question-id');
        var textarea_val = $('textarea[name="memo"]').val();
        SendMemoToServer(question_id, textarea_val);
    });

    // 閉じる
    var backBg = document.getElementById('js-black-bg');
    var closeBtn = document.getElementById('js-close-btn');
    var popupBtn = document.getElementById('popup-btn');
    // 閉じるボタンもしくは、backgroundで閉じた場合はtextareaの中身を消すか?
    // 消す直前にリロードする?

    // backgroundに黒表示
    popup.classList.add('is-show');

    closePopUp(backBg);
    closePopUp(closeBtn);
    closePopUp(popupBtn);

    // 画面を閉じる
    function closePopUp(elm) {
        elm.addEventListener('click', function() {
            popup.classList.remove('is-show');
        });
    }
}

// お気に入り登録の保存のAjax処理
function SendFavoriteToServer(question_id){
    var csrf_token = getCookie('csrftoken');
    $.ajax({
        url: '/jrfoodadv/favorite_ajax/',
        type: 'POST',
        data: {'question_id': question_id},
        dataType: 'json',
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    })
    .done(function(data) {
        if (data['favorite'] === true) {
            $('#favorite, #i_favorite').addClass('favorite_is_true');
        } else if(data['favorite'] === false) {
            $('#favorite, #i_favorite').removeClass('favorite_is_true');
        }
    })
    .fail(function() {
        alert('お気に入りの通信に失敗しました。通信状態の良いところで再度実行してください。');
    })
};

// ボタンクリックでお気に入り登録
$(function() {
    $('button#favorite').on('click', function() {
        var question_id = $(this).attr('data-question-id');
        SendFavoriteToServer(question_id);
    });
});

// あとでやる登録のAjax処理
function SendLaterToServer(question_id){
    var csrf_token = getCookie('csrftoken');
    $.ajax({
        url: '/jrfoodadv/later_ajax/',
        type: 'POST',
        data: {'question_id': question_id},
        dataType: 'json',
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    })
    .done(function(data) {
        if (data['later'] === true) {
            $('#later').addClass('later_is_true');
            $('#later').css('box-shadow', '0 0 0 0');
        } else if(data['later'] === false) {
            $('#later').removeClass('later_is_true');
            $('#later').css('box-shadow', '0rem 0rem 0rem 0.1rem #333');
        }
    })
    .fail(function() {
        alert('あとでやるの通信に失敗しました。通信状態の良いところで再度実行してください。');
    })
};

// ボタンクリックであとでやる登録
$(function() {
    $('button#later').on('click', function() {
        var question_id = $(this).attr('data-question-id');
        SendLaterToServer(question_id);
    });
});

// 中止
$(function() {
    $('.finish_practice_test').on('click', function() {
        var result = window.confirm('中止をするとこれまでの回答は保存されません。\n\nまた、試験を再開することはできません。');
        if(result) {
            window.location.href='/jrfoodadv/';
        }
        else {
        }
    });
});
