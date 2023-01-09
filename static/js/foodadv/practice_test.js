'use strict';

// カウントダウンタイマー
function countDown() {
    var $time_left = $("#TimeLeft").attr('data-time-left');
    var startDateTime = new Date();
    var endDateTime = new Date($time_left);
    var left = endDateTime - startDateTime;
    var a_day = 24 * 60 * 60 * 1000;

    // 期限から現在までの『残時間の時間の部分』
    var hours = Math.floor((left % a_day) / (60 * 60 * 1000))
    // 残時間を秒で割って残分数を出す。
    // 残分数を60で割ることで、残時間の「時」の余りとして、『残時間の分の部分』を出す
    var minutes = Math.floor((left % a_day) / (60 * 1000)) % 60

    // 残時間をミリ秒で割って、残秒数を出す。
    // 残秒数を60で割った余りとして、「秒」の余りとしての残「ミリ秒」を出す。
    // 更にそれを60で割った余りとして、「分」で割った余りとしての『残時間の秒の部分』を出す
    var seconds = Math.floor((left % a_day) / 1000) % 60 % 60

    $("#TimeLeft").text(hours + ':' + minutes + ':' + seconds );
    setTimeout('countDown()', 1000);

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

    // カウントダウンタイマー0以下になったら強制終了
    if (hours+minutes+seconds <= 0){
        var csrf_token = getCookie('csrftoken');
        $.ajax({
            url: '/foodadv/forced_termination_ajax/',
            type: 'POST',
            dataType: 'json',
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_token);
                }
            }
        })
        .done(function(data) {
            window.location.href=data['url'];
        })
        .fail(function() {
            alert('Ajax failed');
        })
    }
}

$(function() {
    countDown();
});


// 解答状況専用
// 直前に閲覧したページのURLを色付けする
$(function() {
    var ref = document.referrer; // 直前に閲覧したURL
    $(`a[href="${ref}"]`).find('.answer_status_item').addClass('answering');
    // 前のページに戻るにhrefを追加する
    $('.answer_status_back').find('a').attr('href', ref);
});
