import market_data as md
import datetime as dt
import pandas as pd
from dateutil import parser


def MA(universe, date):

    """
    This function takes a universe and calculates near and far moving averages.
    If near term moving average is greater than far term moving average, then buy. Otherwise, sell.

    :param universe:
    :return:
    """

    # Define 'today' (based on day of the week)
    #today = dt.datetime.strptime(date, '%Y%m%d')

    # Get the date 30 days from now. THis will be used to make sure we have enough market data to
    # calculate moving averages
    start = (parser.parse(date) + dt.timedelta(-30)).strftime('%Y%m%d')

    window_near = 5
    window_far = 10

    # get data for last 10 days
    # get data for last 30 days
    # calc two MA
    # if 5MA>20MA, buy
    # else sell

    data = {}
    rolling_mean_near = {}
    rolling_mean_far = {}
    decision = {}

    for sym in universe:

        # Get latest close price for a security
        data[sym] = md.get_market_data(sym, start, date)

        # Calculate 5 day moving average
        rolling_mean_near[sym] = pd.rolling_mean(data[sym].Close, window=window_near).ix[date]

        # Calculate 10 day moving average
        rolling_mean_far[sym] = pd.rolling_mean(data[sym].Close, window=window_far).ix[date]

        if rolling_mean_near[sym] > rolling_mean_far[sym]:
            decision[sym] = 1
        else:
            decision[sym] = -1

    return decision