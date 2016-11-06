"""
This script executes trades and maintains a record of their statuses.
"""

from ib.ext.Order import Order
from time import sleep
from ib.ext.Contract import Contract
from ib.opt import Connection, message
import MySQLdb
import yaml
import datetime as dt
import pandas as pd

# Global variable for order id
global oid

# Read config file
with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Connect to MYSQL db
db, cur = ut.connect_to_db(cfg)

# Delete any previous positions we have
delete_positions = "DELETE from positions"
cur.execute(delete_positions)

# Get today's date. This will be used to query our tables
today = dt.datetime.now().strftime('%Y-%m-%d')

# Table for getting latest orders that have not been submitted yet
query = "SELECT * from {db}.{table} where date > '{date}' AND status='NULL' or status='cannot sell';".format(table=cfg['mysql']['table'],
                                                                                      date=today,
                                                                                      db=cfg['mysql']['db'])
# Read data from mysql and put into a dataframe
order_data = pd.read_sql(query, con=db)


def make_contract(symbol, sec_type, exch, prim_exch, curr):

    """
    This functions makes a contract to trade via interactive brokers

    :param symbol:
    :param sec_type:
    :param exch:
    :param prim_exch:
    :param curr:
    :return:
    """

    Contract.m_symbol = symbol
    Contract.m_secType = sec_type
    Contract.m_exchange = exch
    Contract.m_primaryExch = prim_exch
    Contract.m_currency = curr
    return Contract


def make_order(action, quantity, limit_price=None):

    """
    THis functions makes an order to be executed via interactive brokers.
    :param action:
    :param quantity:
    :param limit_price:
    :return:
    """

    # If the price is specified then execute the order as a limit order.
    if limit_price is not None:

        order = Order()
        order.m_orderType = 'LMT'
        order.m_totalQuantity = quantity
        order.m_action = action
        order.m_lmtPrice = limit_price

    # If the price is not specified then execute the order as a market order.
    else:
        order = Order()
        order.m_orderType = 'MKT'
        order.m_totalQuantity = quantity
        order.m_action = action

    return order


def error_handler(msg):

    """
    This function is for parsing error messages from interactive brokers

    :param msg:
    :return:
    """
    print "Server Error: type:%s and msg is %s" % (msg.typeName, msg)

    # If the order is cancelled then update status as 'cancelled'
    if msg.errorCode == 202:
        query = "UPDATE {table} set status='{status}' where order_id='{oid}';".format(table=cfg['mysql']['table'],
                                                                                        status='cancelled',
                                                                                        oid=msg.id)
        cur.execute(query)

    # If the order id is duplicate then update status as 'duplicate_id'
    if msg.errorCode == 103:
        query = "UPDATE {table} set status='{status}' where order_id='{oid}';".format(table=cfg['mysql']['table'],
                                                                                        status='duplicate_id',
                                                                                        oid=msg.id)
        cur.execute(query)


# Total cash available
cash = None


def reply_handler(msg):

    """
    This function is for parsing all regular messages from interactive brokers.
    As we get new messages, they will be properly parsed based on their type and values will be inserted
    into mysql tables.

    :param msg:
    :return:
    """

    # Handler for getting positions
    if msg.typeName == 'updatePortfolio':
        # print "Position:", msg.contract.m_symbol, msg.position, msg.marketPrice, msg.contract.m_currency, msg.contract.m_secType
        query = "INSERT INTO {table} (security, avg_cost, total_value, quantity) values ('{security}', " \
                "'{avg_cost}', '{total_value}', '{quantity}');".format(table='positions',
                                      security=msg.contract.m_symbol,
                                      avg_cost=msg.averageCost,
                                      total_value=msg.marketValue,
                                      quantity=msg.position)
        cur.execute(query)

    # Handler for getting available cash
    if msg.typeName == 'updateAccountValue':

        if msg.key == 'FullAvailableFunds':

            global cash
            cash = msg.value

    # Handler for getting order status (opened, filled or cancelled)
    for index, row in order_data.iterrows():

        if row.exec_price == 'NULL':

            oid = row.order_id

            if msg.typeName == "openOrder" and msg.orderId == oid:
                print "A new %s order (%s) has been opened for symbol %s" % (msg.order.m_action, msg.orderId, msg.contract.m_symbol)
                query_1 = "UPDATE {table} set status='{status}' where order_id='{oid}';".format(table=cfg['mysql']['table'],
                                                                                                status='opened',
                                                                                                oid=msg.orderId)
                cur.execute(query_1)

            if msg.typeName == "orderStatus" and msg.status != "Filled":
                print "This order (%s) has not been filled" % (msg.orderId)
                query_1 = "UPDATE {table} set status='{status}' where " \
                          "order_id = '{oid}';".format(table=cfg['mysql']['table'],
                                                       status='not filled',
                                                       oid=msg.orderId)
                cur.execute(query_1)

            if msg.typeName == "orderStatus" and msg.status == "Filled":
                print "This order (%s) has been filled at $%s" % (msg.orderId, msg.avgFillPrice)
                query_1 = "UPDATE {table} set exec_price='{exec_price}', status='{status}' where " \
                          "order_id = '{oid}';".format(table=cfg['mysql']['table'],
                                                       exec_price=float(msg.avgFillPrice),
                                                       status='filled',
                                                       oid=msg.orderId)
                cur.execute(query_1)


if __name__ == '__main__':

    # Open connection to interactive brokers
    port = cfg['IB_conn']['port']
    client_id = cfg['IB_conn']['client_id']
    con = Connection.create(port=port, clientId=client_id)

    # Register to messages
    con.register(error_handler, 'Error')
    con.registerAll(reply_handler)
    con.register(reply_handler, 'UpdatePortfolio')

    con.connect()

    con.reqAccountUpdates(1, '')
    con.reqAccountUpdates(0, '')
    con.reqPositions()

    sleep(4)

    query = "INSERT INTO {table} (security, avg_cost, total_value, quantity) values ('{security}', " \
            "'{avg_cost}', '{total_value}', '{quantity}');".format(table='positions',
                                                                   security='cash',
                                                                   avg_cost=cash,
                                                                   total_value=cash,
                                                                   quantity=1)
    cur.execute(query)

    # Query for getting positions
    query_positions = "SELECT * from dummy.positions"

    # Read positions data from mysql and put into a dataframe

    positions = pd.read_sql(query_positions, con=db)


    # Execute orders
    for index, row in order_data.iterrows():

        if row.status == 'NULL' or row.status == 'cannot sell':

            oid = row.order_id
            security = row.security
            action = row.action
            size = row.size
            price = float(row.ask_price)

            contract = make_contract(security, 'STK', 'SMART', 'SMART', 'USD')
            offer = make_order(action, size)

            if action == 'buy':
                # Check to make sure total amount of cash is greater than transaction cost and an additional 15%
                if cash > ((price*size) + 0.15*price*size):
                    print 'this is affordable - '+ str(price*size)
                    print ('Buying {size} of {security} at {price}'.format(size=size,
                                                                           security=security,
                                                                           price=price))
                    con.placeOrder(oid, contract, offer)

            if action == 'sell':
                # check to see if we own the security first
                if row.security in list(positions.security):
                    print 'we have the position'
                    #positions[positions['security'] == row.security].quantity
                    if (positions[positions['security'] == row.security].quantity > 0).bool():
                        print "we can sell"
                        print ('Selling {size} of {security} at {price}'.format(size=size,
                                                                                security=security,
                                                                                price=price))
                        con.placeOrder(oid, contract, offer)
                else:
                    print "we don't have this position and cannot sell"
                    query_1 = "UPDATE {table} set status='{status}' where order_id='{oid}';".format(
                        table=cfg['mysql']['table'],
                        status='cannot sell',
                        oid=oid)

                    cur.execute(query_1)

            sleep(5)

    print('disconnected', con.disconnect())

    cur.close()
    db.close()