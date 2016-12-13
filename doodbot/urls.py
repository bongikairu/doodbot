"""doodbot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from bot import views as bot

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^webhook$', bot.webhook),
    url(r'^send_text/(.+)', bot.send_text),
    url(r'^set_switch/', bot.set_switch),
    url(r'^set_timezone/(.+)/(.+)', bot.set_timezone),
]
