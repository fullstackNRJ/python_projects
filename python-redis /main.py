import redis
import logging

r = redis.Redis('localhost',6379)


logging.basicConfig()

class OutOfStockError(Exception):
    """Raised when PyHats.com is all out of today's hottest hat"""

def buyitem(r: redis.Redis, itemid: int) -> None:
    with r.pipeline() as pipe:
        error_count = 0
        while True:
            try:
                #Get available inventory, watching for changes
                # related to this itemid before the transaction
                pipe.watch(itemid)
                nleft: bytes = r.hget(itemid, "quantity")
                if nleft > b"0":
                    pipe.multi()
                    pipe.hincrby(itemid, -1)
                    pipe.hincrby(itemid, 1)
                    pipe.execute()
                    break
                else:
                    #stop watching the itemid and raise to break out
                    pipe.unwatch()
                    raise OutOfStockError(
                            f"Sorry, {itemid} is out of stock!")
            except redis.WatchError:
                #Log total num. of errors by this user to buy this item,
                # then try the same process again of WATCH/HGET/MULTI/EXEC
                error_count += 1
                logging.warning(
                        "WatchError #%d: %s; retrying",
                        error_count,itemid)
                return None
