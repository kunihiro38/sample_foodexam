"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from dotenv import load_dotenv
from django.urls import include, path

# mediaディレクトリに保存した画像の表示
from django.conf import settings
from django.conf.urls.static import static

load_dotenv()

urlpatterns = [
    path('', include('corporate.urls')),
    path('jrfoodadv/', include('jrfoodadv.urls')),
    # path('foodadv/', include('foodadv.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
