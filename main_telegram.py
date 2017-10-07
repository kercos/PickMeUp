# -*- coding: utf-8 -*-

from main_exception import SafeRequestHandler
import webapp2

import json
import jsonUtil
import logging
from time import sleep
import key
from person import Person


import requests


# ================================
# Telegram Send Request
# ================================
def sendRequest(p, url, data, debugInfo):
    from main import tell_admin
    try:
        resp = requests.post(url, data)
        logging.info('Response: {}'.format(resp.text))
        respJson = json.loads(resp.text)
        success = respJson['ok']
        if success:
            return True
        else:
            status_code = resp.status_code
            error_code = respJson['error_code']
            description = respJson['description']
            if error_code == 403:
                # Disabled user
                p.setEnabled(False, put=True)
                #logging.info('Disabled user: ' + p.getFirstNameLastNameUserName())
            elif error_code == 400 and description == "INPUT_USER_DEACTIVATED":
                p.setEnabled(False, put=True)
                debugMessage = '❗ Input user disactivated: ' + p.getFirstNameLastNameUserName()
                logging.debug(debugMessage)
                tell_admin(debugMessage)
            else:
                debugMessage = '❗ Raising unknown err ({}).' \
                               '\nStatus code: {}\nerror code: {}\ndescription: {}.'.format(
                    debugInfo, status_code, error_code, description)
                logging.error(debugMessage)
                # logging.debug('recipeint_chat_id: {}'.format(recipient_chat_id))
                logging.debug('Telling to {} who is in state {}'.format(p.chat_id, p.state))
                tell_admin(debugMessage)
    except:
        report_exception()

# ================================
# SEND MESSAGE
# ================================

def send_message(p, msg, kb=None, markdown=True, inline_keyboard=False, one_time_keyboard=False,
         sleepDelay=False, hide_keyboard=False, force_reply=False, disable_web_page_preview=False):
    # reply_markup: InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardHide or ForceReply
    if inline_keyboard:
        replyMarkup = {  # InlineKeyboardMarkup
            'inline_keyboard': kb
        }
    elif kb:
        replyMarkup = {  # ReplyKeyboardMarkup
            'keyboard': kb,
            'resize_keyboard': True,
            'one_time_keyboard': one_time_keyboard,
        }
    elif hide_keyboard:
        replyMarkup = {  # ReplyKeyboardHide
            'hide_keyboard': hide_keyboard
        }
    elif force_reply:
        replyMarkup = {  # ForceReply
            'force_reply': force_reply
        }
    else:
        replyMarkup = {}

    data = {
        'chat_id': p.chat_id,
        'text': msg,
        'disable_web_page_preview': disable_web_page_preview,
        'parse_mode': 'Markdown' if markdown else '',
        'reply_markup': json.dumps(replyMarkup),
    }
    debugInfo = "tell function with msg={} and kb={}".format(msg, kb)
    success = sendRequest(p, key.TELEGRAM_API_URL + 'sendMessage', data, debugInfo)
    if success:
        if sleepDelay:
            sleep(0.1)
        return True

# ================================
# SEND LOCATION
# ================================

def sendLocation(chat_id, latitude, longitude, kb=None):
    try:
        data = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude,
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendLocation', data)
        logging.info('send location: {}'.format(resp.text))
        if resp.status_code == 403:
            p = Person.query(Person.chat_id == chat_id).get()
            p.enabled = False
            p.put()
            logging.info('Disabled user: ' + p.getFirstNameLastNameUserName())
    except:
        report_exception()

# ================================
# SEND VOICE
# ================================

def sendVoice(chat_id, file_id):
    try:
        data = {
            'chat_id': chat_id,
            'voice': file_id,
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendVoice', data)
        logging.info('Response: {}'.format(resp.text))
    except:
        report_exception()


# ================================
# SEND PHOTO
# ================================

def sendPhotoViaUrlOrId(chat_id, url_id, kb=None):
    try:
        if kb:
            replyMarkup = {  # ReplyKeyboardMarkup
                'keyboard': kb,
                'resize_keyboard': True,
            }
        else:
            replyMarkup = {}
        data = {
            'chat_id': chat_id,
            'photo': url_id,
            'reply_markup': json.dumps(replyMarkup),
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendPhoto', data)
        logging.info('Response: {}'.format(resp.text))
    except:
        report_exception()

def sendPhotoFromPngImage(chat_id, img_data, filename='image.png'):
    try:
        img = [('photo', (filename, img_data, 'image/png'))]
        data = {
            'chat_id': chat_id,
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendPhoto', data=data, files=img)
        logging.info('Response: {}'.format(resp.text))
    except:
        report_exception()


# ================================
# SEND DOCUMENT
# ================================

def sendDocument(chat_id, file_id):
    try:
        data = {
            'chat_id': chat_id,
            'document': file_id,
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendDocument', data)
        logging.info('Response: {}'.format(resp.text))
    except:
        report_exception()


# ================================
# SEND WAITING ACTION
# ================================

def sendWaitingAction(chat_id, action_tipo='typing', sleep_time=None):
    try:
        data = {
            'chat_id': chat_id,
            'action': action_tipo,
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'sendChatAction', data)
        logging.info('send waiting action: {}'.format(resp.text))
        if resp.status_code==403:
            p = Person.query(Person.chat_id == chat_id).get()
            p.enabled = False
            p.put()
            logging.info('Disabled user: ' + p.getFirstNameLastNameUserName())
        elif sleep_time:
            sleep(sleep_time)
    except:
        report_exception()

# ================================
# HANDLERS
# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        json_response = requests.get(key.TELEGRAM_API_URL + 'getMe').json()
        self.response.write(json.dumps(json_response))
        # self.response.write(json.dumps(json.load(urllib2.urlopen(key.TELEGRAM_API_URL + 'getMe'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        allowed_updates = ["message", "inline_query", "chosen_inline_result", "callback_query"]
        data = {
            'url': key.TELEGRAM_WEBHOOK_URL,
            'allowed_updates': json.dumps(allowed_updates),
        }
        resp = requests.post(key.TELEGRAM_API_URL + 'setWebhook', data)
        logging.info('SetWebhook Response: {}'.format(resp.text))
        self.response.write(resp.text)

class GetWebhookInfo(webapp2.RequestHandler):
    def get(self):
        resp = requests.post(key.TELEGRAM_API_URL + 'getWebhookInfo')
        logging.info('GetWebhookInfo Response: {}'.format(resp.text))
        self.response.write(resp.text)

class DeleteWebhook(webapp2.RequestHandler):
    def get(self):
        resp = requests.post(key.TELEGRAM_API_URL + 'deleteWebhook')
        logging.info('DeleteWebhook Response: {}'.format(resp.text))
        self.response.write(resp.text)

# ================================
# WEBHOOK HANDLER
# ================================
class WebhookHandler(SafeRequestHandler):

    def post(self):
        from main import dealWithUserInteraction
        # urlfetch.set_default_fetch_deadline(60)
        body = jsonUtil.json_loads_byteified(self.request.body)
        logging.info('request body: {}'.format(body))
        # self.response.write(json.dumps(body))

        # update_id = body['update_id']
        if 'message' not in body:
            return
        message = body['message']
        if 'chat' not in message:
            return

        chat = message['chat']
        chat_id = str(chat['id'])
        if 'first_name' not in chat:
            return
        text = message.get('text') if 'text' in message else ''
        name = chat['first_name']
        last_name = chat['last_name'] if 'last_name' in chat else None
        username = chat['username'] if 'username' in chat else None
        location = message['location'] if 'location' in message else None
        contact = message['contact'] if 'contact' in message else None
        photo = message.get('photo') if 'photo' in message else None
        document = message.get('document') if 'document' in message else None
        voice = message.get('voice') if 'voice' in message else None

        dealWithUserInteraction(
            chat_id, name, last_name, username,
            application='telegram', text=text,
            location=location, contact=contact,
            photo=photo, document=document, voice=voice
        )

def report_exception():
    from main import tell_admin
    import traceback
    msg = "❗ Detected Exception: " + traceback.format_exc()
    tell_admin(msg)
    logging.error(msg)
