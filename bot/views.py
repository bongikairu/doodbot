# encoding: utf-8

from __future__ import unicode_literals

import json
import random

from django.http import HttpResponseBadRequest, HttpResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage, TemplateSendMessage

from bot.models import Event

from wit import Wit

CHANNEL_ACCESS_TOKEN = b'UIbiQYKRHMHHOkk/q5pRonLGBLd3KXccS2HkZyjK0TaZbItNj9KfChtOMI5t2+RkuwFpSticEhy4gQy/1qlnhb38G4dteU8/EJKSp9zuT10RwwM4R4JZOzB2vgEmwXFurLENwCBCSHJPGvQbmIJ/pwdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = b'20f0ee9d35df8630d817a54255605865'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

wit_client = Wit(access_token='VL225NTUGFQFA77AYFW35U2VPOEO7KA2')


def webhook(request):
    signature = request.META.get('HTTP_X_LINE_SIGNATURE', '')
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponseBadRequest()

    return HttpResponse('ok')


# noinspection PyTypeChecker
def bot_message(text):
    return TemplateSendMessage(text, template={
        "type": "confirm",
        "text": text,
        "actions": [

        ]
    })


def send_text(request, text):
    last_message = Event.objects.last()  # type: Event
    payload_str = last_message.payload
    payload = json.loads(payload_str)

    try:
        line_bot_api.push_message(payload['source']['groupId'], bot_message(text=text))
    except LineBotApiError as e:
        pass

    return HttpResponse('ok')


d20switch = False


def set_switch(request):
    global d20switch
    d20switch = True
    return HttpResponse('ok')


def save_message(event):
    Event.objects.create(payload=str(event), event_type=event.type)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global d20switch
    save_message(event)

    if not hasattr(event, 'message') or not hasattr(event.message, 'text'):
        return

    # wit.ai NLP
    resp = wit_client.message(event.message.text)
    print('Wit.ai response: ' + str(resp))

    auto_stickers = {
        '#น่าเบื่อ': b'bored-hires.png',
        'น่าเบื่อ': b'bored-hires.png',
        '#เกลียด': b'hate-hires.png',
    }

    auto_text_reply = {
        'ใช่ไหมบอท': 'ครับ ใช่ครับ' if random.randint(1, 4) < 4 else 'ไม่',
        'ต้นแย่': 'ต้นแย่',
        'บอทแย่': 'ไม่ว่าบอทสิครับ บอทก็มีหัวใจนะ' if random.randint(1, 10) < 6 else 'ว่าผมทำไมครับ',
        '#d4': random.randint(1, 4),
        '#d6': random.randint(1, 6),
        '#d8': random.randint(1, 8),
        '#d10': random.randint(1, 10),
        '#d12': random.randint(1, 12),
        '#d20': random.randint(1, 20) if not d20switch else 20,
    }

    d20switch = False

    ask_for_food = {
        1: 'สปาเก็ตตี้ก็ดีนะ',
        2: 'พิซซ่าดีไหมครับ',
        3: 'ผัดกะเพราสิ',
        4: 'ไปทาซึก็ไม่เลว',
        5: 'ไข่เจียวก็พอมั้งวันนี้',
        6: 'อะไรก็ได้ไหมครับ เห็นคนชอบกินกัน',
        7: 'หมึกผัดไข่เค็ม',
        8: 'เนื้อย่างแล้วกันนะมื้อนี้',
        9: 'สลัดดีไหม กินผักบ้างก็ดีนะ',
        10: 'คิดเองบ้างนะครับ',
        11: 'ทำคาโบนาร่าสิ อย่าใส่ครีมนะ',
        12: 'เวลาเครียดๆ อย่างนี้ต้องลาบกับเบียร์เท่านั้น',
        13: 'รสดีเด็ดเถอะ',
        14: 'จะกินข้าวแล้วเหรอ ผมยังไม่หิวเลย',
    }

    for key, value in auto_stickers.items():
        if event.message.text == key:
            image_url = b'https://doodbot.herokuapp.com/static/%s' % value
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(image_url, image_url)
            )

    for key, value in auto_text_reply.items():
        if event.message.text == key:
            line_bot_api.reply_message(
                event.reply_token,
                bot_message(value)
            )

    if event.message.text == 'กินอะไรดีบอท':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message(ask_for_food[random.randint(1, 10)])
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
