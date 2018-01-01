from django.conf import settings
from django.db import transaction
from api.models import TokenDatabase
import logging
import requests

logger = logging.getLogger('app')
config = settings.CONFIG


class Twitch(object):
    def __init__(self, uuid):
        self.uuid = uuid
        self.access_token = self._get_access_token()
        self.channel = {}
        self.url = 'https://api.twitch.tv/kraken'

    def get_channel(self):
        self._get_channel()
        return self.channel

    def run_commercial(self, length=30):
        self._get_channel()
        url = '{}/channels/{}/commercial'.format(
            self.url, self.channel['_id']
        )
        logger.info(url)
        headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': '{}'.format(config.get('Provider', 'client_id')),
            'Authorization': 'OAuth {}'.format(self.access_token),
            'Content-Type': 'application/json',
        }
        data = {'length': length}
        r = requests.post(url, data, headers=headers)
        logger.info(r.content)
        return r.json()

    def _get_channel(self):
        logger.info('_get_channel')
        if not self.channel:
            url = '{}/channel'.format(self.url)
            headers = {
                'Accept': 'application/vnd.twitchtv.v5+json',
                'Client-ID': '{}'.format(config.get('Provider', 'client_id')),
                'Authorization': 'OAuth {}'.format(self.access_token),
            }
            r = requests.get(url, headers=headers)
            logger.info(r.content)
            self.channel = r.json()

    @transaction.atomic
    def _get_access_token(self):
        logger.info('_get_access_token')
        p = TokenDatabase.objects.get(uuid=self.uuid)
        refresh_token = str(p.refresh)
        data = {
            'client_id': config.get('Provider', 'client_id'),
            'client_secret': config.get('Provider', 'client_secret'),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'redirect_uri': 'http://fire.cssnr.com:8080/',
        }
        url = '{}/oauth2/token'.format(self.url)
        r = requests.post(url, data)
        d = r.json()
        logger.info(d)
        access_token = d['access_token']
        p.refresh = d['refresh_token']
        p.save()
        logger.info('access_token: {}'.format(access_token))
        return access_token
