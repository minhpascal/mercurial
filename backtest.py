"""
This script is for running backtesting our strategies. It will run the strategy script
for multiple dates.

1. Check if the date is a weekend or not.
2. Run the strategies
3. Run the analysis
"""

import datetime as dt
import argparse
from dateutil import parser
import os

# Parse the arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-start', '--start_date', help='start date for simulation', required=True)
arg_parser.add_argument('-end', '--end_date', help='end date for simulation', required=False)
arg_parser.add_argument('-sim_id', '--sim_id', help='id to keep track of the simulation', required=True)
args = vars(arg_parser.parse_args())

sim_id = args['sim_id']
start_date = args['start_date']

# If an end date is not specified, then use today's date as end date.
if args['end_date']:
    end_date = args['end_date']
else:
    end_date = dt.datetime.now().strftime('%Y%m%d')


# Function for getting list of dates (excluding weekends)
def daterange(start_date, end_date):

    start_date = parser.parse(start_date)
    end_date = parser.parse(end_date)

    for n in range(0,int((end_date - start_date).days)):

        date = start_date + dt.timedelta(n)

        # Don't include weekends
        if not date.isoweekday() in [6, 7]:
            date = date.strftime('%Y%m%d')
            yield date


# Run the strategies for each date
for date in daterange(start_date, end_date):
    print "Running strategy for {date} with id: {sim_id}".format(date=date,
                                                                 sim_id=sim_id)
    os.system("python strategy.py -date {date} -sim_id {sim_id}".format(date=date,
                                                                        sim_id=sim_id))


print "Finished running strategy for all the dates."
print "Running analysis."

# Run the analysis
os.system("python analysis.py -mode simulation -sim_id {sim_id}".format(sim_id=sim_id))