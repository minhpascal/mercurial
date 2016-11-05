import MySQLdb
import market_data as md
import yaml
import pandas as pd
import numpy as np

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Import all strategies
for strategy in cfg['strategies']:
    exec("""from strategy_{strategy} import *""".format(strategy=strategy))

# Loop through all the strategies and get their output
# put them in a dictionary
def get_strategy_output(strategies):

    strategy_output = {}

    for strategy in strategies:

        strategy_output[strategy] = {}

        universe = cfg['strategies'][strategy]['universe']
        output = eval("""{strategy}({universe})""".format(strategy=strategy,
                                                          universe=universe))
        for key, value in output.items():
            strategy_output[strategy][key] = value

    return strategy_output

# Get the output of strategies
strategy_output = get_strategy_output(cfg['strategies_to_run'])

# put output in dataframe and fill any NaN with 0
strategy_output = pd.DataFrame(strategy_output).fillna(value=0)

# Calculate the 'result' by using strategy weights
strategy_output['result'] = np.sign(strategy_output.MA * cfg['strategies']['MA']['weight'] +
                                    strategy_output.coin_flip * cfg['strategies']['coin_flip']['weight'])

# Replace 1 with 'buy' and -1 with 'sell'
strategy_output['result'] = ['buy' if x==1 else 'sell' for x in strategy_output['result']]

# Only select result field and convert to dictionary

strategy_output = strategy_output['result'].to_dict()


# Connect to mysql database
db = MySQLdb.connect(host=cfg['mysql']['host'],    # your host, usually localhost
                     user=cfg['mysql']['user'],    # your username
                     passwd=cfg['mysql']['pwd'],   # your password
                     db=cfg['mysql']['db'])        # name of the database

db.autocommit(on=1)

# you must create a Cursor object. It will let you execute all the queries you need
cur = db.cursor()

# For each strategy and symbol we want to trade, get the latest price and insert into orders table
for sym in strategy_output:
    security = sym
    action = strategy_output[sym]
    size = 5
    ask_price = md.get_latest_price(sym)
    query = "INSERT INTO {table} (date, security, action, size, ask_price, exec_price, status) " \
            "values ({time}, '{security}',  '{action}', '{size}', '{ask_price}', '{exec_price}'," \
            "'{status}');".format(table=cfg['mysql']['table'],
                                  time='NOW()',
                                  security=security,
                                  action=action,
                                  size=size,
                                  ask_price=ask_price,
                                  exec_price='NULL',
                                  status='NULL')
    cur.execute(query)


cur.close()
db.close()