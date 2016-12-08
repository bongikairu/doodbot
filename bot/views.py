# encoding: utf-8

from __future__ import unicode_literals

from django.http import HttpResponseBadRequest, HttpResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage

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

    auto_stickers = {
        '#น่าเบื่อ': b'bored-hires.png',
        'น่าเบื่อ': b'bored-hires.png',
        '#เกลียด': b'hate.png',
    }

    for key, value in auto_stickers.items():
        if event.message.text == key:
            image_url = b'https://doodbot.herokuapp.com/static/%s' % value
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(image_url, image_url)
            )

    if event.message.text == 'teststickerkrub':
        # "packageId": "1305699", "stickerId": "12354168"
        line_bot_api.reply_message(
            event.reply_token,
            StickerSendMessage(b'1305699', b'12354168')
        )


@handler.default()
def default(event):
    save_message(event)
