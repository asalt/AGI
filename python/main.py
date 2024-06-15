import sys
import os 
import inspect

import threading
import time
from queue import Queue, Empty

import click
import time

from tqdm import tqdm

import sqlite_utils
import llm
from llm.migrations import migrate
from llm import cli
from llm import (
    Collection,
    Conversation,
    Response,
    Template,
    UnknownModelError,
    encode,
    get_embedding_models_with_aliases,
    get_embedding_model_aliases,
    get_embedding_model,
    get_key,
    get_plugins,
    get_model,
    get_model_aliases,
    get_models_with_aliases,
    user_dir,
    set_alias,
    remove_alias,
)
# import logging
# logging.basicConfig(level=logging.INFO)

# local
from log import get_logger
from actions import execute_command

#

logger = get_logger(__file__)

cli.logs_db_path = lambda: "memories.db"

if os.environ.get('MODEL') is not None:
    MODEL = os.environ.get('MODEL') 
else:
    MODEL = "orca-mini-3b-gguf2-q4_0"
logger.info(f"Using model: {MODEL}")


INITIAL_INTERVAL = 40



### event loop

def think(text, model, conversation):
    db = get_db()

    response = conversation.prompt(
f"""** internal response ** 
use this response to outline your response to the user.
they will not see it, this is for you to plan.
""" + text )
    
    print("** Internal Thought **\n\n")
    response = stream_response(response)
    print("** End of internal thought **\n\n")
    
    if db is not None:
        response.log_to_db(db) # TODO categorize as internal

    response = conversation.prompt(
f"""** external response **
this is your external response to the user
you may choose to say nothing and just "**wait**" or similar.
don't repeat your inner response, except the actual message you wish to send.
""" )
    
    response = stream_response(response)

    if db is not None:
        response.log_to_db(db) # TODO categorize as external
    
    return conversation
    

def user_input(queue, model, conversation, db=None):
    """Thread function for handling user input."""
    db = get_db()

    # flags
    in_multi = False 
    #
    validated_options = dict()
    click.echo("\nChatting with {}".format(model.model_id))
    click.echo("Type 'exit' or 'quit' to exit")
    click.echo("Type '!multi' to enter multiple lines, then '!end' to finish")
    while True:
        prompt = click.prompt("", prompt_suffix="> " if not in_multi else "")
        if prompt.strip().startswith("!multi"):
            in_multi = True
            bits = prompt.strip().split()
            if len(bits) > 1:
                end_token = "!end {}".format(" ".join(bits[1:]))
            continue
        if in_multi:
            if prompt.strip() == end_token:
                prompt = "\n".join(accumulated)
                in_multi = False
                accumulated = []
            else:
                accumulated.append(prompt)
                continue
        # if template_obj:
        #     try:
        #         prompt, system = template_obj.evaluate(prompt, params)
        #     except Template.MissingVariables as ex:
        #         raise click.ClickException(str(ex))
        if prompt.strip() in ("exit", "quit"):
            break
        system = None #  system message already set
        conversation = think(prompt, model, conversation)
        # System prompt only sent for the first message:
        # for chunk in response:
        #     print(chunk, end="")
        #     sys.stdout.flush()
        # if db is not None:
        #     response.log_to_db(db)
        print("")
    return conversation


def automated_interaction(queue, model, conversation, db=None, interval=100):
    """Thread function for automated interactions."""
    current_interval = interval
    tics = 0
    db = get_db()

    def handle_event(queue):
        try:
            conversation = queue.get_nowait()
            logger.info("Got a new conversation, resetting loop.")
            return conversation, True
        except Empty:
            return None, False

    while True:
        start_time = time.time()
        received_new_message = False

        while time.time() - start_time < current_interval:
            new_conversation, received = handle_event(queue)
            if received:
                conversation = new_conversation
                received_new_message = True
                #start_time = time.time()
                logger.info('exiting inner loop')
                break  # Break from the inner while loop to process new message immediately

        if not received_new_message:  # Check if the loop exited without receiving new message
            logger.info('Waited too long. Got bored.')
            tics += 1
            internal_thought = f"""**This is an internal message not from the user**
It has been some time without user input and you are getting bored.
Refer to the recent topic. Reiterate or re-ask a question.
If there was no recent topic or question at hand, then..
Tell a joke. Make up a rhyme. Say something interesting. Address the user.
The user does not know about this message.
So far it has been {tics} 'moments' with no input.
The larger the number, the more bored you are"""
            conversation = think(internal_thought, model, conversation)

            current_interval = interval * (1.1 + tics)



def event_loop(model, conversation, db):
    queue = Queue()
    # interval = 100  # Interval in seconds for automated messages
    interval = INITIAL_INTERVAL # global var defined at top

    # Create threads
    automated_thread = threading.Thread(target=automated_interaction, args=(queue, model, conversation, db, interval ))
    user_thread = threading.Thread(target=user_input, args=(queue, model, conversation, db))

    # Start threads
    automated_thread.start()
    user_thread.start()

    # Wait for threads to finish
    user_thread.join()
    automated_thread.join()
    #import ipdb; ipdb.set_trace()

    print("Conversation ended.")
    # return conversation # how to do this?

### db stuff

def get_db():
    """ Initialize and return the database connection. """
    log_path = cli.logs_db_path()
    db = sqlite_utils.Database(log_path)
    migrate(db)
    return db

# def log_to_db(db, response):
#     """ Log the response to the database. """
#     response.log_to_db(db)

def query_db(db, query):
    """ Run a specific query on the database and return results. """
    return list(db.query(query))

# def get_response(model, prompt):
#     """ Send a prompt to the model and return the response. """
#     prompt_method = model.prompt
#     return prompt_method(prompt)


def stream_response(response):
    for chunk in response:
        print(chunk, end='')
        sys.stdout.flush()
    print("")
    return response


def intro():

    # log_path = cli.logs_db_path()
    # db = sqlite_utils.Database(log_path)
    # migrate(db)
    db = get_db()

    model = get_model(MODEL)
    conversation = Conversation(model=model)

    # prompt_method = model.prompt

    template = open("../prompts/templates/twostep.txt").read()
    system = open("../prompts/system/file0.txt").read()
    prompt = f"""Hello, your name is {os.environ.get('USER', 'AGI')}. You are a helpful assistant. 
This is your intiation prompt. You are about to incorporated into an event loop whereby you way user input.
You can start the conversation by saying hi or something. Be yourself.
"""
   #prompt += f"when you respond use this format:

   # prompt += f"""
   # You have a variety of commands available to you.
   # Here's one that let's you run commands on the default shell. 
   # Maybe the user would like you to search the filesystem, for example.

   # {inspect.getsource(execute_command)} """#
    conversation = think(prompt, model, conversation)
    event_loop(model, conversation, db)
    # response = conversation.prompt(prompt,
    #                          system=system,
    #                          )

    # response = stream_response(response)
    # response.log_to_db(db)



def main():
    intro()

if __name__ == "__main__":
    main()
    #import ipdb; ipdb.set_trace()
