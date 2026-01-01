"""Event ingestion layer."""

from .connector import SourceConnector
from .adapters import GmailConnector

__all__ = [
    "SourceConnector",
    "GmailConnector",
]

