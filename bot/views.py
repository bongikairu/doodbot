# encoding: utf-8

from __future__ import unicode_literals

import json
import os
import random
import re

from django.http import HttpResponseBadRequest, HttpResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage, TemplateSendMessage

from django.core.cache import cache
from bot.models import Event

from wit import Wit
from pythainlp.segment import segment

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

WIT_ACCESS_TOKEN = os.environ.get('WIT_ACCESS_TOKEN')

wit_client = Wit(access_token=WIT_ACCESS_TOKEN)


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


def set_switch(request):
    cache.set('d20switch', True, None)
    return HttpResponse('ok')


def save_message(event):
    Event.objects.create(payload=str(event), event_type=event.type)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    save_message(event)

    if not hasattr(event, 'message') or not hasattr(event.message, 'text'):
        return

    # wit.ai NLP

    text = event.message.text

    segmented_text = " ".join(segment(text))
    resp = wit_client.message(segmented_text)

    main_intent = resp.get('entities', {}).get('intent', [{}])[0].get('value', '')

    # regular expression for dice
    dice_reg = '^#d([0-9]+)\+([0-9]+)$'

    if main_intent == 'open_bot':
        cache.set('bot_online', True, None)
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('บอททำงานต่อแล้ว')
        )

    if main_intent == 'close_bot':
        cache.set('bot_online', False, None)
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('บอทหยุดทำงานชั่วคราวแล้ว')
        )

    if not cache.get('bot_online'):
        return

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
        '#d20': random.randint(1, 20) if not cache.get('d20switch') else 20,
    }

    cache.set('d20switch', False, None)

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

    if main_intent == 'what_to_eat':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message(ask_for_food[random.randint(1, 10)])
        )

    if main_intent == 'what_not_to_eat':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('ตึกจุล')
        )

    if main_intent == 'what_time':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('ตอนนี้กี่โมงก็ดูข้างบนสิครับ')
        )

    if main_intent == 'capability':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('ลองเอง')
        )

    if main_intent == 'greeting':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('สวัสดีฮะ')
        )

    if bool(re.match(dice_reg,event.message.text)):
        matchObject = re.match(dice_reg, event.message.text)

        if int(matchObject.group(1)) in [4,6,8,10,12,20,100]:
            result = random.randint(1,int(matchObject.group(1))) + int(matchObject.group(2))
        else:
            result = 'ไม่มี'

        line_bot_api.reply_message(
            event.reply_token,
            bot_message(result)
        )

    if event.message.text == 'teststickerkrub':
        # "packageId": "1305699", "stickerId": "12354168"
        line_bot_api.reply_message(
            event.reply_token,
            StickerSendMessage('1305699', '12354168')
        )


@handler.default()
def default(event):
    save_message(event)
