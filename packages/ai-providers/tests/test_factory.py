import pytest

from ai_providers.factory import create_provider
from ai_providers.mock_provider import MockProvider


def test_default_provider_is_mock():
    provider = create_provider(env={})
    assert isinstance(provider, MockProvider)


def test_explicit_mock_provider():
    provider = create_provider("mock", env={"AI_PROVIDER": "anthropic"})
    assert isinstance(provider, MockProvider)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        create_provider("not-a-real-provider", env={})


def test_anthropic_requires_api_key():
    from ai_providers.anthropic_provider import AnthropicProvider

    with pytest.raises(ValueError):
        AnthropicProvider(api_key="")
