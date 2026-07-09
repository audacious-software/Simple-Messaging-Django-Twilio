# pylint: disable=line-too-long, no-member

from django.conf import settings
from django.core.checks import Error, Warning, register # pylint: disable=redefined-builtin

@register()
def check_twilio_settings_defined(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    if ('simple_messaging_switchboard' in settings.INSTALLED_APPS) is False:
        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_CLIENT_ID') is False:
            error = Error('SIMPLE_MESSAGING_TWILIO_CLIENT_ID parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_CLIENT_ID.', obj=None, id='simple_messaging_twilio.E001')
            errors.append(error)

        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN') is False:
            error = Error('SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_AUTH_TOKEN.', obj=None, id='simple_messaging_twilio.E002')
            errors.append(error)

        if hasattr(settings, 'SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER') is False:
            error = Error('SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER parameter not defined', hint='Update configuration to include SIMPLE_MESSAGING_TWILIO_PHONE_NUMBER.', obj=None, id='simple_messaging_twilio.E003')
            errors.append(error)
    else:
        try:        
            from simple_messaging_switchboard.models import Channel # pylint: disable=import-outside-toplevel, import-error

            count = Channel.objects.filter(channel_type__package_name='simple_messaging_twilio').count()

            if count == 0:
                error = Warning('simple_messaging_twilio is installed alongside simple_messaging_switchboard, but no Channels are defined.', hint='Create Channel or consider removing simple_messaging_twilio from settings.INSTALLED_APPS', obj=None, id='simple_messaging_twilio.E004')
                errors.append(error)
        except ProgrammingError:
            pass # Migrations not applied

    return errors
