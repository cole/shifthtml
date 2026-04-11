from shifthtml.client_runtime import (
    _APPLY_JS,
    _CUSTOM_ELEMENT_JS,
    _SSE_JS,
    _WS_JS,
    runtime,
)


def test_runtime_renders_core_js():
    result = str(runtime())
    assert result == f"<script>(function(){{{_APPLY_JS}{_CUSTOM_ELEMENT_JS}}})()</script>"


def test_runtime_with_stream_includes_sse():
    result = str(runtime(stream="/events"))
    assert _SSE_JS in result
    assert 'connectSSE("/events");' in result


def test_runtime_with_socket_includes_ws():
    result = str(runtime(socket="/ws"))
    assert _WS_JS in result
    assert 'connectWS("/ws");' in result


def test_runtime_with_stream_and_socket():
    result = str(runtime(stream="/events", socket="/ws"))
    assert _SSE_JS in result
    assert _WS_JS in result
    assert 'connectSSE("/events");' in result
    assert 'connectWS("/ws");' in result
