"""
This script is for analyzing transactions so we can compare our portfolio's performance to the market (S&P).

"""

import pandas as pd
import datetime as dt
from dateutil import parser
import MySQLdb
import market_data as md
import yaml
import utils as ut
import argparse

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-mode', '--mode', help='determine whether to run in simulation mode or normal', required=True)
arg_parser.add_argument('-sim_id', '--sim_id', help='id to keep track of the simulation', required=False)
args = vars(arg_parser.parse_args())

# If the analysis is being run in simulation mode,
# then run on transactions market as 'simulation'.
# Otherwise, run it for 'filled' transactions.
if args['mode'] == 'simulation':
    status = 'simulation'
else:
    status = 'filled'

sim_id = args['sim_id']

if not sim_id:
    sim_id = 'NULL'

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Connect to MYSQL db
db, cur = ut.connect_to_db(cfg)

query = "SELECT * from {db}.{table} where status='{status}' and " \
        "sim_id='{sim_id}';".format(table=cfg['mysql']['table'],
                                    db=cfg['mysql']['db'],
                                    status=status,
                                    sim_id=sim_id)

transactions = pd.read_sql(query, con=db)
transactions = transactions.set_index('order_id')

# Get today's date
today = dt.datetime.today().strftime("%Y%m%d")

# Get minimum transaction date
min_date = parser.parse(str(transactions.date.min()))
max_date = parser.parse(str(transactions.date.max()))


# Function for getting list of dates
def daterange(start_date, end_date, step):
    for n in range(0, int((end_date - start_date).days), step):
        yield start_date + dt.timedelta(n)


def pf_stats(single_date, transactions, min_date, flag):

    print transactions

    transactions['cost'] = transactions['exec_price'].astype(float) * transactions['size']

    query = "SELECT * from {db}.{table} where security='cash';".format(table='positions',
                                                                       db=cfg['mysql']['db'])

    cs = pd.read_sql(query, con=db)
    cs['action'] = None
    cs = cs.rename(columns={'total_value':'value', 'quantity':'size'})
    cs = cs.drop('avg_cost', 1)

    unique_stocks = pd.unique(transactions.security)

    price = {}
    for ticker in unique_stocks:
        price[ticker] = md.get_market_data(ticker, str(min_date), single_date)

    for index, row in transactions.iterrows():

        if row.action == 'buy':
            transactions.loc[index, 'value'] = row.size * price[row.security].tail(n=1)['Adj Close'].ix[0]
            cs['value'] = (cs['value'].astype(float) - (float(row.exec_price) * row.size))
        if row.action == 'sell':
            transactions.loc[index, 'value'] = row.size * float(row.exec_price)
            cs['value'] = (cs['value'].astype(float) + (float(row.exec_price) * row.size))

    transactions_active = transactions.groupby(['security', 'action']).sum()
    transactions_active = transactions_active.reset_index()
    transactions_active = transactions_active[['security', 'action', 'size', 'cost', 'value']]

    for index, row in transactions_active.iterrows():

        if row.action == 'sell':
            a = transactions_active['security'] == row.security
            b = transactions_active['action'] == 'buy'
            new_quantity = transactions_active[a & b].size - row.size
            new_value = new_quantity * (price[row.security].tail(n=1)['Adj Close'].ix[0])
            new_cost = (transactions_active[a & b].cost / transactions_active[a & b].size) * new_quantity

            transactions_active[a & b] = transactions_active[a & b].set_value(
                transactions_active[a & b].index, 'value', new_value)
            transactions_active[a & b] = transactions_active[a & b].set_value(
                transactions_active[a & b].index, 'size', new_quantity)
            transactions_active[a & b] = transactions_active[a & b].set_value(
                transactions_active[a & b].index, 'cost', new_cost)

    print transactions_active
    transactions_active = transactions_active[transactions_active['action'] != 'sell']
    transactions_active = transactions_active.append(cs)

    transactions_active['net'] = (transactions_active['value'] - transactions_active['cost'])
    transactions_active['net_change'] = 100 * transactions_active['net'] / transactions_active['cost']
    net = transactions_active.value.sum()

    if flag == 'snapshot':
        return transactions_active

    if flag == 'returns':
        return pd.DataFrame({'date': [single_date], 'total': [net]})


start_date = min_date
end_date = max_date

net = pd.DataFrame([])

print "Running analysis from {sd} to {ed}.".format(sd=start_date,
                                                   ed=end_date)

for single_date in daterange(start_date, end_date, step=1):
    if single_date >= min_date:
        single_date = single_date.strftime("%Y%m%d")
        net = net.append(pf_stats(single_date, transactions, min_date, 'returns'))

if len(net):
    net = net.set_index('date')
else:
    print "No data returned"


# Compare portfolio returns to S&P

# Get data for S%P 500 from Google Finance
sp = md.get_market_data('^GSPC', str(transactions.date.min()), today)

# Combine SPY returns with portfolio returns
final = pd.merge(sp, net, how='inner', left_index=True, right_index=True)

# Calculate percentage change
final['sp_returns'] = final.Close.pct_change()*100
final['pt_returns'] = final.total.pct_change()*100

print final[['total', 'sp_returns', 'pt_returns']]