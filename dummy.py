from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import Connection, message
from time import sleep
import yaml

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


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


if __name__ == "__main__":
    port = cfg['IB_conn']['port']
    client_id = cfg['IB_conn']['client_id']
    conn = Connection.create(port=port, clientId=client_id)
    conn.connect()
    oid = 69
    cont = make_contract('AMZN', 'STK', 'SMART', 'SMART', 'USD')
    offer = make_order('BUY', 1)
    conn.placeOrder(oid, cont, offer)
    #sleep(1)
    conn.disconnect()