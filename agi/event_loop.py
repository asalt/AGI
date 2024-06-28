from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Value, Event, Manager
import time

from . import chat

def handle_user_input(input_event):
    """Simulate user input and signal event."""
    while True:
        #user_input = input("User input> ")
        user_input = chat.user_input()
        if user_input:
            input_event.set()  # Signal that there's user input
        if user_input.lower() in ["exit", "quit"]:
            break

def handle_boredom(boredom_counter, input_event):
    """Monitor and handle boredom, resetting on user input."""
    while True:
        time.sleep(1)  # Check the boredom status every second
        if input_event.is_set():
            boredom_counter.value = 0  # Reset boredom counter on user input
            input_event.clear()  # Reset the event
            print("Boredom reset due to user activity.")
        else:
            boredom_counter.value += 1  # Increase boredom counter
            print(f"Boredom level: {boredom_counter.value}")
        if boredom_counter.value > 10:
            print("Triggering boredom response...")
            # Trigger some boredom response
            boredom_counter.value = 0  # Reset after response

def main():
    manager = Manager()
    boredom_counter = manager.Value('i', 0)  # Shared integer
    input_event = manager.Event()  # Shared event

    with ProcessPoolExecutor() as executor:
        # Submit tasks to the executor
        executor.submit(handle_user_input, input_event)
        executor.submit(handle_boredom, boredom_counter, input_event)

if __name__ == "__main__":
    main()

