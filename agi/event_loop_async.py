import sys
import asyncio
import heapq

from agi.status_utils import print_status, console  # Import the console for direct use if needed


# def print_status(message):
#     sys.stdout.write("\x1b[s\x1b[1A\x1b[2K")  # Move cursor up and clear line
#     print(message)
#     sys.stdout.write("\x1b[u")  # Restore cursor position


class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0
    
    async def put(self, item, priority):
        heapq.heappush(self._queue, (priority, self._index, item))
        self._index += 1
    
    async def get(self):
        if self._queue:
            item = heapq.heappop(self._queue)[-1]
            return item
            # print_status(item)
        raise QueueEmpty()

class QueueEmpty(Exception):
    pass

# async def worker(name, queue, boredom_counter):
#     while True:
#         try:
#             # Reset boredom counter when a task is received
#             task = await queue.get()
#             print(f"{name} executing {task}")
#             boredom_counter['count'] = 0
#             await asyncio.sleep(1)  # Simulate doing the task
#         except QueueEmpty:
#             print(f"{name} found no tasks, incrementing boredom counter.")
#             boredom_counter['count'] += 1
#             if boredom_counter['count'] > 10:  # Trigger a boredom response
#                 print(f"{name} is bored. Initiating boredom protocol.")
#                 boredom_counter['count'] = 0
#             await asyncio.sleep(1)
# 
# async def simulate_user_input(queue):
#     while True:
#         # Simulate random user input
#         await asyncio.sleep(5)  # User inputs something every 5 seconds
#         await queue.put("User input task", priority=1)
# 
# async def main():
#     queue = PriorityQueue()
#     boredom_counter = {'count': 0}
# 
#     worker1 = asyncio.create_task(worker("Worker 1", queue, boredom_counter))
#     worker2 = asyncio.create_task(worker("Worker 2", queue, boredom_counter))
#     input_simulator = asyncio.create_task(simulate_user_input(queue))
# 
#     await asyncio.gather(worker1, worker2, input_simulator)
# 
# asyncio.run(main())
