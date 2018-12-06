#!/usr/bin/env python3

import os
import json

from . import setting as st
from .util import logger

__all__ = ['autoconfigure']


def autoconfigure():
    if not os.path.exists(st.CONFIG_FILE): return

    with open(st.CONFIG_FILE) as fp:
        try:
            conf = json.load(fp, parse_int=int, parse_float=float)
            for module, confs in conf.items():
                for k, v in confs.items():
                    if (k.startswith('CRAWL_') or
                        k.startswith('IMAGE_') or
                        k.startswith('DOWNLOAD_')) \
                          and hasattr(st, k):
                        setattr(st, k, v)
            logger.debug('[Config] user config parsed ok')
        except json.JSONDecodeError as e:
            logger.error('[Config] config file error %r' % e)
            exit(-1)