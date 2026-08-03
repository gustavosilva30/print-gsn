from __future__ import annotations

from app.infrastructure.websocket.dispatcher import MessageDispatcher
from app.infrastructure.websocket.messages import ProtocolEnvelope, build_envelope


class _RecordingHandler:
    def __init__(self) -> None:
        self.calls: list[ProtocolEnvelope] = []

    def __call__(self, envelope: ProtocolEnvelope) -> None:
        self.calls.append(envelope)


def test_dispatcher_routes_by_type() -> None:
    dispatcher = MessageDispatcher()
    handler = _RecordingHandler()
    dispatcher.register("print", handler)

    envelope = build_envelope(
        message_type="print",
        version="1.0",
        computer_id="c1",
        company_id="co1",
        token="t1",
        payload={"data": {"code": "A"}},
    )
    dispatcher.dispatch(envelope)
    assert len(handler.calls) == 1
    assert handler.calls[0].type == "print"


def test_dispatcher_ignores_unregistered_type() -> None:
    dispatcher = MessageDispatcher()

    envelope = build_envelope(
        message_type="unknown_type",
        version="1.0",
        computer_id="c1",
        company_id="co1",
        token="t1",
        payload={},
    )
    dispatcher.dispatch(envelope)


def test_dispatcher_uses_default_handler() -> None:
    dispatcher = MessageDispatcher()
    default_handler = _RecordingHandler()
    dispatcher.set_default_handler(default_handler)

    envelope = build_envelope(
        message_type="unknown_type",
        version="1.0",
        computer_id="c1",
        company_id="co1",
        token="t1",
        payload={},
    )
    dispatcher.dispatch(envelope)
    assert len(default_handler.calls) == 1
