from stackin import Invoice


def test_client_defaults_to_sdk_host():
    client = Invoice(api_key="test-key")
    assert client.base_url == "https://sdk.stackin.io"


def test_client_uses_explicit_base_url():
    client = Invoice(base_url="http://localhost:8000", api_key="test-key")
    assert client.base_url == "http://localhost:8000"


def test_headers_include_bearer_token_when_api_key_set():
    client = Invoice(api_key="test-key")
    assert client._headers() == {"Authorization": "Bearer test-key"}


def test_headers_empty_without_api_key():
    client = Invoice(api_key=None)
    assert client._headers() == {}
