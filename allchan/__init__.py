#!/usr/bin/env python3

__version__ = '0.0.1'

from .config import autoconfigure
from .watcher import Watcher
from .downloader import Downloader

autoconfigure()