#!/usr/bin/env python3

import sqlalchemy as sql
import sqlalchemy.orm
import sqlalchemy.ext.declarative

from .setting import DB_URI, DOWNLOAD_REVIVE

__all__ = ['Session', 'Image', 'Thread']


Model = sql.ext.declarative.declarative_base()

class Image(Model):

    __tablename__ = 'Image'

    id = sql.Column(sql.INT, primary_key=True, autoincrement=True)

    site = sql.Column(sql.VARCHAR(32), nullable=False)
    board = sql.Column(sql.VARCHAR(32), nullable=False)
    thread = sql.Column(sql.VARCHAR(32), nullable=False)

    filename_original = sql.Column(sql.VARCHAR(128))
    filename = sql.Column(sql.VARCHAR(128), nullable=False)
    width = sql.Column(sql.INT)
    height = sql.Column(sql.INT)
    size = sql.Column(sql.INT)
    hash = sql.Column(sql.VARCHAR(64))
    path = sql.Column(sql.VARCHAR(512), nullable=False)

    url = sql.Column(sql.VARCHAR(512), nullable=False)
    priority = sql.Column(sql.INT, default=0)
    revive = sql.Column(sql.INT, default=DOWNLOAD_REVIVE)
    status = sql.Column(sql.BOOLEAN, default=0)   # True: ok, False: pending

    time = sql.Column(sql.TIMESTAMP, server_default=sql.text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return '<Image [%s] %s/%s:%r>' % (self.status, self.site, self.board, self.filename)


class Thread(Model):

    __tablename__ = 'Thread'

    id = sql.Column(sql.INT, primary_key=True, autoincrement=True)

    site = sql.Column(sql.VARCHAR(32), nullable=False)
    board = sql.Column(sql.VARCHAR(32), nullable=False)
    thread = sql.Column(sql.VARCHAR(32), nullable=False)
    alive = sql.Column(sql.BOOLEAN, default=True)   # False: deleted
    updates = sql.Column(sql.INT, default=0)

    time = sql.Column(sql.TIMESTAMP, server_default=sql.text('CURRENT_TIMESTAMP'),
                      server_onupdate=sql.text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return '<Thread [%s] %s:%s/%r>' % (self.alive, self.site, self.board, self.thread)

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self.updates > other.updates:
                return False
        return True


engine = sql.create_engine(DB_URI)
Model.metadata.create_all(engine)
Session = sql.orm.sessionmaker(bind=engine)     # NO AUTOCOMMIT!!!