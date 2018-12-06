#!/usr/bin/env python3

import os
import shutil
import sqlite3

from allchan.setting import IMAGE_DIR, IMAGE_DELETED_DIR

broke_files = [ ]
    
db = sqlite3.connect('allchan.sqlite3')
RECYCLE_DIR = os.path.join(IMAGE_DIR, '_recycle')

dirs = [
    os.path.join(IMAGE_DIR, '4chan', 'b'),
    os.path.join(IMAGE_DIR, '4chan', 'c'),
    os.path.join(IMAGE_DIR, '4chan', 'cm'),
    os.path.join(IMAGE_DIR, '4chan', 'w'),
    os.path.join(IMAGE_DIR, '4chan', 'y'),
    os.path.join(IMAGE_DIR, '8chan', 'shota'),
    os.path.join(IMAGE_DIR, '8chan', 'ss'),
]


def relocate():
    cnt = 0
    os.chdir(IMAGE_DIR)
    sql = 'SELECT site, board, thread, path, filename, status FROM Image;'
    for r in db.execute(sql).fetchall():
        site, board, thread, path, filename, status = r
        path = path.replace('/', '\\')

        found = False
        if os.path.exists(path):
            found = True
            # print("[OK] %s:%s/%s/%s => %r" % (site, board, thread, filename, path))
            for dir in dirs:
                p = os.path.join(dir, filename)
                if os.path.join(IMAGE_DIR, path) != p and os.path.exists(p):
                    os.unlink(p)
                    cnt += 1
        else:
            for dir in dirs:
                p = os.path.join(dir, filename)
                if os.path.join(IMAGE_DIR, path) != p and os.path.exists(p):
                    found = True
                    # print("[Relocate] %s:%s/%s/%s =|=> %r" % (site, board, thread, filename, path))
                    if os.path.exists(path): os.unlink(path)
                    shutil.move(p, path)
                    cnt += 1
        if found and status == 0:
            sql = "UPDATE Image SET status = 1 WHERE filename = '%s';" % filename
            db.execute(sql).fetchall()

    db.commit()
    print(">> %d files relocated" % cnt)

def rename():
    cnt = 0
    db.execute('BEGIN;').fetchall()
    for dir in dirs:
        for fn in os.listdir(dir):
            sql = "SELECT filename FROM Image WHERE filename_original = '%s';" % fn
            r = db.execute(sql).fetchall()
            if r != []:
                filename = r[0][0]
                old_fn = os.path.join(dir, fn)
                new_fn = os.path.join(dir, filename)
                if os.path.exists(new_fn):
                    print('rename conflict %r => %r', old_fn, new_fn)
                    continue
                os.rename(old_fn, new_fn)
                cnt += 1
    db.execute('COMMIT;').fetchall()
    print(">> %d files renamed" % cnt)

def mark_orphan():
    cnt = 0
    db.execute('BEGIN;').fetchall()
    for dir in dirs:
        for fn in os.listdir(dir):
            if fn.startswith('ORPHAN_'): continue

            sql = "SELECT count(*) FROM Image WHERE filename = '%s';" % fn
            r = db.execute(sql).fetchall()
            if r[0][0] == 0:
                os.rename(os.path.join(dir, fn), os.path.join(dir, 'ORPHAN_' + fn))
                cnt += 1
    db.execute('COMMIT;').fetchall()
    print(">> %d orphans found" % cnt)

def demark_orphan():
    cnt = 0
    for dir in dirs:
        for fn in os.listdir(dir):
            if fn.startswith('ORPHAN_'):
                os.rename(os.path.join(dir, fn), os.path.join(dir, fn[7:]))
                cnt += 1
    print(">> %d orphans reorphanize" % cnt)

def redownload_broken():
    cnt = 0
    for dir in dirs:
        for fn in os.listdir(dir):
            fsize = os.path.getsize(os.path.join(dir, fn))
            if fsize < 16 * 1024:
                sql = "UPDATE Image SET status = 0 WHERE filename = '%s'" % fn
                db.execute(sql).fetchall()
                cnt += 1

    db.commit()
    print(">> %d files marked for redownload" % cnt)

def mark_downloaded():
    cnt = 0
    sql = 'SELECT path, filename, filename_original FROM Image WHERE status = 0;'
    for r in db.execute(sql).fetchall():
        path, filename, filename_original = r
        if os.path.exists(os.path.join(IMAGE_DIR, path.replace('/', '\\'))) or \
            os.path.exists(os.path.join(IMAGE_DELETED_DIR, filename)) or \
            os.path.exists(os.path.join(IMAGE_DELETED_DIR, filename_original)):
            # but already on disk (which is wierd)
            sql = "UPDATE Image SET status = 1 WHERE path = '%s';" % path
            db.execute(sql).fetchall()
            cnt += 1

    db.commit()
    print(">> %d files marked downloaded" % cnt)

def delete_ghost_records():
    cnt = 0
    os.chdir(IMAGE_DIR)
    # marked downloaded, but in non-watched or dead thread
    sql = 'SELECT path FROM Image ' \
          '  WHERE (status = 1) AND (' \
          '    (site, board, thread) NOT IN (SELECT site, board, thread FROM Thread) ' \
          '  OR ' \
          '    (site, board, thread) IN (SELECT site, board, thread FROM Thread WHERE alive = 0)' \
          '  );'
    for r in db.execute(sql).fetchall():
        path = r[0]
        if os.path.exists(path.replace('/', '\\')): continue
        # yet not on disk (means I've manually deleted)
        sql = "DELETE FROM Image WHERE path = '%s';" % path
        db.execute(sql).fetchall()
        cnt += 1

    db.commit()
    print(">> %d ghost records deleted" % cnt)


if __name__ == '__main__':
    # relocate()
    # rename()
    # mark_orphan()
    # demark_orphan()
    # redownload_broken()
    # mark_downloaded()
    # delete_ghost_records()
    pass