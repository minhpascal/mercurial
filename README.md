# mercurial

Mercurial is a framework that allows you to:

1. Get access to market data from yahoo
2. Plug-in strategies
3. Consolidate output of multiple strategies based on their weighting (not finished yet)
4. Execute trades via Interactive Brokers
5. Analyze your portfolio and compare to benchmark (S&P)

There are multiple components to Mercurial:

1. Strategy
  * This script consolidates output of multiple strategies and stores the data in a mysql table called orders. For example, currently, there are two strategies: strategy_MA and strategy_coin_flip.
2. Trade
  * This script reads strategy output from 'orders' table and executes the orders via Interactive Brokers. As orders are sent to Interactive Brokers, messages are received and stored in 'orders' table to reflect latest status of each order. For example, as an order is sent, it's status changes to 'opened' and as it is executed, it changes to 'filed'.
3. Analysis
  * As orders are executed, their executed price is stored in the same table. This transaction data is analyzed in the Analysis.py script and is compared to a benchmark (S&P).
