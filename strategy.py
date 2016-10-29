import MySQLdb
import market_data as md
import yaml

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

strategy_output = get_strategy_output(cfg['strategies'])

# Connect to mysql database
db = MySQLdb.connect(host=cfg['mysql']['host'],    # your host, usually localhost
                     user=cfg['mysql']['user'],    # your username
                     passwd=cfg['mysql']['pwd'],   # your password
                     db=cfg['mysql']['db'])        # name of the database

db.autocommit(on=1)

# you must create a Cursor object. It will let you execute all the queries you need
cur = db.cursor()

# For each strategy and symbol we want to trade, get the latest price and insert into orders table
for strategy in strategy_output:
    for sym in strategy_output[strategy]:
        security = sym
        action = strategy_output[strategy][sym]
        size = 5
        ask_price = md.get_latest_price(sym)
        query = "INSERT INTO {table} (date, strategy, security, action, size, ask_price, exec_price, status) " \
                "values ({time}, '{strategy}', '{security}',  '{action}', '{size}', '{ask_price}', '{exec_price}'," \
                "'{status}');".format(table=cfg['mysql']['table'],
                                      time='NOW()',
                                      strategy=strategy,
                                      security=security,
                                      action=action,
                                      size=size,
                                      ask_price=ask_price,
                                      exec_price='NULL',
                                      status='NULL')
        cur.execute(query)


cur.close()
db.close()