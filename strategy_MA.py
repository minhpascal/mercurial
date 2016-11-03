import market_data as md
import datetime as dt
import pandas as pd


def MA(universe):

    """
    This function takes a universe and calculates near and far moving averages.
    If near term moving average is greater than far term moving average, then buy. Otherwise, sell.

    :param universe:
    :return:
    """

    # Define 'today' (based on day of the week)
    today = dt.datetime.now()

    if today.isoweekday() == 6:
        today = (today + dt.timedelta(-1)).strftime('%Y%m%d')
    elif today.isoweekday() == 7:
        today = (today + dt.timedelta(-2)).strftime('%Y%m%d')
    elif today.isoweekday() == 1:
        today = today = (today + dt.timedelta(-3)).strftime('%Y%m%d')
    else:
        today = (today + dt.timedelta(-1)).strftime('%Y%m%d')

    window_near = 5
    window_far = 10

    # Get the date 30 days from now. THis will be used to make sure we have enough market data to
    # calculate moving averages
    start = (dt.datetime.now() + dt.timedelta(-30)).strftime('%Y%m%d')

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
        data[sym] = md.get_market_data(sym, start, today)

        # Calculate 5 day moving average
        rolling_mean_near[sym] = pd.rolling_mean(data[sym].Close, window=window_near).ix[today]

        # Calculate 10 day moving average
        rolling_mean_far[sym] = pd.rolling_mean(data[sym].Close, window=window_far).ix[today]

        if rolling_mean_near[sym] > rolling_mean_far[sym]:
            decision[sym] = 1
        else:
            decision[sym] = -1

    return decision