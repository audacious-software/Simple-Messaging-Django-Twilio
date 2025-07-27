# pylint: disable=line-too-long, no-member

import importlib
import json
import logging
import mimetypes

from io import BytesIO

import requests
import phonenumbers

from twilio.rest import Client

from django.conf import settings
from django.core import files
from django.http import HttpResponse
from django.utils import timezone

from simple_messaging.models import IncomingMessage, IncomingMessageMedia, BlockedSender
from simple_messaging.utils import split_into_bundles

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

def process_outgoing_message(outgoing_message, metadata=None): # pylint: disable=too-many-branches
    if metadata is None:
        metadata = {}

    twilio_client_id = metadata.get('client_id', None)

    if twilio_client_id is None:
        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID'):
            twilio_client_id = settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID
        else:
            return None
    else:
        del metadata['client_id']

    twilio_auth_token = metadata.get('auth_token', None)

    if twilio_auth_token is None:
        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN'):
            twilio_auth_token = settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN
        else:
            return None
    else:
        del metadata['auth_token']

    twilio_phone_number = metadata.get('phone_number', None)

    if twilio_phone_number is None:
        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER'):
            twilio_phone_number = settings.SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER
        else:
            return None
    else:
        del metadata['phone_number']

    if (twilio_client_id is not None) and (twilio_auth_token is not None) and (twilio_phone_number is not None):
        client = Client(twilio_client_id, twilio_auth_token)

        transmission_metadata = {}

        if outgoing_message.transmission_metadata is not None:
            try:
                transmission_metadata = json.loads(outgoing_message.transmission_metadata)
            except ValueError:
                transmission_metadata = {}

        destination = metadata.get('destination', None)

        if destination is None:
            destination = outgoing_message.current_destination()

        twilio_message = None

        if outgoing_message.message.startswith('image:'):
            twilio_message = client.messages.create(to=destination, from_=twilio_phone_number, media_url=[outgoing_message.message[6:]])
        else:
            twilio_sids = []

            for outgoing_file in outgoing_message.media.all().order_by('index'):
                file_url = '%s%s' % (settings.SITE_URL, outgoing_file.content_file.url)

                twilio_message = client.messages.create(to=destination, from_=twilio_phone_number, media_url=file_url)

                twilio_sids.append(twilio_message.sid)

            outgoing_message_content = outgoing_message.fetch_message(transmission_metadata)

            if outgoing_message_content.strip() != '':
                outgoing_messages = split_into_bundles(outgoing_message_content.strip(), bundle_size=1000)

                for outgoing_message_chunk in outgoing_messages:
                    twilio_message = client.messages.create(to=destination, from_=twilio_phone_number, body=outgoing_message_chunk)

                    twilio_sids.append(twilio_message.sid)

            metadata['twilio_sid'] = twilio_sids

        return metadata

    return None

def simple_messaging_media_enabled(outgoing_message): # pylint: disable=unused-argument
    try:
        return settings.SIMPLE_MESSAGING_MEDIA_ENABLED
    except AttributeError:
        pass

    return True

def process_incoming_request(request): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    if request.POST.get('MessageSid', None) is None:
        return None

    response = '<?xml version="1.0" encoding="UTF-8" ?><Response>'

    responses = []

    for app in settings.INSTALLED_APPS:
        try:
            response_module = importlib.import_module('.simple_messaging_api', package=app)

            responses.extend(response_module.simple_messaging_response(request.POST))
        except ImportError:
            pass
        except AttributeError:
            pass

    for message in responses:
        response += '<Message>' + message + '</Message>'

    response += '</Response>'

    if request.method == 'POST': # pylint: disable=too-many-nested-blocks
        sender = request.POST['From']

        if BlockedSender.objects.filter(sender=sender).count() > 0:
            response = '<?xml version="1.0" encoding="UTF-8" ?><Response></Response>'

            logging.info('[simple_messaging_twilio] Blocked incoming message from %s.', sender)

            return HttpResponse(response, content_type='text/xml')

        record_responses = True

        for app in settings.INSTALLED_APPS:
            try:
                response_module = importlib.import_module('.simple_messaging_api', package=app)

                record_responses = response_module.simple_messaging_record_response(request.POST)
            except ImportError:
                pass
            except AttributeError:
                pass

        if record_responses:
            now = timezone.now()

            destination = request.POST['To']

            incoming = IncomingMessage(recipient=destination, sender=sender)
            incoming.receive_date = now
            incoming.message = request.POST['Body'].strip()
            incoming.transmission_metadata = json.dumps(dict(request.POST), indent=2)

            incoming.save()

            incoming.encrypt_sender()

            num_media = 0

            media_objects = {}

            if 'NumMedia' in request.POST:
                num_media = int(request.POST['NumMedia'])

                for i in range(0, num_media):
                    media = IncomingMessageMedia(message=incoming)

                    media.content_url = request.POST['MediaUrl' + str(i)]
                    media.content_type = request.POST['MediaContentType' + str(i)]
                    media.index = i

                    media.save()

                    media_response = requests.get(media.content_url, timeout=120)

                    if media_response.status_code != requests.codes.ok:
                        continue

                    filename = media.content_url.split('/')[-1]

                    extension = mimetypes.guess_extension(media.content_type)

                    if extension is not None:
                        if extension == '.jpe':
                            extension = '.jpg'

                        filename += extension

                    file_bytes = BytesIO()
                    file_bytes.write(media_response.content)

                    media.content_file.save(filename, files.File(file_bytes))
                    media.save()

                    media_objects[filename] = {
                        'content': file_bytes.getvalue(),
                        'mime-type': media.content_type
                    }

            for app in settings.INSTALLED_APPS:
                try:
                    response_module = importlib.import_module('.simple_messaging_api', package=app)

                    response_module.process_incoming_message(incoming)
                except ImportError:
                    pass
                except AttributeError:
                    pass

    return HttpResponse(response, content_type='text/xml')

def lookup_numbers(phone_numbers): # pylint: disable=too-many-branches
    results = []

    twilio_client_id = None
    twilio_auth_token = None

    try:
        from simple_messaging_switchboard.models import Channel # pylint: disable=import-outside-toplevel

        for channel in Channel.objects.all():
            if channel.channel_type.package_name == 'simple_messaging_twilio':
                config = json.loads(channel.configuration)

                if 'client_id' in config and 'auth_token' in config:
                    twilio_client_id = config['client_id']
                    twilio_auth_token = config['auth_token']

            if twilio_client_id == '':
                twilio_client_id = None

            if twilio_auth_token == '': # nosec
                twilio_auth_token = None

            if twilio_client_id is not None and twilio_auth_token is not None:
                break
    except ImportError:
        pass

    if twilio_client_id is None and hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID'):
        twilio_client_id = settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID

    if twilio_auth_token is None and hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN'):
        twilio_auth_token = settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN


    if None in (twilio_client_id, twilio_auth_token,):
        return results

    client = Client(twilio_client_id, twilio_auth_token)

    for phone_number in phone_numbers:
        result = {}

        try:
            parsed_number = phonenumbers.parse(phone_number, settings.SIMPLE_MESSAGING_COUNTRY_CODE)
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

            lookup = client.lookups.v2.phone_numbers(formatted_number).fetch(fields='line_type_intelligence')

            if lookup.line_type_intelligence is None:
                result['number'] = phone_number
                result['type'] = 'Unparseable or invalid phone number'
                result['carrier'] = 'Unknown'
                result['notes'] = 'Unable to parse phone number "' + phone_number + '". Please verify that it was entered correctly.'
            else:
                result['number'] = lookup.phone_number
                result['type'] = lookup.line_type_intelligence.get('type', 'Unknown')
                result['carrier'] = lookup.line_type_intelligence.get('carrier_name', 'Unknown')

                if lookup.line_type_intelligence.get('valid', False):
                    result['notes'] = 'Number reported as invalid. Please verify that it was entered correctly.'

        except phonenumbers.phonenumberutil.NumberParseException:
            result['number'] = phone_number
            result['type'] = 'Unparseable or invalid phone number'
            result['carrier'] = 'Unknown'
            result['notes'] = 'Unable to parse phone number "' + phone_number + '". Please verify that it was entered correctly.'

        results.append(result)

    return results

def fetch_sync_messages(since): # pylint: disable=too-many-locals
    channels = []

    try:
        from simple_messaging_switchboard.models import Channel # pylint: disable=import-outside-toplevel

        for channel in Channel.objects.all():
            if channel.channel_type.package_name == 'simple_messaging_twilio':
                config = json.loads(channel.configuration)

                if 'client_id' in config and 'auth_token' in config and 'phone_number' in config and 'country_code' in config:
                    twilio_client_id = config['client_id']
                    twilio_auth_token = config['auth_token']
                    phone_number = config['phone_number']
                    country_code = config['country_code']

                    channels.append((phone_number, country_code, twilio_client_id, twilio_auth_token, channel.identifier))
    except ImportError:
        pass

    if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID') and hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN') and hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER') and hasattr(settings, 'SIMPLE_MESSAGING_COUNTRY_CODE'):
        channels.append((
            settings.SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER,
            settings.SIMPLE_MESSAGING_COUNTRY_CODE,
            settings.SIMPLE_MESSAGING_TWILIO_CLIENT_ID,
            settings.SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN,
            'default',
        ))

    messages = []

    for channel in channels:
        channel_client = Client(channel[2], channel[3])

        parsed_number = phonenumbers.parse(channel[0], channel[1])
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

        for twilio_message in channel_client.messages.list(to=formatted_number, date_sent_after=since):
            message = {
                'id': {
                    'SmsMessageSid': twilio_message.sid,
                    'twilio_sid': twilio_message.sid,
                },
                'message_channel': channel[4],
                'to': twilio_message.to,
                'from': twilio_message.from_,
                'message': twilio_message.body,
                'sent': twilio_message.date_sent,
                'direction': 'incoming',
                'metadata': {
                    'error': twilio_message.error_message,
                    'status': twilio_message.status,
                },
                'media': [],
            }

            for media in twilio_message.media.list():
                message['media'].append({
                    'content_type': media.content_type,
                    'url': 'https://api.twilio.com%s' % media.uri[:-5]
                })

            messages.append(message)

        for twilio_message in channel_client.messages.list(from_=formatted_number, date_sent_after=since):
            message = {
                'id': {
                    'SmsMessageSid': twilio_message.sid,
                    'twilio_sid': twilio_message.sid,
                },
                'message_channel': channel[4],
                'to': twilio_message.to,
                'from': twilio_message.from_,
                'message': twilio_message.body,
                'sent': twilio_message.date_sent,
                'direction': 'outgoing',
                'metadata': {
                    'error': twilio_message.error_message,
                    'status': twilio_message.status,
                },
                'media': [],
            }

            for media in twilio_message.media.list():
                message['media'].append({
                    'content_type': media.content_type,
                    'url': 'https://api.twilio.com%s' % media.uri[:-5]
                })

            messages.append(message)

    return messages
