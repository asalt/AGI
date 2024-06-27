# think.py
# an early sketch trying to figure out the event loop
from queue import Queue, Empty
import threading
import time

def thinking_thread(queue, thinker):
    while True:
        try:
            # Check for new input, with a timeout
            prompt = queue.get(timeout=1)  # Adjust timeout as needed
            thinker.update_state('last_user_interaction', datetime.now())
            response = thinker.think(prompt)
            print(response)
        except Empty:
            # No input received, proceed with regular thinking
            thinker.perform_regular_thinking()

def user_input_thread(queue):
    while True:
        user_input = input("> ")
        queue.put(user_input)
        if user_input.lower() in ["exit", "quit"]:
            break

def run_conversation():
    conversation_queue = Queue()
    conversation_thinker = Think(conversation=None, db=get_db())  # Setup Think instance

    # Create threads for thinking and user input
    thinker_thread = threading.Thread(target=thinking_thread, args=(conversation_queue, conversation_thinker))
    input_thread = threading.Thread(target=user_input_thread, args=(conversation_queue,))

    # Start threads
    thinker_thread.start()
    input_thread.start()

    # Wait for threads to complete
    input_thread.join()
    thinker_thread.join()

run_conversation()
