"""
This script executes individual strategies and groups the result together based on weights.

"""

import MySQLdb
import market_data as md
import yaml
import pandas as pd
import numpy as np
import argparse
import utils as ut
import datetime as dt

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-date', '--date', help='Date you want ro run the strategy for', required=False)
arg_parser.add_argument('-sim_id', '--sim_id', help='id to keep track of the simulation', required=False)
args = vars(arg_parser.parse_args())

# Check to see if date argument was passed
# If it was then use that else use today's date
if args['date']:
    date = args['date']
else:
    date = dt.datetime.now().strftime('%Y%m%d')

sim_id = args['sim_id']

if not sim_id:
    sim_id = 'NULL'

# Load config
with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Import all strategies
for strategy in cfg['strategies_to_run']:
    exec("""from strategy_{strategy} import *""".format(strategy=strategy))


# Loop through all the strategies and get their output
# put them in a dictionary
def get_strategy_output(strategies, date):

    strategy_output = {}

    for strategy in strategies:

        strategy_output[strategy] = {}

        universe = cfg['strategies'][strategy]['universe']
        output = eval("""{strategy}({universe}, '{date}')""".format(strategy=strategy,
                                                                  universe=universe,
                                                                  date=date))
        for key, value in output.items():
            strategy_output[strategy][key] = value

    return strategy_output

# Get the output of strategies
strategy_output = get_strategy_output(cfg['strategies_to_run'], date)

# put output in dataframe and fill any NaN with 0
strategy_output = pd.DataFrame(strategy_output).fillna(value=0)

# Calculate the 'result' by using strategy weights
strategy_output['result'] = np.sign(strategy_output.MA * cfg['strategies']['MA']['weight'] +
                                    strategy_output.coin_flip * cfg['strategies']['coin_flip']['weight'])

# Replace 1 with 'buy' and -1 with 'sell'
strategy_output['result'] = ['buy' if x==1 else 'sell' for x in strategy_output['result']]

# Only select result field and convert to dictionary
strategy_output = strategy_output['result'].to_dict()

# Connect to MYSQL db
db, cur = ut.connect_to_db(cfg)

# For each strategy and symbol we want to trade, get the latest price and insert into orders table
for sym in strategy_output:

    ask_price = md.get_market_data(sym, date, date).Close.ix[0]

    if dt.datetime.now().strftime('%Y%m%d') == date:
        status = 'NULL'
        exec_price = 'NULL'
    else:
        status = 'simulation'
        exec_price = ask_price

    security = sym
    action = strategy_output[sym]
    size = 5

    query = "INSERT INTO {table} (date, sim_id, security, action, size, ask_price, exec_price, status) " \
            "values ({time}, '{sim_id}', '{security}',  '{action}', '{size}', '{ask_price}', '{exec_price}'," \
            "'{status}');".format(table=cfg['mysql']['table'],
                                  time=date,
                                  sim_id=sim_id,
                                  security=security,
                                  action=action,
                                  size=size,
                                  ask_price=ask_price,
                                  exec_price=exec_price,
                                  status=status)
    cur.execute(query)


cur.close()
db.close()