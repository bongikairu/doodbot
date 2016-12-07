# encoding: utf-8

from __future__ import unicode_literals

from django.http import HttpResponseBadRequest, HttpResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

from bot.models import Event

CHANNEL_ACCESS_TOKEN = b'UIbiQYKRHMHHOkk/q5pRonLGBLd3KXccS2HkZyjK0TaZbItNj9KfChtOMI5t2+RkuwFpSticEhy4gQy/1qlnhb38G4dteU8/EJKSp9zuT10RwwM4R4JZOzB2vgEmwXFurLENwCBCSHJPGvQbmIJ/pwdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = b'20f0ee9d35df8630d817a54255605865'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


def webhook(request):
    signature = request.META.get('HTTP_X_LINE_SIGNATURE', '')
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponseBadRequest()

    return HttpResponse('ok')


def save_message(event):
    Event.objects.create(payload=str(event), event_type=event.type)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    save_message(event)

    if event.message.text == '#น่าเบื่อ':
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(b'https://doodbot.herokuapp.com/static/bored.png', b'https://doodbot.herokuapp.com/static/bored.png')
        )


@handler.default()
def default(event):
    save_message(event)
