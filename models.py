# pylint: disable=line-too-long, no-member

from django.db.utils import ProgrammingError

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


@register()
def check_twilio_channels_defined(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    if 'simple_messaging_switchboard' in settings.INSTALLED_APPS: # pylint: disable=too-many-nested-blocks
        from simple_messaging_switchboard.models import ChannelType, Channel # pylint: disable=import-outside-toplevel, import-error

        try:
            twilio_type = ChannelType.objects.filter(package_name='simple_messaging_twilio').first()

            if twilio_type is None:
                error = Warning('simple_messaging_twilio installed, but no corresponding Channel Type exists.', hint='Add Channel Type with the "simple_messaging_twilio" package type.', obj=None, id='simple_messaging_twilio.W001')
                errors.append(error)
            else:
                twilio_channels = Channel.objects.filter(channel_type=twilio_type)

                if twilio_channels.count() == 0:
                    error = Warning('simple_messaging_twilio installed, but no corresponding Channel installed.', hint='Add Channel with the "simple_messaging_twilio" channel type. Disable if needed.', obj=None, id='simple_messaging_twilio.W002')
                    errors.append(error)
                else:
                    for twilio_channel in twilio_channels:
                        config = twilio_channel.fetch_configuration()

                        if ('client_id' in config) is False:
                            error = Warning('Channel %s missing client_id parameter.' % twilio_channel, hint='Add Twilio SID as the client_id field.', obj=None, id='simple_messaging_twilio.W003')
                            errors.append(error)

                        if ('auth_token' in config) is False:
                            error = Warning('Channel %s missing auth_token parameter.' % twilio_channel, hint='Add Twilio authorization token as the auth_token field.', obj=None, id='simple_messaging_twilio.W004')
                            errors.append(error)

                        if ('phone_number' in config) is False:
                            error = Warning('Channel %s missing phone_number parameter.' % twilio_channel, hint='Add Twilio phone number as the phone_number field.', obj=None, id='simple_messaging_twilio.W005')
                            errors.append(error)

                        if ('country_code' in config) is False:
                            error = Warning('Channel %s missing country_code parameter.' % twilio_channel, hint='Add Twilio country code as the country_code field.', obj=None, id='simple_messaging_twilio.W006')
                            errors.append(error)

        except ProgrammingError:
            pass # Migrations not applied

    return errors
