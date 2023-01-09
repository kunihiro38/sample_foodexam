"""
"""
import math

from django import template
from django.utils.safestring import mark_safe
from jrfoodadv.models import AnswerResult

# Djangoテンプレートタグライブラリ
register = template.Library()

@register.simple_tag
def return_fontawesome(answer_result:int) -> str:
    """Noneもしくは0,1,2を引数で受け取りstrで返す
    WAITING = 0 -> 未実施
    UNANSWERED = 1 -> 未解答
    INCORRECT = 2 -> 不正解
    CORRECT = 3 -> 正解
    """
    if not answer_result:
        return mark_safe('<i class="fa fa-minus fa-1x gray_color"></i>')
    elif answer_result == AnswerResult.UNANSWERED:
        return '未'
    elif answer_result == AnswerResult.INCORRECT:
        return mark_safe('<i class="fa fa-times fa-1x red_color"></i>')
    elif answer_result == AnswerResult.CORRECT:
        return mark_safe('<i class="fa fa-genderless fa-1x blue_color" \
                            style="font-size:large;"></i>')
    else:
        raise RuntimeError()


@register.simple_tag
def division(value_a, value_b):
    """割り算 -> 小数点切り捨てして返す"""
    calculation_result = value_a / value_b
    calculation_result = math.floor(calculation_result*100) # 小数点第1位消す
    return calculation_result
