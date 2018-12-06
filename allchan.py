#!/usr/bin/env python3
#
# Author: Kahsolt
# Description: Image crawler for xChan.
# Create Date: 2018/11/24
# Update Date: 2018/11/30
#

import sys

from allchan import Watcher
from allchan import Downloader
from allchan.setting import DOWNLOAD_WORKER


if __name__ == '__main__':

    if len(sys.argv) == 1:
        print('[Allchan] started in watch mode')

        watcher = Watcher()
        try:
            watcher.start()
            while True:
                url = input('>> Add watch thread url:\n').strip(' \t\n\r')
                if len(url) > 0:
                    try:
                        watcher.add_watched_thread(url)
                        print('<< [OK] thread %r added to watchlist' % url)
                    except:
                        print('<< [ERROR] bad url!!')
        except KeyboardInterrupt:
            watcher.stop()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg == '-sync':
            print('[Allchan] started in sync mode')

            downloader = Downloader(DOWNLOAD_WORKER)
            try:
                downloader.start()
                downloader.wait()
            except KeyboardInterrupt:
                downloader.stop()
        elif arg == '-update':
            print('[Allchan] started in instant update mode')

            watcher = Watcher()
            try:
                watcher.instant_update()
            except KeyboardInterrupt:
                watcher.db.flush()
    else:
        print('Usage: allchan [-sync|-update]')