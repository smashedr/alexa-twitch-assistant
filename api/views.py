from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.models import TokenDatabase
import json
import logging
import requests

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
        if intent == 'UpdateTitle':
            return update_title(event)
        else:
            raise ValueError('Unknown Intent')
    except Exception as error:
        logger.exception(error)
        speech = alexa_resp('Error. {}.'.format(error), 'Error')
        return alexa_resp(speech, 'Error')


def update_title(event):
    logger.info('UpdateTitle')
    title = event['request']['intent']['slots']['title']['value'].strip()
    logger.info('title: {}'.format(title))
    speech = 'Title will be updated to. {}'.format(title)
    return alexa_resp(speech, 'Update Title')


@transaction.atomic
def get_access_token(uuid):
    logger.info('get_access_token')
    p = TokenDatabase.objects.get(uuid=uuid)
    refresh_token = str(p.refresh)
    data = {
        'client_id': config.get('Provider', 'client_id'),
        'client_secret': config.get('Provider', 'client_secret'),
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'redirect_uri': 'http://fire.cssnr.com:8080/',
    }
    url = 'https://api.twitch.tv/kraken/oauth2/token'
    r = requests.post(url, data)
    d = r.json()
    access_token = d['access_token']
    p.refresh = d['refresh_token']
    p.save()
    logger.info('access_token: {}'.format(access_token))
    return access_token


def alexa_resp(speech, title, status=200, reprompt=None, session_end=True):
    alexa = build_alexa_response(
        {}, build_speech_response(title, speech, reprompt, session_end)
    )
    return JsonResponse(alexa, status=status)


def build_speech_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_alexa_response(session_attributes, speech_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speech_response
    }


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
