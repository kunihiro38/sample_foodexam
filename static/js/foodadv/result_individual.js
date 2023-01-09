'use strict';

// inputをdisabledにしておく
$('input').prop('disabled', true);

// 正しい解答に始めからskyblue色をつけておく
$(function(){
    var correct_answer = $('.correct_answer').attr('data_correct_answer');
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

// 誤答に選択肢た場合も始めから赤色をつけておく
$(function(){
    // もし誤答の場合は発動
    var current_choice = $('.current_choice').attr('data_current_choice');
    var correct_answer = $('.correct_answer').attr('data_correct_answer');
    if (current_choice !== correct_answer) {
        var choices = [];
        choices.push($('#id_select_answer_0').val());
        choices.push($('#id_select_answer_1').val());
        choices.push($('#id_select_answer_2').val());
        choices.push($('#id_select_answer_3').val());
        for (var choice = 0; choice < choices.length; ++choice) {
            if (current_choice === choices[choice]) {
                $('[value=' + choices[choice] + ']').parent('label').prepend('<i class="fa fa-times fa-1x red_color" style="padding-left: .5rem;"></i>');
                $('[value=' + choices[choice] + ']').parent('label').addClass("red_color strong");
                $('[value=' + choices[choice] + ']').parent('p').prepend('<i class="fa fa-times fa-1x red_color" style="padding-left: .5rem;"></i>');
                $('[value=' + choices[choice] + ']').parent('p').next('.choice_label').addClass("red_color strong");
                // inputボタンの削除
                $('[value=' + choices[choice] + ']').remove();
            }
        }
    }
});
