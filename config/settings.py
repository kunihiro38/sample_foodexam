"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import payjp
import requests
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ['DEBUG']
if str(DEBUG) == 'True':
    # 開発時
    # 404エラーはdjangoのデフォルトエラーが表示さる
    DEBUG = True
else:
    # 本番
    # 作成した404にリダイレクトが表示される
    DEBUG = False

ALLOWED_HOSTS = [
    os.environ['HOSTS1']
]

# 利用制限したemail。フードイグザムの機能を使ってもらいたい時に提示する。
# 制限箇所：アカウント名変更、パスワード変更、退会処理
LIMITED_EMAIL = os.environ['LIMITED_EMAIL']

# ALLOWED_HOSTSに"*"ではなく"www.food-exam.com"を記述するとAWSのターゲットグループのヘルスステータスでunhealthy状態になる
# 以下のようにインスタンスメタデータを実行中のインスタンスから取得してALLOWS_HOSTSに追加することで回避
EC2_PRIVATE_IP = None
try:
    EC2_PRIVATE_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4',
                                timeout = 0.01).text
    ALLOWED_HOSTS.append(EC2_PRIVATE_IP)
except requests.exceptions.RequestException:
    pass


# 本番用と開発用
PRODUCTION = True

# Application definition

INSTALLED_APPS = [
    'corporate.apps.CorporateConfig',
    'jrfoodadv.apps.JrfoodadvConfig',
    'foodadv.apps.FoodadvConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.media',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'foodtech',
        'USER': os.environ['MYSQL_USER'],
        'PASSWORD': os.environ['MYSQL_PASSWORD'],
        'HOST': os.environ['DATABASES_HOST'],
        'PORT': os.environ['DATABASES_PORT'],
    }
}

# django3.2にアップデート時に警告文として出現するようになった
# 参考：https://docs.djangoproject.com/ja/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD='django.db.models.AutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


################
# static files #
################

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

################
# media files #
################

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ['MEDIA_ROOT']


# login_requiredデコレータのリダイレクト先
LOGIN_URL = 'jrfoodadv:signin'

# メールサーバー用
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

if DEBUG is False:
    # 本番
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # 開発：コンソールに表示
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# 食品表示検定・初級
# 支払い
JRFOODADV_AMOUNT = 1100
USABLE_PERIOD = 30
# マンスリープラン
JRFOODADV_MONTHLY_PLAN_NAME = 'マンスリープラン'
JRFOODADV_MONTHLY_AMOUNT = 1980
MONTHLY_USABLE_PERIOD = 30
# 10days集中プラン
JRFOODADV_TEN_DAYS_PLAN_NAME = '10days集中プラン'
JRFOODADV_TEN_DAYS_AMOUNT = 990
TEN_DAYS_USABLE_PERIOD = 10
# 3days短期プラン
JRFOODADV_THREE_DAYS_PLAN_NAME = '3daysお試しプラン'
JRFOODADV_THREE_DAYS_AMOUNT = 330
THREE_DAYS_USABLE_PERIOD = 3


# 食品表示検定・中級
# マンスリープラン
FOODADV_MONTHLY_PLAN_NAME = 'マンスリープラン'
FOODADV_MONTHLY_AMOUNT = 3480
# 10days集中プラン
FOODADV_TEN_DAYS_PLAN_NAME = '10days集中プラン'
FOODADV_TEN_DAYS_AMOUNT = 1480
# 3days短期プラン
FOODADV_THREE_DAYS_PLAN_NAME = '3daysお試しプラン'
FOODADV_THREE_DAYS_AMOUNT = 540


# djangoログ
# 本番はログ格納。開発はconsole出力
if DEBUG is False:
    # 本番
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,

        # ログフォーマット
        'formatters': {
            'verbose': {
                'format': '\t'.join([
                    '[%(levelname)s]',
                    'asctime:%(asctime)s'
                    # 'module:%(module)s',
                    'name:%(name)s' # moduleよりnameの方が直感的で分かり易い
                    'message:%(message)s',
                    'process:%(process)d',
                    # 'thread:%(thread)d', # asctimeで管理できるし、肥大化するので不要
                ])
            },
        },

        # ログをどこに出すかの設定
        'handlers': {
            'file': { # どこに出すかの設定に名前をつける。fileという名前をつけている。
                'level': 'DEBUG', # DEBUG以上のログを取り扱うという意味
                'class': 'logging.FileHandler', # ログを出力するためのクラスを指定
                # 'filename': os.path.join(BASE_DIR, 'debug.log'),
                'filename': os.environ['DEBUG_FILE_PATH'], # どこに出すか
                'formatter': 'verbose', # どの出力フォーマットで出すか→formatters/verbose
            },
        },

        # loggersは名前空間で(複数)設定できる
        # 実際にviews.py等に直接書き込んでconsoleに出力できる
        'loggers': {
            # 以下djangoは本体が出すログ全般を拾うロガーとしてとりあえずの設定
            'django': {
                'handlers': ['file'], # 先に定義したhandlersのうちどれを使用するか指定する
                'level': 'DEBUG', # 設定したログレベル以下のログは出力されなくなる
                'propagate': False,
            },
        },
    }
