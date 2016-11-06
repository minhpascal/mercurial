"""
This utils file is for storing useful utilities functions that can be used by main scripts.
"""

import MySQLdb


def connect_to_db(cfg):

    # Connect to mysql database
    db = MySQLdb.connect(host=cfg['mysql']['host'],  # your host, usually localhost
                         user=cfg['mysql']['user'],  # your username
                         passwd=cfg['mysql']['pwd'],  # your password
                         db=cfg['mysql']['db'])  # name of the data base

    cur = db.cursor()
    db.autocommit(on=1)

    return db, cur