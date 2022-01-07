import json
import logging
import os
import socket
import ssl
from typing import Any, Dict

import dotenv

from core.parser import parse
from core.objects import Message, UserInfo


dotenv.load_dotenv()


class Bot:
    def __init__(self) -> None:
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6697
        self.oauth_token = os.getenv('OAUTH_TOKEN')
        self.username = os.getenv('TWITCH_USERNAME')
        # self.channels = ['wazfu']
        self.channels = ['xchrombot']
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
            logging.info(f'< {command}')
        self.irc.send((command + '\r\n').encode('utf-8'))

    def send_credentials(self) -> None:
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        self.send_command('CAP REQ :twitch.tv/tags')

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
            logging.info('Terminating bot...')
            for channel in self.channels:
                logging.info(f'Leaving channel {channel}')
                self.send_command(f'PART #{channel}')
            self.irc.close()

    def log_message(self, message: Message) -> None:
        user = message.user
        if isinstance(user, UserInfo):
            user = user.display_name
        logging.info(f'> {user or "-"}@{message.channel}: {message.text}')

    def handle_message(self, received_message: str) -> None:
        if len(received_message) == 0:
            return
        message: Message = parse(received_message, command_prefix=self.command_prefix)
        self.log_message(message)

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
            logging.warning('Error while handling template command', message, template)
            logging.warning(e)
            return
        self.send_privmsg(message.channel, text)

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

        command_name = message.text_args[0].lstrip(self.command_prefix)
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
            command.lstrip(self.command_prefix)
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
    FORMAT = '[%(asctime)-15s] %(levelname)s %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )
    main()
