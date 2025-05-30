"""
Axiom Text Editor Package
"""

from .core import AxiomEditor
from .buffer import TextBuffer
from .commands import CommandParser
from .syntax import SyntaxHighlighter
from .error_handler import ErrorHandler, AxiomError
from .config import Config

__version__ = "1.0.0"
__author__ = "Axiom Development Team"

__all__ = [
    'AxiomEditor',
    'TextBuffer',
    'CommandParser',
    'SyntaxHighlighter',
    'ErrorHandler',
    'AxiomError',
    'Config'
]
