# Trading Profits Calculator

Calculates trading profits by matching sell transactions with corresponding buy transactions, using the FIFO (first in, first out) principle. Supports fractional/partial matching for sells/buys.

In particular, this implementation can help with tax declarations by calculating taxable gains and the holding period for each sale. For example, under German tax regulations as of 2020, any gains on crypto currency sales with a holding period of more than 1 year are tax free, whereas for shorter holding periods the net gains (sale proceeds minus purchase cost) are taxable.

Reads transaction CSV files exported from the great [Portfolio Performance](https://www.portfolio-performance.info) app (choose File - Export - Depot Transactions/Depotumsätze).

## Requirements

* Python 3.x

## Run

1) Export transactions from Portfolio Performance. Choose "File" - "Export" - "Depot Transactions/Depotumsätze" to store one or more depot's transactions in CSV files in on selected directory.

2) Run `python analyze.py <path to directory with depot csvs>` to run the calculation. Edit analyze.py as needed to export all sales from one tax year into an XLS file, for example.
