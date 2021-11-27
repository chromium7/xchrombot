from collections import namedtuple
import datetime
import socket
import os

import dotenv


dotenv.load_dotenv()


TEMPLATE_COMMANDS = {
    '!discord': 'Please join the {message.channel} Discord server, {message.user}',
    '!so': 'Check out {message.text_args[0]}, they are a nice streamer'
}


Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args'
)


class Bot:
    def __init__(self) -> None:
        self.irc_server = 'irc.twitch.tv'
        self.irc_port = 6667
        self.oauth_token = os.getenv('OAUTH_TOKEN')
        self.username = os.getenv('TWITCH_USERNAME')
        self.channels = ['xchrombot']
        # self.load_template_commands()
        self.custom_commands = {
            '!date': self.reply_with_date
        }

    def send_privmsg(self, channel: str, message: str) -> None:
        self.send_command(f'PRIVMSG #{channel} :{message}')

    def send_command(self, command: str) -> None:
        if 'PASS' not in command:
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode('utf-8'))

    def connect(self) -> None:
        self.irc = socket.socket()
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, 'Hello!')
        self.loop_for_messages()

    def loop_for_messages(self) -> None:
        while True:
            received_messages = self.irc.recv(2048).decode('utf-8')
            for message in received_messages.split('\r\n'):
                self.handle_message(message)

    def reply_with_date(self, message: Message) -> None:
        formatted_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = f'Here you go {message.user}, the date is {formatted_date}'
        self.send_privmsg(message.channel, text)

    def handle_message(self, received_message: str) -> None:
        if not received_message:
            return
        message = self.parse_message(received_message)
        print(f'> {message}')

        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        if message.irc_command == 'PRIVMSG':
            if TEMPLATE_COMMANDS.get(message.text_command):
                self.handle_template_command(
                    message,  # Message(...)
                    message.text_command,  # !discord
                    TEMPLATE_COMMANDS[message.text_command]  # Please join the discord server
                )
            if self.custom_commands.get(message.text_command):
                self.custom_commands[message.text_command](message)

    def handle_template_command(self, message: Message, command: str, template: str) -> None:
        text = template.format(**{'message': message})
        self.send_privmsg(message.channel, text)

    def get_user_from_prefix(self, prefix: str) -> str:
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
            prefix = parts[0][1:]
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
            text_command = text_parts[0]
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

        message = Message(
            prefix=prefix,
            user=user,
            channel=channel,
            irc_command=irc_command,
            irc_args=irc_args,
            text=text,
            text_command=text_command,
            text_args=text_args
        )
        return message


def main() -> None:
    bot = Bot()
    bot.connect()


if __name__ == '__main__':
    main()
