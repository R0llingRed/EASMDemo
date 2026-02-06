"""TLS helpers for scanner tasks."""

import ssl


def create_ssl_context(verify_tls: bool = True) -> ssl.SSLContext:
    """Create SSL context based on TLS verification policy."""
    context = ssl.create_default_context()
    if not verify_tls:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context
