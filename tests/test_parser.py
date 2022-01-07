import unittest

from core.objects import Message, UserInfo
from core.parser import parse


class TestParseMessage(unittest.TestCase):

    def test_parse_message(self) -> None:
        sample_message = ':xchromium7!xchromium7@xchromium7.tmi.twitch.tv PRIVMSG #xchrombot :!drop'
        message: Message = parse(sample_message)
        self.assertEqual(message.user, 'xchromium7')
        self.assertEqual(message.channel, 'xchrombot')
        self.assertEqual(message.irc_command, 'PRIVMSG')
        self.assertEqual(message.text_command, 'drop')
        self.assertEqual(message.text_args, [])
        self.assertEqual(message.text, '!drop')

    def test_parse_message_with_tag(self) -> None:
        sample_message = (
            '@badge-info=;badges=;client-nonce=42ef7105da542f903e76632b768ab844;'
            'color=#5F9EA0;display-name=xchromium7;emotes=;first-msg=0;flags=;id=3f23c8a6-30ee-442c-84ff-ad318fedf60e;'
            'mod=0;room-id=746006571;subscriber=0;tmi-sent-ts=1638066687071;turbo=0;user-id=69618261;user-type= '
            ':xchromium7!xchromium7@xchromium7.tmi.twitch.tv PRIVMSG #xchrombot :!drop'
        )
        message: Message = parse(sample_message)
        # Message content should be equal to the first test
        self.assertEqual(message.channel, 'xchrombot')
        self.assertEqual(message.irc_command, 'PRIVMSG')
        self.assertEqual(message.text_command, 'drop')
        self.assertEqual(message.text_args, [])
        self.assertEqual(message.text, '!drop')
        user = message.user
        self.assertIsInstance(user, UserInfo)
        self.assertEqual(user.display_name, 'xchromium7')
        self.assertEqual(user.user_id, '69618261')
        self.assertEqual(user.user_type, '')
        self.assertEqual(user.color, '#5F9EA0')
        self.assertEqual(user.badges, '')
        self.assertEqual(user.badge_info, '')
        self.assertEqual(user.emotes, '')
        self.assertEqual(user.flags, '')
        self.assertEqual(user.id, '3f23c8a6-30ee-442c-84ff-ad318fedf60e')
        self.assertEqual(user.tmi_sent_ts, '1638066687071')
        self.assertEqual(user.client_nonce, '42ef7105da542f903e76632b768ab844')
        self.assertFalse(user.subscriber)
        self.assertFalse(user.turbo)
        self.assertFalse(user.mod)
        self.assertFalse(user.first_msg)
        self.assertFalse(user.emote_only)

