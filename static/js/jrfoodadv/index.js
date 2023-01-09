'use strict';

// 初回get時
SendTargetChoicesToServer();

$('input#id_target_0, input#id_target_1').change(function() {
    // 未出題にチェックついた時
    if ($('input#id_target_0').is(':checked')) {
        var unquestioned = true;
    }
    // 未出題にチェック外れた時
    if ($('input#id_target_0').is('')) {
        var unquestioned = false;
    }
    // ミスにチェックついた時
    if ($('input#id_target_1').is(':checked')) {
        var miss = true;
    }
    // ミスにチェック外れた時
    if ($('input#id_target_1').is('')) {
        var miss = false;
    }
    SendTargetChoicesToServer(unquestioned, miss);
});


function SendTargetChoicesToServer(unquestioned=false, miss=false) {
    // 全問題数カウントして代入
    $.ajax({
        url: 'count_question_ajax/',
        type: 'get',
        data: {'unquestioned': unquestioned, 'miss': miss},
        dataType: 'json',
    })
    .done(function(data){
        // 先に値があるなら削除
        $('#textbook_chapter_1').remove();
        $('#textbook_chapter_2').remove();
        $('#textbook_chapter_3').remove();
        $('#textbook_chapter_4').remove();
        $('#textbook_chapter_5').remove();
        $('#textbook_chapter_6').remove();
        $('.select_answers span').remove();


        // カウント数を付与
        $('label #id_chapter_0').parent().append('<span style="color:#697679;" id="textbook_chapter_1">'+' '+data['LABELING_BRIDGE']+'</span>');
        $('label #id_chapter_1').parent().append('<span style="color:#697679;" id="textbook_chapter_2">'+' '+data['FRESH_FOOD']+'</span>');
        $('label #id_chapter_2').parent().append('<span style="color:#697679;" id="textbook_chapter_3">'+' '+data['PROCESSED_FOOD']+'</span>');
        $('label #id_chapter_3').parent().append('<span style="color:#697679;" id="textbook_chapter_4">'+' '+data['VARIOUS_FOOD']+'</span>');
        $('label #id_chapter_4').parent().append('<span style="color:#697679;" id="textbook_chapter_5">'+' '+data['OTHER_FOOD']+'</span>');
        $('label #id_chapter_5').parent().append('<span style="color:#697679;" id="textbook_chapter_6">'+' '+data['THINK_FOOD']+'</span>');
        $('.select_answers').append('<span>'+' '+data['all_questions']+'</span>')
    })
    .fail(function(){
        alert('通信に失敗しました。通信状態の良いところで再度実行してください。');
    })
};


// 出題分野のどれか一つにでもチェックを入れないと問題のスタートができない
$('input#id_chapter_0,\
    input#id_chapter_1,\
    input#id_chapter_2,\
    input#id_chapter_3,\
    input#id_chapter_4,\
    input#id_chapter_5').change(function() {
    function CheckInputTag(chapter){
        if ($(chapter).is(':checked')) {
            $('button').removeClass('invalid_button')
                .prop('disabled', false)
                .text(' スタート')
                .prepend('<i class="fa fa-play" style="color:#fff;"></i>');
        };
    };
    var chapter = $(this).attr('id');
    CheckInputTag('input#' + chapter);

    // 全てのchapterにチェックが入っていないか確認
    // 入っていなければボタンを初期状態に戻す
    var chapters_list = [
        'input#id_chapter_0',
        'input#id_chapter_1',
        'input#id_chapter_2',
        'input#id_chapter_3',
        'input#id_chapter_4',
        'input#id_chapter_5',
    ]
    var flg = false;
    for (const chapter of chapters_list) {
        // 1つでもチェックが入っていたらflgをtrueにしボタンもそのまま
        if ($(chapter).is(':checked')) {
            var flg = true;
        };
    };
    // flgがfalseのままなら、buttonを初期の何のチェックも入っていない状態に戻す
    if (flg === false){
        $('button').addClass('invalid_button')
            .prop('disabled', true)
            .text(' 出題分野を選択してください')
            .remove('i');
    };
});
