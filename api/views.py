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
        elif intent == 'EmoteOnly':
            return emote_only(event)
        else:
            raise ValueError('Unknown Intent')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error. {}'.format(error), 'Error')


def emote_only(event):
    logger.info('EmoteOnly')
    status = event['request']['intent']['slots']['status']['value']
    logger.info('status: {}'.format(status))
    twitch = Twitch(event['session']['user']['accessToken'])
    if status == 'on' or status == 'enable':
        twitch.emote_only(True)
        return alexa_resp('Emote Only mode turned on.', 'Emote Only')
    elif staticmethod == 'off' or status == 'disable':
        twitch.emote_only(False)
        return alexa_resp('Emote Only mode turned off.', 'Emote Only')
    else:
        speech = 'Not sure if you want to turn emote only mode on or off.'
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
