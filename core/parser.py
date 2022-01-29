from typing import Any, Dict, Union

from .objects import Message, UserInfo


def parse(received_message: str, command_prefix: str = '!') -> Message:
    # If tags are included, message starts with @
    if received_message.startswith('@'):
        user_data, message_data = received_message.split(' ', 1)
        user = parse_user_data(user_data)
        message = parse_message_data(message_data, user=user, command_prefix=command_prefix)
    else:
        message = parse_message_data(received_message, command_prefix=command_prefix)
    return message


def parse_user_data(message: str) -> UserInfo:
    """
    Returns a UserInfo object
    Parse the user data received when 
    """
    parts = message.strip('@').split(';')
    user_keys = UserInfo.__annotations__
    parts_dict: Dict[str, Any] = {}
    for part in parts:
        key, value = part.split('=', 1)
        key = key.replace('-', '_')
        if key not in user_keys:
            continue
        # Normalize boolean values
        if user_keys[key] == bool:
            parts_dict[key] = True if value == '1' else False
        else:
            parts_dict[key] = value

    return UserInfo(**parts_dict)  # type: ignore


def parse_message_data(message: str, user: Union[UserInfo, str] = '', command_prefix: str = '!') -> Message:
    """
    Returns a Message object
    Parse the standard message data received from twitch IRC
    """
    parts = message.split(' ')
    prefix = None
    channel = ''
    irc_command = None
    irc_args = None
    text = None
    text_command = ''
    text_args = []
    if parts[0].startswith(':'):
        prefix = parts[0].lstrip(':')
        if not user:
            user = get_user_from_prefix(prefix)
        parts = parts[1:]

    text_start = next(
        (i for i, part in enumerate(parts) if part.startswith(':')),
        None
    )
    if text_start is not None:
        text_parts = parts[text_start:]
        text_parts[0] = text_parts[0][1:]
        text = ' '.join(text_parts)
        if text_parts[0].startswith(command_prefix):
            text_command = text_parts[0].lstrip(command_prefix)
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


def get_user_from_prefix(prefix: str) -> str:
    domain = prefix.split('!')[0]
    if domain.endswith('.tmi.twitch.tv'):
        return domain[:-len('.tmi.twitch.tv')]
    if 'tmi.twitch.tv' not in domain:
        return domain
    return ''
