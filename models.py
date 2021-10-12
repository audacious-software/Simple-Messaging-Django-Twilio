# pylint: disable=line-too-long

from django.conf import settings
from django.core.checks import Error, register

@register()
def check_twilio_settings_defined(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID') is False:
        error = Error('SIMPLE_MESSAGING_TWILIO_CLIENT_ID parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_CLIENT_ID.', obj=None, id='simple_messaging_twilio.E001')
        errors.append(error)

    if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN') is False:
        error = Error('SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN.', obj=None, id='simple_messaging_twilio.E002')
        errors.append(error)

    if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER') is False:
        error = Error('SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER.', obj=None, id='simple_messaging_twilio.E003')
        errors.append(error)

    return errors
