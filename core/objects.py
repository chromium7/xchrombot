from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UserInfo:
    badge_info: str
    badges: str
    client_nonce: str
    color: str
    display_name: str
    emotes: str
    first_msg: bool
    flags: str
    id: str
    mod: bool
    room_id: str
    subscriber: bool
    tmi_sent_ts: str
    turbo: bool
    user_id: str
    user_type: str


@dataclass
class Message:
    prefix: Optional[str]
    user: Optional[UserInfo]
    channel: Optional[str]
    irc_command: Optional[str]
    irc_args: List[str]
    text: Optional[str]
    text_command: Optional[str]
    text_args: List[str]