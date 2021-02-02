import requests
try:
    import xml.etree.cElementTree as ET 
except ImportError:
    import xml.etree.ElementTree as ET

from flask import Flask
app = Flask(__name__)

from flask import Flask, request, abort
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage,TextSendMessage, ImageSendMessage, StickerSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage
import boto3
import os
import json
import botocore
import binascii
from pyDes import des, CBC, PAD_PKCS5
import qrcode
import cv2
import time
from datetime import datetime

# Line Bot API設定
line_bot_api = LineBotApi('')
handler = WebhookHandler('')

def des_decrypt(secret_key, s):
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    de = k.decrypt(binascii.a2b_hex(s), padmode=PAD_PKCS5)
    return de

@app.route("/callback", methods=['POST'])

def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message= (TextMessage,ImageMessage))

def handle_message(event):

    if event.message.type == "text":

        mtext = event.message.text
        user_id = event.source.user_id
        f = open("mode.txt",'w')
        if mtext == "@安全門模式":
            f.write("1")
            line_bot_api.push_message(user_id,TextSendMessage(text="已轉換成安全門模式"))
        elif mtext == "@結算模式":
            f.write("2")
            line_bot_api.push_message(user_id,TextSendMessage(text="已轉換成結算模式"))
        else:
            f.write("1")
            line_bot_api.push_message(user_id,TextSendMessage(text="請傳送QRCode"))
        f.close()

    else:
        print("接收到圖片")
        message_content = line_bot_api.get_message_content(event.message.id)
        user_id = event.source.user_id

        # 下載使用者上傳的圖片到user_id.jpg
        img_dir = "qrcode.jpg"
        open(img_dir, 'w').close()
        with open(img_dir,'wb') as fd:
            for i in message_content.iter_content():
                fd.write(i)

        im = cv2.imread("qrcode.jpg")
        det = cv2.QRCodeDetector()
        retval, points, straight_qrcode = det.detectAndDecode(im)
        start_time = des_decrypt('s1071405', retval).decode("utf-8")
        start_time = datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')

        right_now = datetime.now()
        gap = right_now-start_time
        gap = gap.seconds
        minute = gap / 60
        hour = int(minute / 60) - 16
        minute = int(minute % 60)

        f = open("mode.txt",mode='r')
        if f.read() == "1":
            print("安全門模式")
            if hour > 0 or minute > 10:
                line_bot_api.push_message(user_id,TextSendMessage(text="檢測時間與通過時間間隔過長，拒絕進入。"))
            else:
                line_bot_api.push_message(user_id,TextSendMessage(text="通過，請進入工地。"))
        else:
            working_time = "工作時長："+str(hour)+" 小時 "+str(minute)+" 分鐘"
            line_bot_api.push_message(user_id,TextSendMessage(text=working_time))


if __name__ == '__main__':
    app.run()