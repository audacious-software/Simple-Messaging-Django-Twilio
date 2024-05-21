# pylint: disable=line-too-long, no-member, len-as-condition, import-outside-toplevel

import datetime

import pytz
import requests

import twilio

from twilio.rest import Client

from django.conf import settings
from django.utils import timezone

def dashboard_signals():
    signals = []

    if 'simple_messaging_switchboard' in settings.INSTALLED_APPS:
        return signals

    try: # If set up without Switchboard...
        client_id = settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID
        auth_token = settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN
        phone_number = settings.SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER

        if (None in (client_id, auth_token, phone_number)) is False:
            signals.append({
                'name': 'Twilio: %s' % phone_number,
                'refresh_interval': 1800,
                'configuration': {
                    'widget_columns': 6,
                    'active': True,
                }
            })
    except AttributeError:
        pass

    return signals

def dashboard_template(signal_name):
    if signal_name.startswith('Twilio:'):
        return 'dashboard/simple_dashboard_widget_twilio_status.html'

    return None

def update_dashboard_signal_value(signal_name, client_id=None, auth_token=None, phone_number=None, window_days=28, root_client_id=None, root_auth_token=None): # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    if signal_name.startswith('Twilio:'):
        value = {
            'dates': []
        }

        try:
            if client_id is None:
                client_id = settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID

            if auth_token is None:
                auth_token = settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN

            if phone_number is None:
                phone_number = settings.SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER

            client = Client(client_id, auth_token)

            here_tz = pytz.timezone(settings.TIME_ZONE)

            today = timezone.now().astimezone(here_tz).date()

            start_date = today - datetime.timedelta(days=window_days)

            index_date = start_date

            while index_date <= today:
                date_value = {
                    'date': index_date.isoformat(),
                    'incoming_count': 0,
                    'incoming_error_count': 0,
                    'outgoing_count': 0,
                    'outgoing_error_count': 0,
                }

                date_sent = datetime.datetime(index_date.year, index_date.month, index_date.day, 0, 0, 0)

                incoming_messages = client.messages.list(to=phone_number, date_sent=date_sent)

                for message in incoming_messages:
                    if message.error_code is None:
                        date_value['incoming_count'] += 1
                    else:
                        date_value['incoming_error_count'] += 1

                outgoing_messages = client.messages.list(from_=phone_number, date_sent=date_sent)

                for message in outgoing_messages:
                    if message.error_code is None:
                        date_value['outgoing_count'] += 1
                    else:
                        date_value['outgoing_error_count'] += 1

                value['dates'].append(date_value)

                index_date += datetime.timedelta(days=1)

            if root_client_id is None:
                if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_MAIN_CLIENT_ID'):
                    root_client_id = settings.SIMPLE_MESSAGING_TWILIO_MAIN_CLIENT_ID
                else:
                    root_client_id = client_id

            if root_auth_token is None:
                if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_MAIN_AUTH_TOKEN'):
                    root_auth_token = settings.SIMPLE_MESSAGING_TWILIO_MAIN_AUTH_TOKEN
                else:
                    root_auth_token = auth_token

            balances_url = 'https://api.twilio.com/2010-04-01/Accounts/%s/Balance.json' % root_client_id

            basic_auth = requests.auth.HTTPBasicAuth(root_client_id, root_auth_token)

            response = requests.get(balances_url, auth=basic_auth)

            value['balance'] = response.json()

            if 'balance' in value['balance']:
                value['display_value'] = '%s incoming msgs., %s outgoing msgs., %s %s remaining' % (date_value['incoming_count'], date_value['outgoing_count'], value['balance']['balance'], value['balance']['currency'])
            else:
                value['display_value'] = '%s incoming msgs., %s outgoing msgs.' % (date_value['incoming_count'], date_value['outgoing_count'],)

            return value

        except AttributeError:
            pass
        except twilio.base.exceptions.TwilioException: # Encountered in testing or setup contexts
            pass

    return None
