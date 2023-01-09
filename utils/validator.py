""" corporateとjrfoodadvで使用する汎用処理（関数）をおく
"""
import re

def validate_password_with_email(password, email) -> bool:
    """ passwordとemaiチェック。
    emailのusernameと同じ文字列を含むpasswordの場合は不可。
    emailのusernameが1文字の時は必ず通す。
    passwordはvと置き換える→メッセージ文言がpasswordで漏れるのを防ぐ。
    """
    if not isinstance(email, str):
        raise ValueError('#validate_password_with_email: email is not str.')
    if not isinstance(password, str):
        raise ValueError('#validate_password_with_email: v is not str.')

    if not password:
        raise ValueError('#validate_password_with_email: v is None.')

    # emailからusernameを切り取る
    username = email[:email.find('@')]
    if username == '':
        raise ValueError('#validate_password_with_email: not emal.')

    if len(username) == 1:
        # emailのusernameが1文字の時は必ず通す
        return True

    elif len(username) > 1:
        if username in password:
            return False
        else:
            # OK
            return True
    else:
        raise ValueError(f'validate_password_with_email: {username}')


def validate_password1_and_password2(password1, password2) -> bool:
    """ password1とpassword2（確認用パスワード）チェック。
    password1とpassword2がequalでなければNG。
    password1とpassword2をそれぞれv1とv2に置き換える→メッセージ文言がpasswordで漏れるのを防ぐ。
    """
    if not isinstance(password1, str):
        raise ValueError('#validate_password1_and_password2: v1 is not str.')
    if not isinstance(password2, str):
        raise ValueError('#validate_password1_and_password2: v2 is not str.')
    if not password1:
        raise ValueError('#validate_password1_and_password2: v1 is None.')
    if not password2:
        raise ValueError('#validate_password1_and_password2: v2 is None.')

    if password1 != password2:
        # NG
        return False
    else:
        # password1 == password2
        # OK
        return True


def validate_emoji(text):
    """ emojiが含まれているかのチェック。
    emojiが1つでも含まれている場合はNG。
    """
    # 正規表現パターンを構築
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        # u"\U000024C2-\U0001F251" # 日本語
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                    "]+", re.UNICODE)

    if re.findall(emoji_pattern, text):
        return False
    else:
        return True
