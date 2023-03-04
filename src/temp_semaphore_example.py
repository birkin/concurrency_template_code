import logging
import trio


logging.basicConfig( level=logging.DEBUG )
log = logging.getLogger(__name__)


async def worker(limiter):
    # log.debug( f'limiter_a, ``{limiter.__dict__}``' )
    async with limiter:
        log.debug( f'limiter_b, ``{limiter}``' )
        log.debug( f'limiter.lot, ``{limiter._lot}``' )
        log.debug( f'limiter.lot, ``{limiter._borrowers}``' )
        log.debug( f'limiter.lot, ``{limiter._pending_borrowers}``' )
        log.debug( f'limiter.lot, ``{limiter._total_tokens}``' )
        print("Worker is doing some work...")
        await trio.sleep(1)
        print("Worker finished work!")

async def main():
    # Create a semaphore with an initial value of 2
    # limiter = trio.Semaphore(2)
    limiter = trio.CapacityLimiter(2)
    
    # Start 3 workers that will try to acquire the semaphore
    async with trio.open_nursery() as nursery:
        for i in range(10):
            nursery.start_soon(worker, limiter)
    
if __name__ == "__main__":
    trio.run(main)
