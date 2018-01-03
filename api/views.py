from django.conf import settings
from django.shortcuts import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.twitch import Twitch
from api.alexa import alexa_resp
import json
import logging

logger = logging.getLogger('app')
config = settings.CONFIG


@require_http_methods(["GET"])
def api_home(request):
    log_req(request)
    return HttpResponse('API Online')


@csrf_exempt
@require_http_methods(["POST"])
def alexa_post(request):
    log_req(request)
    try:
        body = request.body.decode('utf-8')
        event = json.loads(body)
        logger.info(event)
        intent = event['request']['intent']['name']
        if intent == 'GetTitle':
            return get_title(event)
        elif intent == 'UpdateTitle':
            return update_title(event)
        elif intent == 'RunCommercial':
            return run_commercial(event)
        elif intent == 'ChatStatus':
            return chat_status(event)
        elif intent == 'ClearChat':
            return clear_chat(event)
        elif intent == 'SendChat':
            return send_chat(event)
        else:
            raise ValueError('Unknown Intent')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error. {}'.format(error), 'Error')


def send_chat(event):
    logger.info('SendChat')
    message = event['request']['intent']['slots']['message']['value']
    twitch = Twitch(event['session']['user']['accessToken'])
    twitch.send_irc_msg(message)
    return alexa_resp('Message sent.', 'Send Chat Message')


def clear_chat(event):
    logger.info('ChatStatus')
    twitch = Twitch(event['session']['user']['accessToken'])
    twitch.send_irc_msg('/clear')
    return alexa_resp('Chat has been cleared.', 'Clear Chat')


def chat_status(event):
    logger.info('ChatStatus')
    status = event['request']['intent']['slots']['status']['value']
    mode = event['request']['intent']['slots']['mode']['value']
    logger.info('status: {}'.format(status))
    logger.info('mode: {}'.format(mode))

    if 'emote' in mode:
        chat_mode = 'emoteonly'
    elif 'nine' in mode:
        chat_mode = 'r9kbeta'
    elif 'slow' in mode:
        chat_mode = 'slow'
    elif 'follower' in mode:
        chat_mode = 'followers'
    else:
        speech = 'Unknown chat mode. {}'.format(mode)
        return alexa_resp(speech, 'Unknown Chat Mode')

    twitch = Twitch(event['session']['user']['accessToken'])
    if status == 'on' or status == 'enable':
        twitch.set_chat_mode(chat_mode, True)
        speech = '{} mode turned on.'.format(mode)
        return alexa_resp(speech, 'Chat Mode')
    elif staticmethod == 'off' or status == 'disable':
        twitch.set_chat_mode(chat_mode, False)
        speech = '{} mode turned off.'.format(mode)
        return alexa_resp(speech, 'Chat Mode')
    else:
        speech = 'Was unsure if you wanted to turn the mode on or off.'
        return alexa_resp(speech, 'Unknown Action')


def update_title(event):
    logger.info('UpdateTitle')
    title = event['request']['intent']['slots']['title']['value']
    title = title.title()
    logger.info('title: {}'.format(title))
    twitch = Twitch(event['session']['user']['accessToken'])
    update = twitch.update_channel(title)
    logger.info(update)
    speech = 'Your title has been updated too. {}'.format(title)
    return alexa_resp(speech, 'Update Title')


def get_title(event):
    logger.info('GetTitle')
    twitch = Twitch(event['session']['user']['accessToken'])
    channel = twitch.get_channel()
    logger.info(channel)
    title = channel['status']
    logger.info('title: {}'.format(title))
    speech = 'Your current title is. {}'.format(title)
    return alexa_resp(speech, 'Current Title')


def run_commercial(event):
    logger.info('RunCommercial')
    twitch = Twitch(event['session']['user']['accessToken'])
    commercial = twitch.run_commercial()
    logger.info(commercial)
    speech = 'A commercial has been started.'
    return alexa_resp(speech, 'Commercial Started')


def log_req(request):
    """
    DEBUGGING ONLY
    """
    data = None
    if request.method == 'GET':
        data = 'GET: '
        for key, value in request.GET.items():
            data += '"%s": "%s", ' % (key, value)
    if request.method == 'POST':
        data = 'POST: '
        for key, value in request.POST.items():
            data += '"%s": "%s", ' % (key, value)
    if data:
        data = data.strip(', ')
        logger.info(data)
        json_string = '{%s}' % data
        return json_string
    else:
        return None
