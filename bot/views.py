# encoding: utf-8

from __future__ import unicode_literals

import json
import os
import random
import re
import googlemaps

import pytz
from django.utils import timezone

from django.http import HttpResponseBadRequest, HttpResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage, TemplateSendMessage

from django.core.cache import cache
from bot.models import Event

from wit import Wit
from pythainlp.segment import segment

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')

if os.environ.get('TEST_API', ''):
    class LineBotApiTest():
        def reply_message(self, reply_token, data):
            print(str(data))


    line_bot_api = LineBotApiTest()
else:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

handler = WebhookHandler(LINE_CHANNEL_SECRET)

WIT_ACCESS_TOKEN = os.environ.get('WIT_ACCESS_TOKEN', '')

wit_client = Wit(access_token=WIT_ACCESS_TOKEN)

GMAPS_KEY = os.environ.get('GMAPS_KEY', '')

gmaps = googlemaps.Client(key=GMAPS_KEY)


def nlp_segment(text):  # type: str
    parts = []
    for part in text.split(" "):
        try:
            subparts = segment(part)
            parts.extend(subparts)
        except Exception:
            parts.append(part)
    return parts


print("Current datetime is %s (Los Angeles time)" % timezone.now().astimezone(pytz.timezone('America/Los_Angeles')).strftime('%X %x'))
print(nlp_segment('เริ่มต้นการทำงานของบอท กำลังทดสอบการ segment ข้อความภาษาไทยนะครับ'))


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


def set_timezone(request, tz_str, tz_name):
    cache.set('timezone_%s' % tz_name, tz_str.replace('-', '/'), None)
    return HttpResponse('ok')


def save_message(event):
    Event.objects.create(payload=str(event), event_type=event.type)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if not os.environ.get('TEST_API', ''):
        save_message(event)

    if not hasattr(event, 'message') or not hasattr(event.message, 'text'):
        return

    # wit.ai NLP

    text = event.message.text

    segmented_text = " ".join(nlp_segment(text))
    resp = wit_client.message(segmented_text)
    print(resp)

    main_intent = resp.get('entities', {}).get('intent', [{}])[0].get('value', '')

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
    }

    ask_for_food = [
        'สปาเก็ตตี้ก็ดีนะ',
        'พิซซ่าดีไหมครับ',
        'ผัดกะเพราสิ',
        'ไปทาซึก็ไม่เลว',
        'ไข่เจียวก็พอมั้งวันนี้',
        'อะไรก็ได้ไหมครับ เห็นคนชอบกินกัน',
        'หมึกผัดไข่เค็ม',
        'เนื้อย่างแล้วกันนะมื้อนี้',
        'สลัดดีไหม กินผักบ้างก็ดีนะ',
        'คิดเองบ้างนะครับ',
        'ทำคาโบนาร่าสิ อย่าใส่ครีมนะ',
        'เวลาเครียดๆ อย่างนี้ต้องลาบกับเบียร์เท่านั้น',
        'รสดีเด็ดเถอะ',
        'จะกินข้าวแล้วเหรอ ผมยังไม่หิวเลย',
    ]

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
            bot_message(random.choice(ask_for_food))
        )

    if main_intent == 'what_not_to_eat':
        line_bot_api.reply_message(
            event.reply_token,
            bot_message('ตึกจุล')
        )

    if main_intent == 'what_time':

        request_timezone = resp.get('entities', {}).get('timezone', [{}])[0].get('value', '')
        if type(request_timezone) == dict:
            request_timezone = request_timezone.get('value', '')
        if request_timezone:

            known_timezone = {
                'ไทย': 'Asia/Bangkok',
                'ญี่ปุ่น': 'Asia/Tokyo',
                'ซานฟราน': 'America/Los_Angeles',
                'อังกฤษ': 'Europe/London',
                'ออสเตรีย': 'Europe/Vienna',
                'กรุงโซล': 'Asia/Seoul',
            }

            tz_str = known_timezone.get(request_timezone, None) or cache.get('timezone_%s' % request_timezone)

            if not tz_str:
                geocode_result = gmaps.geocode(request_timezone)
                print(geocode_result)
                if len(geocode_result) > 0:
                    location = geocode_result[0]['geometry']['location']
                    tz_gmap = gmaps.timezone((location['lat'], location['lng']))
                    print(tz_gmap)
                    tz_str = tz_gmap['timeZoneId']

            if tz_str:

                current_time = timezone.now().astimezone(pytz.timezone(tz_str))

                line_bot_api.reply_message(
                    event.reply_token,
                    bot_message('ขณะนี้เป็นเวลา %s นาฬิกา %s นาที %s วินาที ปี้ป' % (current_time.strftime('%H'), current_time.strftime('%M'), current_time.strftime('%S')))
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    bot_message('ไม่รู้ฮะว่าที่นั่นกี่โมง')
                )

        else:
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

    # regular expression for dice
    dice_reg = r'^#?([0-9]+)?d([0-9]+)(\+([0-9]+))?'
    matchObject = re.match(dice_reg, event.message.text)
    if matchObject:
        dice_count = int(matchObject.group(1) or '1')
        dice_type = int(matchObject.group(2))
        dice_add = int(matchObject.group(4) or '0')
        if dice_type in [4, 6, 8, 10, 12, 20, 100]:
            if dice_count <= 100:
                result = 0
                for i in range(dice_count):
                    result += random.randint(1, dice_type) if not cache.get('d20switch') else dice_type
                result += dice_add
            else:
                result = 'เยอะขนาดนั้นไปทอยเอาเองนะครับ'
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

    cache.set('d20switch', False, None)


@handler.default()
def default(event):
    save_message(event)


if os.environ.get('TEST_API', ''):
    handle_message(MessageEvent(message=TextMessage(text='ตอนนี้กี่โมงที่ไทยอ่ะบอท')))

try:
    line_bot_api.push_message('U4b1094667bd89d0d3f18cb28fa105680', bot_message(text='bot started'))
except LineBotApiError as e:
    print('Unable to send init msg to kenny')
    print(e)
