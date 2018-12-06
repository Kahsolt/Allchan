#!/usr/bin/env python3

import logging

from .setting import LOG_FILE, LOG_LEVEL

__all__ = ['logger']


logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
fp = logging.FileHandler(LOG_FILE, mode='a+')
fp.setLevel(logging.DEBUG)
fp.setFormatter(logging.Formatter(
  "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
logger.addHandler(fp)
stderr = logging.StreamHandler()
stderr.setFormatter(logging.Formatter(
  "%(asctime)s - %(levelname)s: %(message)s"))
stderr.setLevel(logging.INFO)
logger.addHandler(stderr)