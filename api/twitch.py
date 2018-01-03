from datetime import datetime
from django.conf import settings
from django.db import transaction
from api.models import TokenDatabase
import logging
import requests
import socket

logger = logging.getLogger('app')
config = settings.CONFIG


class Twitch(object):
    def __init__(self, uuid):
        self.version = 'kraken.v5'
        self.uuid = uuid
        self.base_url = 'https://api.twitch.tv/kraken'
        self.access_token = self._get_access_token()
        self.channel = {}
        self.stream = {}
        self.stream_id = None
        self.id = None
        self.name = None

    def __repr__(self):
        return 'Twitch API class version: {}'.format(self.version)

    def get_channel(self):
        self._get_channel()
        return self.channel

    def get_stream(self):
        self._get_stream()
        return self.stream

    def send_irc_msg(self, message):
        r = self._send_irc(message)
        return r

    def set_chat_mode(self, command, enable=True):
        if enable:
            r = self._send_irc('/{}'.format(command))
        else:
            r = self._send_irc('/{}off'.format(command))
        return r

    def update_channel(self, title):
        self._get_channel()
        url = '{}/channels/{}'.format(self.base_url, self.id)
        logger.info('url: {}'.format(url))
        headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': '{}'.format(config.get('Provider', 'client_id')),
            'Authorization': 'OAuth {}'.format(self.access_token),
            'Content-Type': 'application/json',
        }
        data = {'channel': {'status': title}}
        r = requests.put(url, json=data, headers=headers)
        return r.json()

    def run_commercial(self, length=30):
        self._get_channel()
        url = '{}/channels/{}/commercial'.format(
            self.base_url, self.id
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

    def get_uptime(self, human=True):
        self._get_stream()
        if self.stream:
            stream_created_at = self.stream['started_at']
            stream_created_date = datetime.strptime(
                stream_created_at, '%Y-%m-%dT%H:%M:%SZ'
            )
            stream_uptime = datetime.utcnow() - stream_created_date
            if human:
                return sec_to_human(stream_uptime.seconds)
            else:
                return stream_uptime.seconds
        else:
            return 'Not Online' if human else None

    def _get_stream(self):
        logger.info('_get_stream')
        if not self.channel:
            self._get_channel()
        if not self.stream:
            url = '{}/streams/{}'.format(self.base_url, self.id)
            headers = {
                'Accept': 'application/vnd.twitchtv.v5+json',
                'Client-ID': '{}'.format(config.get('Provider', 'client_id')),
                'Authorization': 'OAuth {}'.format(self.access_token),
            }
            r = requests.get(url, headers=headers)
            logger.info(r.content)
            d = r.json()
            self.stream = d['stream']
            if self.stream:
                self.stream_id = self.stream['_id']

    def _get_channel(self):
        logger.info('_get_channel')
        if not self.channel:
            url = '{}/channel'.format(self.base_url)
            headers = {
                'Accept': 'application/vnd.twitchtv.v5+json',
                'Client-ID': '{}'.format(config.get('Provider', 'client_id')),
                'Authorization': 'OAuth {}'.format(self.access_token),
            }
            r = requests.get(url, headers=headers)
            logger.info(r.content)
            self.channel = r.json()
            self.id = self.channel['_id']
            self.name = self.channel['name']

    def _send_irc(self, message):
        self._get_channel()
        connect = ('irc.chat.twitch.tv', 6667)

        def send_irc(msg):
            irc.send('{}\n'.format(msg).encode())

        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.settimeout(None)
        irc.connect(connect)
        send_irc('PASS oauth:{}'.format(self.access_token))
        send_irc('NICK {0}'.format(self.name))
        send_irc('PRIVMSG #{} :{}'.format(self.name, message))
        r = irc.recv(1024).decode()
        irc.close()
        return r

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
            'redirect_uri': config.get('Provider', 'redirect_uri'),
        }
        url = '{}/oauth2/token'.format(self.base_url)
        r = requests.post(url, data)
        d = r.json()
        logger.info(d)
        access_token = d['access_token']
        p.refresh = d['refresh_token']
        p.save()
        logger.info('access_token: {}'.format(access_token))
        return access_token


def sec_to_human(seconds):
    try:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h < 1:
            ms = 's' if m > 1 else ''
            o = '{} minute{}'.format(m, ms)
        else:
            hs = 's' if h > 1 else ''
            ms = 's' if m > 1 else ''
            o = '{} hour{} and {} minute{}'.format(h, hs, m, ms)
        return o
    except Exception as error:
        logger.exception(error)
        return None
