import pandas as pd
import datetime as dt
from dateutil import parser
import MySQLdb
import market_data as md
import yaml

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Connect to mysql database
db = MySQLdb.connect(host=cfg['mysql']['host'],    # your host, usually localhost
                     user=cfg['mysql']['user'],         # your username
                     passwd=cfg['mysql']['pwd'],  # your password
                     db=cfg['mysql']['db'])        # name of the data base

cur = db.cursor()
db.autocommit(on=1)

query = "SELECT * from {db}.{table} where status='filled';".format(table=cfg['mysql']['table'],
                                                                   db=cfg['mysql']['db'])

transactions = pd.read_sql(query, con=db)
transactions = transactions.set_index('order_id')

# Get today's date
today = dt.datetime.today().strftime("%Y%m%d")

# Get minimum transaction date
min_date = parser.parse(str(transactions.date.min()))


# Function for getting list of dates
def daterange(start_date, end_date, step):
    for n in range(0, int((end_date - start_date).days), step):
        yield start_date + dt.timedelta(n)


def pf_stats(single_date, transactions, min_date, flag):

    query = "SELECT * from {db}.{table} where status='filled';".format(table=cfg['mysql']['table'],
                                                                       db=cfg['mysql']['db'])
    transactions = pd.read_sql(query, con=db)
    transactions = transactions.set_index('order_id')

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

    transactions_active = transactions_active[transactions_active['action'] != 'sell']
    transactions_active = transactions_active.append(cs)

    transactions_active['net'] = (transactions_active['value'] - transactions_active['cost'])
    transactions_active['net_change'] = 100 * transactions_active['net'] / transactions_active['cost']
    net = transactions_active.value.sum()

    if flag == 'snapshot':
        return transactions_active

    if flag == 'returns':
        return pd.DataFrame({'date': [single_date], 'total': [net]})


start_date = parser.parse('20160905')
end_date = parser.parse(today)

net = pd.DataFrame([])

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