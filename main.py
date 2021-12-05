from collections import namedtuple
import datetime
import json
import os
import socket
import ssl
from typing import Any, Dict, Optional

import dotenv

from core.utils import remove_prefix


dotenv.load_dotenv()


Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args'
)


#@badge-info=;badges=;client-nonce=42ef7105da542f903e76632b768ab844;
#color=#5F9EA0;display-name=xchromium7;emotes=;first-msg=0;flags=;id=3f23c8a6-30ee-442c-84ff-ad318fedf60e;
#mod=0;room-id=746006571;subscriber=0;tmi-sent-ts=1638066687071;turbo=0;user-id=69618261;user-type= :xchromium7!xchromium7@xchromium7.tmi.twitch.tv PRIVMSG #xchrombot :!drop

class Bot:
    def __init__(self) -> None:
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6697
        self.oauth_token = os.getenv('OAUTH_TOKEN')
        self.username = os.getenv('TWITCH_USERNAME')
        self.channels = ['wazfu']
        self.command_prefix = '!'
        self.state: Dict[str, Any] = {}
        self.state_filename = 'state.json'
        self.state_schema: Dict[str, Any] = {
            'template_commands': {},
        }
        self.custom_commands = {
            'cmds': self.list_commands,
            'addcmd': self.add_template_command,
            'editcmd': self.edit_template_command,
            'delcmd': self.delete_template_command,
        }

    def init(self) -> None:
        self.read_state()
        self.connect()

    def ensure_state_schema(self) -> bool:
        """
        Make sure the state has the default schema
        """
        is_dirty = False
        for key in self.state_schema:
            if key not in self.state:
                is_dirty = True
                self.state[key] = self.state_schema[key]
        return is_dirty

    def read_state(self) -> None:
        """
        Load states from file
        """
        with open(self.state_filename, 'r') as file:
            self.state = json.load(file)
        is_dirty = self.ensure_state_schema()
        if is_dirty:
            self.write_state()

    def write_state(self) -> None:
        """
        Update file with current state
        """
        with open(self.state_filename, 'w') as file:
            json.dump(self.state, file)

    def send_privmsg(self, channel: str, message: str) -> None:
        self.send_command(f'PRIVMSG #{channel} :{message}')

    def send_command(self, command: str) -> None:
        if 'PASS' not in command:
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode('utf-8'))

    def send_credentials(self) -> None:
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        # self.send_command('CAP REQ :twitch.tv/membership')

    def connect(self) -> None:
        """
        Connect to twitch IRC server
        """
        self.irc = ssl.wrap_socket(socket.socket())
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_credentials()
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, 'is here EleGiggle')
        self.loop_for_messages()

    def loop_for_messages(self) -> None:
        try:
            while True:
                received_messages = self.irc.recv(2048).decode()
                for message in received_messages.split('\r\n'):
                    self.handle_message(message)
        except KeyboardInterrupt:
            print('Terminating bot...')
            for channel in self.channels:
                print(f'Leaving channel {channel}')
                self.send_command(f'PART #{channel}')
            self.irc.close()

    def print_message(self, message: Message) -> None:
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        channel = f':{message.channel}' if message.channel else ''
        user = f'@{message.user}' if message.user else message.prefix
        print(f'> [{time}] {channel} {user} {message.irc_command}: {message.text or ""}')

    def handle_message(self, received_message: str) -> None:
        if len(received_message) == 0:
            return
        message = self.parse_message(received_message)
        # self.print_message(message)
        print(received_message)
        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.chat.twitch.tv')

        if message.irc_command == 'PRIVMSG':
            if self.custom_commands.get(message.text_command):
                self.custom_commands[message.text_command](message)  # type: ignore
            elif message.text_command in self.state['template_commands']:
                self.handle_template_command(
                    message,
                    message.text_command,
                    self.state['template_commands'][message.text_command]
                )

    def handle_template_command(self, message: Message, command: str, template: str) -> None:
        try:
            text = template.format(**{'message': message})
        except IndexError:
            text = f'@{message.user} your command is missing an argument'
        except Exception as e:
            print('Error while handling template command', message, template)
            print(e)
            return
        self.send_privmsg(message.channel, text)

    def get_user_from_prefix(self, prefix: str) -> Optional[str]:
        domain = prefix.split('!')[0]
        if domain.endswith('.tmi.twitch.tv'):
            return domain[:-len('.tmi.twitch.tv')]
        if 'tmi.twitch.tv' not in domain:
            return domain
        return None

    def parse_message(self, received_message: str) -> Message:
        parts = received_message.split(' ')
        prefix = None
        user = None
        channel = None
        irc_command = None
        irc_args = None
        text = None
        text_command = None
        text_args = None
        if parts[0].startswith(':'):
            prefix = remove_prefix(parts[0], ':')
            user = self.get_user_from_prefix(prefix)
            parts = parts[1:]

        text_start = next(
            (i for i, part in enumerate(parts) if part.startswith(':')),
            None
        )
        if text_start is not None:
            text_parts = parts[text_start:]
            text_parts[0] = text_parts[0][1:]
            text = ' '.join(text_parts)
            if text_parts[0].startswith(self.command_prefix):
                text_command = remove_prefix(text_parts[0], self.command_prefix)
                text_args = text_parts[1:]
            parts = parts[:text_start]
        irc_command = parts[0]
        irc_args = parts[1:]

        hash_start = next(
            (i for i, part in enumerate(irc_args) if part.startswith('#')),
            None
        )
        if hash_start is not None:
            channel = irc_args[hash_start][1:]

        return Message(
            prefix=prefix,
            user=user,
            channel=channel,
            irc_command=irc_command,
            irc_args=irc_args,
            text=text,
            text_command=text_command,
            text_args=text_args
        )

    # CUSTOM COMMANDS BEGIN
    def list_commands(self, message: Message) -> None:
        template_command_names = list(self.state['template_commands'].keys())
        custom_command_names = list(self.custom_commands.keys())
        all_command_names = [
            self.command_prefix + command
            for command in (template_command_names + custom_command_names)
        ]
        text = f'@{message.user} ' + ' '.join(all_command_names)
        self.send_privmsg(message.channel, text)

    def add_template_command(self, message: Message, force: bool = False) -> None:
        if len(message.text_args) < 2:
            command = 'editcmd' if force else 'addcmd'
            text = f'@{message.user} Usage: !{command} <name> <template>'
            self.send_privmsg(message.channel, text)
            return

        command_name = remove_prefix(message.text_args[0], self.command_prefix)
        template = ' '.join(message.text_args[1:])
        if command_name in self.state['template_commands'] and not force:
            text = f'@{message.user} Command {command_name} already exists, use {self.command_prefix}editcmd if you want to update it.'
            self.send_privmsg(message.channel, text)
            return

        self.state['template_commands'][command_name] = template
        self.write_state()
        text = f'@{message.user} Command {command_name} has been {"added" if not force else "updated"}!'
        self.send_privmsg(message.channel, text)

    def edit_template_command(self, message: Message) -> None:
        return self.add_template_command(message, force=True)

    def delete_template_command(self, message: Message) -> None:
        if len(message.text_args) < 1:
            text = f'@{message.user} Usage: !delcmd <name>'
            self.send_privmsg(message.channel, text)
            return
        command_names = [
            remove_prefix(command, self.command_prefix)
            for command in message.text_args
        ]
        for command_name in command_names:
            if command_name not in self.state['template_commands']:
                text = f'@{message.user} Command {command_name} does not exist.'
                self.send_privmsg(message.channel, text)
                return
        for command_name in command_names:
            del self.state['template_commands'][command_name]
        self.write_state()
        text = f'@{message.user} Command {command_names} has been deleted!'
        self.send_privmsg(message.channel, text)


def main() -> None:
    bot = Bot()
    bot.init()


if __name__ == '__main__':
    main()
