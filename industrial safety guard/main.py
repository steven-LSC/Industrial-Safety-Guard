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
from linebot.models import MessageEvent, TextMessage,TextSendMessage, ImageSendMessage, StickerSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage, CameraAction
import boto3
import os
import json
import botocore
import binascii
from pyDes import des, CBC, PAD_PKCS5
import barcode
from barcode.writer import ImageWriter
import qrcode
import cv2
import time
import pyimgur
from datetime import datetime

# 控制現場拍照片
right_now_flag = False

# Line Bot API設定
line_bot_api = LineBotApi('')
handler = WebhookHandler('')

# AWS 帳號設定
ACCESS_KEY_ID = ''
ACCESS_SECRET_KEY = ''

def des_encrypt(secret_key, s):
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    en = k.encrypt(s, padmode=PAD_PKCS5)
    return binascii.b2a_hex(en)


def des_decrypt(secret_key, s):
    iv = secret_key
    k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    de = k.decrypt(binascii.a2b_hex(s), padmode=PAD_PKCS5)
    return de

def detect_PPE():

    client=boto3.client('rekognition',aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,region_name = 'ap-northeast-1')

    source_file='/Users/steven/Desktop/工安管理員/user.jpg'
    imageSource=open(source_file,'rb')
    response = client.detect_protective_equipment(Image={'Bytes': imageSource.read()}, 
        SummarizationAttributes={'MinConfidence':80, 'RequiredEquipmentTypes':['FACE_COVER', 'HAND_COVER', 'HEAD_COVER']})

    face_check = False
    head_check = False
    other_check = False
    
    print('Detected PPE for people in image ') 
    print('\nDetected people\n---------------')
    if len(response['Persons']) == 1:
        other_check = True
        for person in response['Persons']:
            print('Person ID: ' + str(person['Id']))
            print ('Body Parts\n----------')
            body_parts = person['BodyParts']
            if len(body_parts) == 0:
                    print ('No body parts found')
            else:
                for body_part in body_parts:
                    ppe_items = body_part['EquipmentDetections']
                    if body_part['Name'] == 'FACE' and len(ppe_items) > 0:
                        face_check = True
                    if body_part['Name'] == 'HEAD' and len(ppe_items) > 0:
                        head_check = True
                    if len(ppe_items) ==0:
                        print ('No PPE detected on ' + body_part['Name'])
                    else:
                        print('PPE detected on ' + body_part['Name'])

    return [other_check,face_check,head_check]

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
    global right_now_flag
    if event.message.type == "text":
        mtext = event.message.text
        user_id = event.source.user_id
        if mtext == "@準備上工":
            message=TextSendMessage(
                text="請按下拍照，來檢查你的頭盔跟口罩",
                quick_reply=QuickReply(
                    items=[QuickReplyButton(action=CameraAction(label="拍照"))]
                )
            )
            right_now_flag = True
            line_bot_api.push_message(user_id,message)
        else:
            line_bot_api.push_message(user_id,TextSendMessage(text="請按準備上工"))
    
    else:
        print("接收到圖片")
        user_id = event.source.user_id
        if right_now_flag == True:
            message_content = line_bot_api.get_message_content(event.message.id)
            img_dir = "/Users/steven/Desktop/工安管理員/user.jpg"
            open(img_dir, 'w').close()
            with open(img_dir,'wb') as fd:
                for i in message_content.iter_content():
                    fd.write(i)

            print("完成下載使用者上傳的圖片")

            detect_result=detect_PPE()
            if detect_result[0] == False:
                line_bot_api.push_message(user_id,TextSendMessage(text="請重拍，只能拍自己。"))
            else:
                if detect_result[1] == False:
                    line_bot_api.push_message(user_id,TextSendMessage(text="沒戴口罩"))
                elif detect_result[2] == False:
                    line_bot_api.push_message(user_id,TextSendMessage(text="沒戴頭盔"))
                else:
                    line_bot_api.push_message(user_id,TextSendMessage(text="通過了"))
                    
                    # 上傳自拍照到S3
                    data = open('/Users/steven/Desktop/工安管理員/user.jpg', 'rb')
                    s3 = boto3.resource(
                        's3',
                        aws_access_key_id=ACCESS_KEY_ID,
                        aws_secret_access_key=ACCESS_SECRET_KEY,
                    )
                    s3.Bucket("safety-labor-image").put_object(Key=user_id+'.jpg', Body=data)
                    
                    # 加密現在時間
                    right_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    secret_str = des_encrypt('s1071405', right_now)

                    # 建立QR Code
                    img = qrcode.make(data=secret_str)
                    img.save("/Users/steven/Desktop/工安管理員/qrcode.jpg")

                    # 傳到imgur
                    CLIENT_ID = ""
                    PATH = "/Users/steven/Desktop/工安管理員/qrcode.jpg"
                    title = "qrcode"
                    imgur = pyimgur.Imgur(CLIENT_ID)
                    uploaded_image = imgur.upload_image(PATH, title=title)
                    
                    # 傳給使用者
                    line_bot_api.push_message(user_id,ImageSendMessage(original_content_url= uploaded_image.link,preview_image_url= uploaded_image.link))
            right_now_flag = False
        else:
            line_bot_api.push_message(user_id,TextSendMessage(text="請先重新取得開工權"))


if __name__ == '__main__':
    app.run()