# pylint: disable=line-too-long

import json
import traceback

from django_dialog_engine.dialog import BaseNode, DialogTransition

class SendMediaMessageNode(BaseNode):
    @staticmethod
    def parse(dialog_def):
        if dialog_def['type'] == 'send-media-message':
            try:
                message_node = SendMediaMessageNode(dialog_def['id'], dialog_def['next_id'], dialog_def.get('media_url', None), dialog_def.get('message', None))

                return message_node
            except KeyError:
                traceback.print_exc()

        return None

    def __init__(self, node_id, next_node_id, media_url, message):# pylint: disable=too-many-arguments
        super(SendMediaMessageNode, self).__init__(node_id, node_id) # pylint: disable=super-with-arguments

        self.next_node_id = next_node_id
        self.media_url = media_url
        self.message = message

    def node_type(self):
        return 'send-media-message'

    def str(self):
        definition = {
            'id': self.node_id,
            'next_id': self.next_node_id,
            'media_url': self.media_url,
            'message': self.message,
        }

        return json.dumps(definition, indent=2)

    def evaluate(self, dialog, response=None, last_transition=None, extras=None, logger=None): # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements, unused-argument
        if extras is None:
            extras = {}

        transition = DialogTransition(new_state_id=self.next_node_id)

        transition.metadata['reason'] = 'echo-media-continue'

        transition.metadata['exit_actions'] = [{
            'type': 'echo',
            'message': self.message,
            'media_url': self.media_url,
        }]

        return transition

    def actions(self):
        return []

    def next_nodes(self):
        nodes = [
            (self.next_node_id, 'Next',),
        ]

        return nodes

    def node_definition(self):
        node_def = super().node_definition() # pylint: disable=missing-super-argument

        node_def['message'] = self.message

        return node_def

    def search_text(self):
        values = ['echo-media']

        if self.message is not None:
            values.append(self.message)

        if self.media_url is not None:
            values.append(self.media_url)

        if self.next_node_id is not None:
            values.append(self.next_node_id)

        return '%s\n%s' % (super().search_text(), '\n'.join(values)) # pylint: disable=missing-super-argument


def dialog_builder_cards():
    return [
        ('Twilio: Send Media Message', 'send-media-message',),
    ]
