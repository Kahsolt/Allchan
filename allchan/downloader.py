#!/usr/bin/env python3

import time
import queue
import random
import requests
import requests.exceptions
import threading

from .setting import *
from .util import logger
from .model import Session, Image

__all__ = ['Downloader', 'DownloadTask']


class DownloadTask(object):

    def __init__(self, id, priority=0, **kwargs):
        self.id = id
        self.priority = priority
        self.retry = kwargs.get('retry', DOWNLOAD_RETRY)
        self.timestamp = int(time.time())

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self.priority > other.priority or \
                self.priority == other.priority and self.timestamp > other.timestamp:
                return False
        return True

class DownloadWorker(threading.Thread):

    def __init__(self, downloader, evt_stop):
        super(self.__class__, self).__init__()
        self.db = Session()
        self.downloader = downloader
        self.queue = downloader.queue
        self.evt_stop = evt_stop

    def run(self):
        def _do_download():
            headers = { 'User-Agent': random.choice(DOWNLOAD_USER_AGENTS) }
            proxies = DOWNLOAD_PROXY_LOCAL or random.choice(DOWNLOAD_PROXIES) \
                if DOWNLOAD_PROXY_ENABLE else None
            try:
                res = requests.get(img.url, headers=headers, proxies=proxies, timeout=DOWNLOAD_TIMEOUT)
                if res.status_code == 200:
                    fdir = os.path.join(IMAGE_DIR, img.site, img.board)
                    os.makedirs(fdir, exist_ok=True)
                    fpath = os.path.join(fdir, img.filename)
                    if os.path.exists(fpath):
                        logger.warn('[Downloader] overwrite %r' % img.filename)

                    try:
                        with open(fpath, 'wb+') as fp:
                            fp.write(res.content)
                            fp.flush()
                        img.status = True
                        self.db.add(img)
                        self.db.commit()
                    except IOError:
                        logger.error("[Downloader] cannot write file %r" % img.filename)
                elif res.status_code == 404:
                    logger.info("[Downloader] image %r got 404'd" % img.url)
                    img.status = True
                    self.db.add(img)
                    self.db.commit()
                    return
                else:
                    logger.debug('[Downloader] network error: (%d, %s) for %s'
                                 % (res.status_code, res.reason, img.url))
            except (TimeoutError, requests.ConnectionError):
                logger.debug('[Downloader] timeout for %r' % img.url)
            except requests.exceptions.ProxyError:
                logger.debug('[Downloader] bad proxy %r' % proxies)
                DOWNLOAD_PROXIES.remove(proxies)
            except Exception as e:
                logger.error("[Downloader] %r" % e)

            task.retry -= 1
            if img.status == False and task.retry > 0:  # retry
                task.timestamp = int(time.time())
                task.priority += 1
                self.queue.put(task)
                img.priority = task.priority
            else:
                img.revive -= 1
            self.db.add(img)
            self.db.commit()

        while not self.evt_stop.is_set():
            task = self.queue.get()
            img = self.db.query(Image).get(task.id)
            if img is None:
                logger.error("[Downloader] bad task %r" % task)
                continue

            t = time.time()     # time started
            _do_download()
            if img.status:
                self.downloader.dltimes.append(time.time() - t)  # time finished

            self.evt_stop.wait(min(self.downloader.dltime_avg, DOWNLOAD_DELAY))


class Downloader(object):

    def __init__(self, workers=2):
        self.db = Session()
        self.queue = queue.PriorityQueue(DOWNLOAD_QUEUE_SIZE)
        self.dltimes = [ ]
        self.dltime_avg = DOWNLOAD_DELAY

        self.evt_stop = threading.Event()
        self.worker_threads = [ DownloadWorker(self, self.evt_stop) for _ in range(workers) ]
        self.report_thread = threading.Thread(target=self.report_task, args=(self.evt_stop,))
        self.statistics_thread = threading.Thread(target=self.statistics_task, args=(self.evt_stop,))

    def start(self):
        logger.debug('[Downloader] started with %d workers' % len(self.worker_threads))
        self.revive_task()
        self.report_thread.start()
        self.statistics_thread.start()
        for wt in self.worker_threads: wt.start()

    def stop(self):
        self.evt_stop.set()
        self.wait()
        logger.debug('[Downloader] stopped')

    def wait(self):
        self.report_thread.join()
        self.statistics_thread.join()
        for wt in self.worker_threads: wt.join()

    def revive_task(self):
        imgs_pending = self.db.query(Image).filter_by(status=False).all()
        cnt = len(imgs_pending)
        logger.info('[Queue] restoring %d pendings' % cnt)
        for img in imgs_pending:
            self.queue.put(DownloadTask(id=img.id, priority=img.priority))

    def report_task(self, evt_stop):
        while not evt_stop.is_set():
            cnt = self.queue.qsize()
            logger.info('[Queue] %d pendings, dltime_avg: %d' % (cnt, self.dltime_avg))
            evt_stop.wait(50)

    def statistics_task(self, evt_stop):
        while not evt_stop.is_set():
            cnt_dltimes = len(self.dltimes)
            if cnt_dltimes != 0:
                self.dltime_avg = int(sum(self.dltimes) / cnt_dltimes)
                self.dltimes = self.dltimes[len(self.dltimes) - 100:]
            evt_stop.wait(self.dltime_avg * 4)