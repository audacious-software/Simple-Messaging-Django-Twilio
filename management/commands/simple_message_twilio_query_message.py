# pylint: disable=no-member, line-too-long, superfluous-parens

import json

from django.conf import settings
from django.core.management.base import BaseCommand

from twilio.rest import Client

class Command(BaseCommand):
    help = 'Queries Twilio for message status'

    def add_arguments(self, parser):
        parser.add_argument('sid', type=str, help='SID of Twilio message')

        parser.add_argument('--client_id', type=str, help='Twilio Client ID', required=False)
        parser.add_argument('--auth_token', type=str, help='Twilio Authorization Token', required=False)

    def handle(self, *args, **options):
        twilio_client_id = options.get('client_id', None)

        if twilio_client_id is None:
            if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID'):
                twilio_client_id = settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID

        twilio_auth_token = options.get('auth_token', None)

        if twilio_auth_token is None:
            if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN'):
                twilio_auth_token = settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN

        if (twilio_client_id is not None) and (twilio_auth_token is not None):
            client = Client(twilio_client_id, twilio_auth_token)

            message = client.messages(options.get('sid', '')).fetch() # pylint: disable=not-callable

            context = message._proxy # pylint: disable=protected-access

            payload = context._version.fetch(method="GET", uri=context._uri) # pylint: disable=protected-access

            print(json.dumps(payload, indent=2))
        else:
            print('Please provide a valid Twilio client ID and auth token or specify one in settings.py (SIMPLE_MESSAGING_TWILIO_CLIENT_ID, SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN).')
