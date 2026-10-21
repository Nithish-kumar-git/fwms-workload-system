"""Redact credentials after formatting, including exception and JSON fields."""
import json
import logging
import re


class RedactingFormatter(logging.Formatter):
    def __init__(self, delegate, secrets=()):
        super().__init__()
        self.delegate = delegate
        self.secrets = tuple(value for value in secrets if value)

    def format(self, record):
        try:
            output = self.delegate.format(record)
            for secret in sorted(self.secrets, key=len, reverse=True):
                output = output.replace(secret, '[REDACTED]')
                output = output.replace(json.dumps(secret)[1:-1], '[REDACTED]')
            output = re.sub(r'postgres(?:ql)?(?:\+[\w]+)?://[^\s"\'<>]+',
                            '[REDACTED DATABASE URL]', output, flags=re.I)
            output = re.sub(r'Bearer\s+[^\s"\'<>]+', 'Bearer [REDACTED]', output, flags=re.I)
            return re.sub(r'eyJ[\w-]+\.[\w-]+\.[\w-]+', '[REDACTED TOKEN]', output)
        except Exception:
            return 'Log event suppressed (formatting error)'
