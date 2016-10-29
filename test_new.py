#!/usr/bin/env python

from time import sleep
import yaml

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


# LOAD the ib.ext and ib.opt Libraries
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message

# DEFINE a basic function to capture error messages
def error_handler(msg):
    print "Error", msg

# DEFINE a basic function to print the "raw" server replies
def replies_handler(msg):
    print "Server Reply:", msg

# DEFINE a basic function to print the "parsed" server replies for an IB Request of "Portfolio Update" to list an IB portfolio position
def print_portfolio_position(msg):
    #print "Position:", msg.contract.m_symbol, msg.position, msg.marketPrice, msg.contract.m_currency, msg.contract.m_secType
    #print "Position:", msg
    if msg.typeName=='openOrderStatus':
        print msg.orderId

def message_handler(msg):
    print msg
    if msg.typeName == 'openOrder':
        #print msg.orderId
        #print msg.status
        #print msg.filled
        #print msg.avgFillPrice
        print msg
        #print msg.contract.m_symbol

# Main code - adding "if __name__ ==" is not necessary

# Create the connection to IBGW with client socket id=1234
port = cfg['IB_conn']['port']
client_id = cfg['IB_conn']['client_id']
ibgw_conChannel = ibConnection(port=port,clientId=client_id)
ibgw_conChannel.connect()

# Map server replies for "Error" messages to the "error_handler" function
#ibgw_conChannel.register(error_handler, 'Error')

# Map server replies to "print_portfolio_position" function for "UpdatePortfolio" client requests
ibgw_conChannel.register(print_portfolio_position, 'updatePortfolio')
ibgw_conChannel.registerAll(message_handler)

# Map server "raw" replies to "replies_handler" function for "UpdateAccount" client requests
#ibgw_conChannel.register(replies_handler, 'orderStatus')

# Make client request for AccountUpdates (includes request for Portfolio positions)
ibgw_conChannel.reqAccountUpdates(1, '')

# Stop client request for AccountUpdates
ibgw_conChannel.reqAccountUpdates(0, '')
#ibgw_conChannel.reqPositions()


sleep(5)

# Disconnect - optional
# print 'disconnected', ibgw_conChannel.disconnect()