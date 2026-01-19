from content import eod, gex, fred


def update_sequence():
    symbols = eod.priority_update_set()
    eod.Historical(symbols).update_sequence()
    eod.Intraday('SPY').update_sequence()
    gex.DIX().update_sequence()
    fred.Observations(['DTB3','SOFR90DAYAVG' ]).update_sequence()

    return True

if __name__ == "__main__":
    update_sequence()