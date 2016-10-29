#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# This script is an example of using the ib.opt.messagetools module.
##

from ib.ext.Order import Order

from time import sleep
from ib.ext.Contract import Contract
from ib.opt import Connection, message
import MySQLdb
import yaml
import datetime as dt
import pandas as pd

global oid

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


db = MySQLdb.connect(host=cfg['mysql']['host'],    # your host, usually localhost
                     user=cfg['mysql']['user'],         # your username
                     passwd=cfg['mysql']['pwd'],  # your password
                     db=cfg['mysql']['db'])        # name of the data base

cur = db.cursor()
db.autocommit(on=1)

today = dt.datetime.now().strftime('%Y-%m-%d')+ ' 00:00:00'

query = "SELECT * from {db}.{table} where date > '{date}' AND exec_price is NULL;".format(table=cfg['mysql']['table'],
                                                          date=today,
                                                            db = cfg['mysql']['db'])

df_mysql = pd.read_sql(query, con=db)

df_mysql = df_mysql.tail(3)

print df_mysql

def make_contract(symbol, sec_type, exch, prim_exch, curr):
    Contract.m_symbol = symbol
    Contract.m_secType = sec_type
    Contract.m_exchange = exch
    Contract.m_primaryExch = prim_exch
    Contract.m_currency = curr
    return Contract


def make_order(action, quantity, price=None):
    if price is not None:
        order = Order()
        order.m_orderType = 'LMT'
        order.m_totalQuantity = quantity
        order.m_action = action
        order.m_lmtPrice = price

    else:
        order = Order()
        order.m_orderType = 'MKT'
        order.m_totalQuantity = quantity
        order.m_action = action

    return order


def error_handler(msg):
    print "Server Error: %s" % msg


def reply_handler(msg):

    for index, row in df_mysql.iterrows():
        if row.exec_price == None:
            oid = row.order_id
            if msg.typeName == "openOrder" and msg.orderId == oid:
                print "A new %s order (%s) has been opened for symbol %s" % (msg.order.m_action, msg.orderId, msg.contract.m_symbol)

            if msg.typeName == "orderStatus" and msg.status == "Filled":
                print "This order (%s) has been filled at $%s" % (msg.orderId, msg.avgFillPrice)
                query_1 = "UPDATE {table} set exec_price='{exec_price}' where order_id = '{oid}';".format(table=cfg['mysql']['table'],
                                                                                                        exec_price=msg.avgFillPrice,
                                                                                                        oid=msg.orderId)
                cur.execute(query_1)


if __name__ == '__main__':

    port = cfg['IB_conn']['port']
    client_id = cfg['IB_conn']['client_id']
    con = Connection.create(port=port, clientId=client_id)

    #con.register(next_valid_order_id_handler, 'NextValidId')
    con.register(error_handler, 'Error')
    con.registerAll(reply_handler)

    con.connect()

    for index, row in df_mysql.iterrows():
        if row.exec_price == None:
            oid = row.order_id
            security = row.security
            action = row.action
            size = row.size
            price = row.ask_price
            contract = make_contract(security, 'STK', 'SMART', 'SMART', 'USD')
            offer = make_order(action, size, price)
            print ('Buying {size} of {security} at {price}'.format(size=size,
                                                                   security=security,
                                                                   price=price))
            con.placeOrder(oid, contract, offer)
            sleep(2)

    #con.connect()

#    oid = get_next_valid_order_id(con)

    #cont = make_contract('SBUX', 'STK', 'SMART', 'SMART', 'USD')
    #offer = make_order('SELL', 6, 52)
    #con.placeOrder(oid, cont, offer)
    #sleep(2)
    print('disconnected', con.disconnect())





cur.close()
db.close()