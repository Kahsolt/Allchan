#!/usr/bin/env python3

import re
import time
import queue
import requests
import threading

from .setting import *
from .util import logger
from .model import Session, Thread
from .crawler import Chan4Crawler, Chan8Crawler
from .downloader import Downloader

__all__ = ['Watcher']


class Watcher(object):

    def __init__(self):
        self.watchlist = queue.PriorityQueue()
        self.db = Session()
        self.downloader = Downloader(DOWNLOAD_WORKER)   # thread
        self.crawlers = {
            '4chan': Chan4Crawler(self.db, self.downloader.queue),
            '8chan': Chan8Crawler(self.db, self.downloader.queue),
        }

        self.evt_stop = threading.Event()
        self.watch_thread = threading.Thread(target=self.watch_task, args=(self.evt_stop,))

        self.load_watchlist_file()

    def add_watched_thread(self, url=None, site=None, board=None, thread=None):
        if '4chan' in url:
            site = '4chan'
            m = re.match('.*boards.4chann?e?l?.org/(\w*)/thread/(\d*).*', url)
            if m is not None:
                board, thread = m.groups()
        elif '8ch' in url:
            site = '8chan'
            m = re.match('.*8ch.net/(\w*)/res/(\d*).html.*', url)
            if m is not None:
                board, thread = m.groups()

        if not None in [site, board, thread]:
            thread = int(thread)
            cnt = self.db.query(Thread).filter(Thread.site==site,
                                               Thread.board==board,
                                               Thread.thread==thread).count()
            if cnt == 0:
                thr = Thread(site=site, board=board, thread=thread, alive=True, updates=0)
                self.db.add(thr)
                self.db.commit()
                self.watchlist.put(thr)
        else:
            raise ValueError('[Watcher] bad url %r', url)

    def instant_update(self):
        for thr in self.db.query(Thread).filter(Thread.alive==True).all():
            crawler = self.crawlers.get(thr.site)
            if crawler is not None:
                try:
                    cnt_new = crawler.crawl_thread(thr.board, thr.thread)
                    logger.info('[Watcher] %d new content in %s:%s/%s' % (cnt_new, thr.site, thr.board, thr.thread))
                    thr.updates += 1
                    time.sleep(0.5)
                except requests.HTTPError:
                    thr.alive = False
                    logger.error('[Watcher] R.I.P thread %s:%s/%s ' % (thr.site, thr.board, thr.thread))
            else:
                logger.error('[Watcher] no crawler for site %r' % thr.site)
        self.db.commit()

    def load_watchlist_file(self):
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE) as fp:
                for url in fp.read().split('\n'):
                    try:
                        self.add_watched_thread(url)
                    except:
                        pass

    def start(self):
        self.downloader.start()
        self.watch_thread.start()
        logger.debug('[Watcher] started with %d crawlers' % len(self.crawlers))

    def stop(self):
        self.evt_stop.set()
        self.watch_thread.join()
        self.downloader.stop()
        logger.debug('[Watcher] stopped')

    def watch_task(self, evt_stop):
        for thr in self.db.query(Thread).filter(Thread.alive==True).all():
            self.watchlist.put(thr)

        while not evt_stop.is_set():
            thr = self.watchlist.get()

            crawler = self.crawlers.get(thr.site)
            cnt_new = 0
            if crawler is not None:
                try:
                    cnt_new = crawler.crawl_thread(thr.board, thr.thread)
                    logger.info('[Watcher] %d new content in %s:%s/%s' % (cnt_new, thr.site, thr.board, thr.thread))
                    thr.updates += 1
                except requests.HTTPError:
                    thr.alive = False
                    logger.error('[Watcher] R.I.P thread %s:%s/%s ' % (thr.site, thr.board, thr.thread))
            else:
                logger.error('[Watcher] no crawler for site %r' % thr.site)

            if thr.alive:
                self.watchlist.put(thr)
            evt_stop.wait(max(cnt_new * self.downloader.dltime_avg, CRAWL_DELAY))