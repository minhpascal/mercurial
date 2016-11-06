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
