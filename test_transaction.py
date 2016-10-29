import datetime
from time import sleep
import yaml

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

order_id = 1
port = cfg['IB_conn']['port']
client_id = cfg['IB_conn']['client_id']
con = ibConnection(port=port,clientId=client_id)
con.connect()




########################################################################################################################
def error_handler(msg):
    print "Server Error: %s" % msg

def reply_handler(msg):

    if msg.typeName == "openOrder" and msg.orderId == order_id and not fill_dict.has_key(msg.orderId):
        create_fill_dict_entry(msg)

    if msg.typeName == "orderStatus" and msg.status == "Filled" and fill_dict[msg.orderId]["filled"] == False:
        create_fill(msg)

    print "Server Response: %s, %s\n" % (msg.typeName, msg)


con.register(error_handler, 'Error')

con.registerAll(reply_handler)

def create_fill_dict_entry(msg):

    fill_dict[msg.orderId] = {
        "symbol": msg.contract.m_symbol,
        "exchange": msg.contract.m_exchange,
        "direction": msg.order.m_action,
        "filled": False
    }

    print fill_dict


def create_fill(msg):

    fd = fill_dict[msg.orderId]

    symbol = fd["symbol"]
    exchange = fd["exchange"]
    filled = msg.filled
    direction = fd["direction"]
    fill_cost = msg.avgFillPrice

    fill = FillEvent(
        datetime.datetime.utcnow(), symbol,
        exchange, filled, direction, fill_cost
    )

    fill_dict[msg.orderId]["filled"] = True

    print fill_dict

    #events.put(fill_event)

con.reqAccountUpdates(1, '')

# Stop client request for AccountUpdates
con.reqAccountUpdates(0, '')


sleep(5)