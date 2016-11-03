import random


def coin_flip(universe):

    """
    Dummy strategy. Get a random integer from 0 to 1 and based on that, decide whether to buy or sell.

    :param universe:
    :return:
    """

    num = random.randrange(0, 2)
    decision = {}

    for sym in universe:
        if num:
            decision[sym] = 1
        else:
            decision[sym] = -1

    return decision