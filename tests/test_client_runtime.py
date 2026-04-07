from shifthtml.client_runtime import (
    _APPLY_JS,
    _CUSTOM_ELEMENT_JS,
    _SSE_JS,
    _WS_JS,
    runtime,
)


def test_runtime_renders_core_js():
    result = runtime().render()
    assert result == f"<script>{_APPLY_JS}{_CUSTOM_ELEMENT_JS}</script>"


def test_runtime_with_stream_includes_sse():
    result = runtime(stream="/events").render()
    assert _SSE_JS in result
    assert 'connectSSE("/events");' in result


def test_runtime_with_socket_includes_ws():
    result = runtime(socket="/ws").render()
    assert _WS_JS in result
    assert 'connectWS("/ws");' in result


def test_runtime_with_stream_and_socket():
    result = runtime(stream="/events", socket="/ws").render()
    assert _SSE_JS in result
    assert _WS_JS in result
    assert 'connectSSE("/events");' in result
    assert 'connectWS("/ws");' in result
