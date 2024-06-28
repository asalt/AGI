# chat_async.py
import sys
import time
import asyncio
import aioconsole
from agi.event_loop_async import PriorityQueue, QueueEmpty

from agi.status_utils import print_status, console  # Import the console for direct use if needed

# from rich.console import Console
from rich.prompt import Prompt
# 
# console = Console()


from agi.log import get_logger, get_logger_async
logger = get_logger_async(__file__)

async def worker(name, queue, boredom_counter, initial_tic_threshold=10):

    tic_threshold = initial_tic_threshold
    while True:
        try:
            task = await queue.get()
            logger.debug(f"{name} got a task: {task}")
            # response
            print_status(f"I understood your message to be\n{task}")
            #await asyncio.sleep(1)  # Simulate task processing
            logger.debug("resetting counter because user event")
            boredom_counter['count'] = 0
            tic_threshold = initial_tic_threshold
        except QueueEmpty:
            logger.debug(f"{name} found no tasks, incrementing boredom counter.")
            boredom_counter['count'] += 1
            await asyncio.sleep(1)
        if boredom_counter['count'] > tic_threshold:
            await queue.put(f"I'm bored, I've been waiting {tic_threshold} ticks!", priority=2)
            tic_threshold = tic_threshold * 1.1
            logger.debug(f"{name} is bored after {tic_threshold} ticks.")
            boredom_counter['count'] = 0
            

async def chat_user_input(queue, msg="Enter text here: "):
    while True:
        # sys.stdout.write("\x1b[s")  # Save cursor position
        user_input = await asyncio.to_thread(Prompt.ask, "Enter text here: ", console=console)

        if user_input.lower() in ["exit", "quit"]:
            break
        await queue.put(user_input, priority=1)
        # sys.stdout.write("\x1b[u")  # Restore cursor position


async def main():
    queue = PriorityQueue()
    boredom_counter = {'count': 0}

    workers = [asyncio.create_task(worker(f"Worker {i}", queue, boredom_counter)) for i in range(1)]
    #worker = asyncio.create_task(worker(f"worker {1}", queue, boredom_counter))
    user_input_task = asyncio.create_task(chat_user_input(queue))

    await asyncio.gather(*workers, user_input_task)

asyncio.run(main())
