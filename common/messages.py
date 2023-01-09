""" corporateとjrfoodadvの共通で使用する共通（関数以外）をおく
"""

class FormMessages(object):
    """ エラーメッセージ
    """
    # user
    CANT_SIGNUP_USERNAME = 'このアカウント名では登録できません。'
    CANT_SIGNUP_EMAIL='このメールアドレスでは登録できません。'
    ALREADY_EXISTS = '既に登録されているメールアドレスです。'
    INCORRECT_PASSWORD = 'パスワードが間違っています。'
    NOT_EQUAL_PASSWD1_AND_PASSWD2 = '確認用パスワードが一致しません。'
    WRONG_EMAIL_OR_PASSWORD = 'メールアドレスかパスワードが間違っています。'
    INVALID_PASSWORD_WITH_EMAIL = 'メールアカウントをパスワードの一部として使用することはできません。'
    CANT_USE_EMOJI = '絵文字を使用しないでください。'
