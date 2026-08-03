from __future__ import annotations

from typing import Callable

from loguru import logger

from app.infrastructure.websocket.command_handler import CommandHandler
from app.infrastructure.websocket.messages import (
    ProtocolEnvelope,
    ProtocolMessageError,
)


class MessageDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}
        self._default_handler: CommandHandler | None = None

    def register(self, message_type: str, handler: CommandHandler) -> None:
        self._handlers[message_type] = handler

    def set_default_handler(self, handler: CommandHandler) -> None:
        self._default_handler = handler

    def dispatch(self, envelope: ProtocolEnvelope) -> None:
        logger.debug(
            "Dispatching message | type={type} | id={id}",
            type=envelope.type,
            id=envelope.id,
        )
        handler = self._handlers.get(envelope.type)
        if handler is None:
            handler = self._default_handler
        if handler is None:
            logger.warning(
                "No handler registered for message type: {type}",
                type=envelope.type,
            )
            return
        try:
            handler(envelope)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Handler failed for message type={type} | id={id}",
                type=envelope.type,
                id=envelope.id,
            )
