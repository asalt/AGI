# chat_async.py
import sys
import time
import asyncio
import aioconsole
import datetime

from agi.event_loop_async import PriorityQueue, QueueEmpty, Task
from agi.think import think


# from agi.status_utils import print_status, print_body, print_footer, console, layout  # Import the console for direct use if needed

from agi.log import get_logger, get_logger_async

logger = get_logger_async(__file__)
from agi.db import get_db


def print_status(message):
    # Clear the current input line and print the message
    sys.stdout.write("\033[F\033[K")
    print(message)
    print("\n\n")
    # Redisplay the input prompt without waiting for input
    sys.stdout.write("Enter text here: ")
    sys.stdout.flush()


async def worker(
    name, priority_queue, boredom_counter, initial_tic_threshold=10, conversation=None
):

    tic_threshold = initial_tic_threshold
    while True:
        try:
            task = await priority_queue.get()
            logger.debug(f"{name} got a task: {task}")
            # response
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            print_status(f"{current_time}:  {name} received the message to be\n{task.message}")
            conversation = await think(task.message, conversation)
            # await update_queue.put((f"{current_time}:  {name} understood the message to be\n{task}", 'output'))

            # await asyncio.sleep(1)  # Simulate task processing
            if task.input_type == "user":
                logger.debug("resetting counter because user event")
                boredom_counter["count"] = 0
                tic_threshold = initial_tic_threshold
        except QueueEmpty:
            logger.debug(f"{name} found no tasks, incrementing boredom counter.")
            boredom_counter["count"] += 1
            await asyncio.sleep(1)
        if boredom_counter["count"] > tic_threshold:
            await priority_queue.put(
                Task(
                    f" **INTERNAL THOUGHT** I (the AI) has been waiting {tic_threshold} ticks! (this is not a user message)",
                    "internal",
                    priority=2,
                )
            )

            tic_threshold = tic_threshold * 1.2
            logger.debug(f"{name} is bored after {tic_threshold} ticks.")
            boredom_counter["count"] = 0


async def chat_user_input(priority_queue, msg="Enter text here: "):
    while True:
        user_input = await aioconsole.ainput()

        # user_input = await asyncio.to_thread(Prompt.ask, "", console=console)

        if user_input.lower() in ["exit", "quit"]:
            break
        await priority_queue.put(Task(user_input, "user", priority=1))


        # layout['footer'].update(Panel(msg, style="on red"))
        # layout['footer'].update(user_input)

        # # Directly print to the 'input' area using console.input within a specific area
        # with console.capture() as capture:  # Capture output to prevent it from printing directly
        #     user_input = await asyncio.to_thread(
        #         Prompt.ask, "Enter text here: ", console=console
        #     )
        # layout['footer'].update(capture.get())  # Update the 'input' area with captured input

        # sys.stdout.write("\x1b[u")  # Restore cursor position


async def main(conversation=None):
    # update_queue = asyncio.Queue()
    # updater_task = asyncio.create_task(ui_updater(update_queue))

    priority_queue = PriorityQueue()
    boredom_counter = {"count": 0}

    workers = [
        asyncio.create_task(
            worker(
                f"Worker {i}",
                priority_queue,
                boredom_counter,
                conversation=conversation,
            )
        )
        for i in range(1)
    ]
    # worker = asyncio.create_task(worker(f"worker {1}", queue, boredom_counter))
    user_input_task = asyncio.create_task(chat_user_input(priority_queue))

    print_status("Enter text here: ")
    await asyncio.gather(*workers, user_input_task)


if __name__ == "__main__":
    asyncio.run(main())
