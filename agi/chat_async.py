# chat_async.py
import time
import asyncio
import aioconsole
from agi.event_loop_async import PriorityQueue, QueueEmpty

from agi.log import get_logger, get_logger_async
logger = get_logger_async(__file__)

async def worker(name, queue, boredom_counter, initial_tic_threshold=10):

    tic_threshold = initial_tic_threshold
    while True:
        try:
            task = await queue.get()
            logger.debug("got a task")
            await queue.put(task, priority=1)
            # await asyncio.sleep(1)  # Simulate task processing
            boredom_counter['count'] = 0
            tic_threshold = initial_tic_threshold
        except QueueEmpty:
            # print(f"{name} found no tasks, incrementing boredom counter.")
            boredom_counter['count'] += 1
            logger.debug("increasing counter")
            await asyncio.sleep(4)
        if boredom_counter['count'] > tic_threshold:
            await queue.put(f"I'm bored, I've been waiting {tic_threshold} ticks!", priority=2)
            tic_threshold = tic_threshold * 1.1
            logger.debug("resetting counter")
            boredom_counter['count'] = 0
            

async def chat_user_input(queue):
    while True:
        user_input = await aioconsole.ainput("Enter command: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        await queue.put(user_input, priority=1)

async def main():
    queue = PriorityQueue()
    boredom_counter = {'count': 0}

    workers = [asyncio.create_task(worker(f"Worker {i}", queue, boredom_counter)) for i in range(2)]
    user_input_task = asyncio.create_task(chat_user_input(queue))

    await asyncio.gather(*workers, user_input_task)

asyncio.run(main())
