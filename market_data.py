"""
This library is for getting market data from Yahoo!
"""

from pandas.io.data import DataReader
import datetime as dt


def get_market_data(ticker, start_date, end_date):

    """
    This function gets market data for a ticker from Yahoo!

    :param ticker:
    :param start_date:
    :param end_date:
    :return:
    """
    return DataReader(ticker, "yahoo", start_date, end_date)


def get_latest_price(ticker):

    """
    This function uses get_market_data function to get latest
    close price for a ticker.

    :param ticker:
    :return:
    """

    today = dt.datetime.now()

    if today.isoweekday() == 6:
        today = (today + dt.timedelta(-1)).strftime('%Y%m%d')
    elif today.isoweekday() == 7:
        today = (today + dt.timedelta(-2)).strftime('%Y%m%d')
    elif today.isoweekday() == 1:
        today = today = (today + dt.timedelta(-3)).strftime('%Y%m%d')
    else:
        today = (today + dt.timedelta(-1)).strftime('%Y%m%d')

    df = get_market_data(ticker, today, today)

    return df.Close.ix[0]