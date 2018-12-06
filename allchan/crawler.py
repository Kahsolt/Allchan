#!/usr/bin/env python3

import basc_py4chan
import py8chan

from .setting import *
from .model import Image
from .downloader import  DownloadTask

__all__ = ['Chan4Crawler', 'Chan8Crawler']


class AbstractCrawler(object):

    __sitename__ = None

    def __init__(self, db, download_queue):
        self.db = db
        self.download_queue = download_queue

    def crawl_thread(self, board, thread):
        pass


class Chan4Crawler(AbstractCrawler):

    __sitename__ = '4chan'

    def __init__(self, db, download_queue):
        super(self.__class__, self).__init__(db, download_queue)

    def crawl_thread(self, board, thread):
        b = basc_py4chan.Board(board)
        t = b.get_thread(thread_id=thread, raise_404=True)

        cnt_new = 0
        for f in t.file_objects():
            if f.file_deleted: continue
            if f.file_width < IMAGE_MIN_WIDTH or \
                  f.file_height < IMAGE_MIN_HEIGHT or \
                  f.file_size < IMAGE_MIN_SIZE or \
                  f.file_width / f.file_height > IMAGE_MAX_HW_RATIO or \
                  f.file_height / f.file_width > IMAGE_MAX_HW_RATIO:
                continue
            cnt = self.db.query(Image).filter_by(filename=f.filename).count()    # should it be unique
            if cnt != 0: continue

            path = '%s/%s/%s' % (self.__sitename__, board, f.filename)
            img = Image(site=self.__sitename__, board=board, thread=thread,
                        filename_original=f.filename_original, filename=f.filename,
                        width=f.file_width, height=f.file_height, size=f.file_size,
                        hash=f.file_md5_hex, path=path, url=f.file_url,
                        priority=0, status=False)
            self.db.add(img)
            cnt_new += 1
            self.download_queue.put(DownloadTask(id=img.id, priority=img.priority))

        self.db.commit()
        return cnt_new


class Chan8Crawler(AbstractCrawler):

    __sitename__ = '8chan'

    def __init__(self, db, download_queue):
        super(self.__class__, self).__init__(db, download_queue)

    def crawl_thread(self, board, thread):
        b = py8chan.Board(board)
        t = b.get_thread(thread_id=thread, raise_404=True)

        cnt_new = 0
        for f in t.file_objects():
            if f.file_width < IMAGE_MIN_WIDTH or \
                  f.file_height < IMAGE_MIN_HEIGHT or \
                  f.file_size < IMAGE_MIN_SIZE or \
                  f.file_width / f.file_height > IMAGE_MAX_HW_RATIO or \
                  f.file_height / f.file_width > IMAGE_MAX_HW_RATIO:
                continue
            cnt = self.db.query(Image).filter_by(filename=f.filename).count()    # should it be unique
            if cnt != 0: continue

            try:
                md5 = f.file_md5_hex    # might missing
            except KeyError:
                md5 = None
            path = '%s/%s/%s' % (self.__sitename__, board, f.filename)
            img = Image(site=self.__sitename__, board=board, thread=thread,
                        filename_original=f.filename_original, filename=f.filename,
                        width=f.file_width, height=f.file_height, size=f.file_size,
                        hash=md5, path=path, url=f.file_url,
                        priority=0, status=False)
            self.db.add(img)
            cnt_new += 1
            self.download_queue.put(DownloadTask(id=img.id, priority=img.priority))

        self.db.commit()
        return cnt_new