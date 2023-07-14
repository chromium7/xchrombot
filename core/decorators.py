from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional

from core.objects import Message, UserInfo

if TYPE_CHECKING:
    from main import Bot


def require_mod(func: Callable) -> Callable:
    @wraps(func)
    def inner(self: 'Bot', message: Message, *args: Any, **kwargs: Any) -> None:
        user: Optional[UserInfo] = getattr(message, 'user', None)
        if type(user) != UserInfo or not user.is_mod:
            return None
        return func(self, message, *args, **kwargs)
    return inner

