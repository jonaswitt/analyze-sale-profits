#!/usr/bin/python
# -*- coding: utf8 -*-

import pandas as pd
import numpy as np
import os
import sys

if len(sys.argv) < 2:
    print("usage: analyze.py <path to directory with depot csvs>")
    sys.exit(1)
depotDir = sys.argv[1]

dfs = []
for fName in os.listdir(depotDir):
    if not fName.endswith(".csv"):
        continue
    fPath = os.path.join(depotDir, fName)
    df = pd.read_csv(fPath, sep=";", decimal=",", thousands=".",
        parse_dates=["Datum"],
        # index_col="Datum"
    )
    df["Depot"] = ".".join(fName.split(".")[:-1])
    dfs.append(df)

df = pd.concat(dfs).sort_values("Datum")
df = df.drop(["Buchungswährung", "Bruttobetrag", "Währung Bruttobetrag", "Wechselkurs", "ISIN", "WKN", "Ticker-Symbol", "Notiz"], axis=1)
df = df[((df["Typ"] == "Kauf") | (df["Typ"] == "Verkauf") | (df["Typ"] == "Einlieferung") | (df["Typ"] == "Auslieferung"))]

df["Bruttowert"] = df["Wert"] - df["Gebühren"] - df["Steuern"]
df["Kurs"] = (df["Bruttowert"] / df["Stück"]).abs()
df["KursMitGeb"] = (df["Bruttowert"] / df["Stück"]).abs()

inRowsIndexer = (df["Typ"] == "Kauf") | (df["Typ"] == "Einlieferung")
df.loc[inRowsIndexer, "InOut"] = 1
outRowsIndexer = (df["Typ"] == "Verkauf") | (df["Typ"] == "Auslieferung")
df.loc[outRowsIndexer, "InOut"] = -1

tdfs = []

for wp in sorted(df["Wertpapiername"].unique()):
    # if wp != "Stellar Lumen":
    #     continue

    wdf = df[df["Wertpapiername"] == wp].drop(["Wertpapiername"], axis=1)
    wdf["Bestand"] = (wdf["Stück"] * np.sign(wdf["InOut"])).cumsum()

    print(wp)
    # print(wdf.drop(["Gebühren", "Steuern", "Bruttowert"], axis=1))

    fifoStack = []
    transactionLog = []
    for date, row in wdf.iterrows():
        if row["InOut"] == 1:
            fifoStack.append(row)
            transactionLog.append(dict(row))

        elif row["InOut"] == -1:
            sellAmt = row["Stück"]

            amtRemaining = sellAmt
            while amtRemaining > 0 and len(fifoStack) > 0:
                purchase = dict(fifoStack[0])
                purchaseAmt = purchase["Stück"]
                if purchaseAmt < amtRemaining:
                    # purchase counts full, need to split sale
                    matchedAmt = purchaseAmt
                    fifoStack.pop(0)
                elif purchaseAmt > amtRemaining:
                    # purchase counts in part, need to reduce
                    matchedAmt = amtRemaining
                    fifoStack[0]["Stück"] -= amtRemaining
                else:
                    # exact fit
                    matchedAmt = purchaseAmt
                amtRemaining -= matchedAmt

                halteDauer = (row["Datum"] - purchase["Datum"]).total_seconds() / 60 / 60 / 24
                outRow = {
                    "Datum": row["Datum"],
                    "Depot": row["Depot"],
                    "Typ": row["Typ"],
                    "Kurs": row["Kurs"],
                    "InOut": -1,
                    "Gebühren": row["Gebühren"] / sellAmt * matchedAmt,
                    "Steuern": row["Steuern"] / sellAmt * matchedAmt,
                    "Wert": row["Wert"] / sellAmt * matchedAmt,
                    "Bruttowert": row["Bruttowert"] / sellAmt * matchedAmt,
                    "Stück": matchedAmt,
                    "Anschaffungsdatum": purchase["Datum"],
                    "Haltedauer Tage": halteDauer,
                    "Anschaffungskurs": purchase["Kurs"],
                    "Anschaffungskosten": matchedAmt * purchase["KursMitGeb"],
                }
                outRow["Gewinn"] = -outRow["Bruttowert"] - outRow["Anschaffungskosten"]
                if halteDauer < 365 and outRow["Gewinn"] > 0:
                    outRow["Steuergewinn"] = outRow["Gewinn"]
                else:
                    outRow["Steuergewinn"] = 0
                transactionLog.append(outRow)

    tdf = pd.DataFrame(transactionLog)
    tdf["Bestand"] = (tdf["Stück"] * np.sign(tdf["InOut"])).cumsum()
    print(tdf.drop(["Gebühren", "Steuern", "Anschaffungskurs", "Anschaffungskosten", "Haltedauer Tage", "Steuergewinn"], axis=1))

    # tdf.to_csv("{}.csv".format(wp))

    tdf["Wertpapiername"] = wp
    tdfs.append(tdf)

    print()
    print()


tdf = pd.concat(tdfs)

verkauf = tdf[(tdf["Typ"] == "Verkauf")]
verkauf2019 = verkauf[(verkauf["Datum"] >= "2019-01-01") & (verkauf["Datum"] <= "2019-12-31")]
print(verkauf2019)

verkauf2019.to_excel("verkauf2019.xlsx", index=False)
