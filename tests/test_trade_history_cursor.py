from datetime import datetime, timezone

import pytest

from bybit_options.api.routes.trade_history import _decode_cursor, _encode_cursor, CursorValue


def test_cursor_roundtrip_with_iso_timestamp() -> None:
    cursor = CursorValue(time=datetime(2026, 1, 19, tzinfo=timezone.utc), id="123")
    encoded = _encode_cursor(cursor)
    decoded = _decode_cursor(encoded)

    assert decoded.id == "123"
    assert decoded.time.isoformat() == "2026-01-19T00:00:00+00:00"


def test_cursor_decode_invalid_payload() -> None:
    with pytest.raises(ValueError):
        _decode_cursor("not-a-valid-cursor")
