"""Explicit fictional login for feature tests predating the authentication gate."""
from victor.auth import AuthManager
from unittest.mock import patch


def authenticated_gui(config, **kwargs):
    from victor.gui.app import GUIManager
    if 'auth' not in kwargs:
        auth = AuthManager(config.data_dir)
        auth.setup('feature-test-only-password')
        kwargs['auth'] = auth
    # Feature fixtures must never contact the online voice service at startup.
    with patch('victor.voice.output.VoiceOutput.preload'):
        return GUIManager(config, **kwargs)
