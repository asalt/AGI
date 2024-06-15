import sys
import os 

import threading
import time
from queue import Queue, Empty

import click

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
import logging
logging.basicConfig(level=logging.INFO)


cli.logs_db_path = lambda: "memories.db"

PROMPTs = [
    'you have limited memory. you must manage youro memory carefully. you have a db available of past memories. what questions do you have?'
]
if os.environ.get('MODEL') is not None:
    MODEL = os.environ.get('MODEL') 
else:
    MODEL = "orca-mini-3b-gguf2-q4_0"
logging.info(f"Using model: {MODEL}")


### event loop

def user_input(queue, model, conversation, db=None):
    """Thread function for handling user input."""
    db = get_db()

    # flags
    in_multi = False 
    #
    validated_options = dict()
    click.echo("Chatting with {}".format(model.model_id))
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
        response = conversation.prompt(prompt, system, **validated_options)
        # System prompt only sent for the first message:
        for chunk in response:
            print(chunk, end="")
            sys.stdout.flush()
        if db is not None:
            response.log_to_db(db)
        print("")

def automated_interaction(queue, model, conversation, db=None, interval=100):
    """Thread function for automated interactions."""

    db = get_db()
    while True:
        # Check if there is an interruption from the user input
        try:
            message = queue.get_nowait()
            if message == 'quit':
                break
            print(f"Handling user input: {message}")
            # Here would be the interaction with the model using the message
        except Empty:
            # No user interruption, proceed with scheduled message

            # print("Sending scheduled prompt to the model...")
            # Wait for the next scheduled time
            step_duration = interval / 100
            time.sleep(interval)
            # for _ in tqdm(range(100), desc="Boredom counter: "):
            #    time.sleep(step_duration)

            response = conversation.prompt("""**This is an internal message not from the user**
it is an internal thought. 
it has been some time without user input and you are getting bored. 
refer to the recent topic. reiterate or re-ask a question.
if there was no recent topic or question at hand, then..
tell a joke. make up a rhyme. say something interesting. address the user. 
the user does not know about this message.
""")
            response = stream_response(response)
            if db is not None:
                response.log_to_db(db)




def event_loop(model, conversation, db):
    queue = Queue()
    interval = 10  # Interval in seconds for automated messages

    # Create threads
    automated_thread = threading.Thread(target=automated_interaction, args=(queue, model, conversation, db, interval ))
    user_thread = threading.Thread(target=user_input, args=(queue, model, conversation, db))

    # Start threads
    automated_thread.start()
    user_thread.start()

    # Wait for threads to finish
    user_thread.join()
    automated_thread.join()

    print("Conversation ended.")

### db stuff

def get_db():
    """ Initialize and return the database connection. """
    log_path = cli.logs_db_path()
    db = sqlite_utils.Database(log_path)
    migrate(db)
    return db

def log_to_db(db, response):
    """ Log the response to the database. """
    response.log_to_db(db)

def query_db(db, query):
    """ Run a specific query on the database and return results. """
    return list(db.query(query))

def get_response(model, prompt):
    """ Send a prompt to the model and return the response. """
    prompt_method = model.prompt
    return prompt_method(prompt)

def _xx_main():
    db = get_db()
    model = get_model(MODEL)

    # Initial interaction
    response = get_response(model, PROMPT)
    log_to_db(db, response)

    # Follow-up interaction
    conv_query = "select * from conversations"
    conversations = query_db(db, conv_query)
    resp_query = "select * from responses"
    responses = query_db(db, resp_query)
    follow_up_prompt = f"""
    No look you do have memories! they're in this database called memories.db
    look i run this sql {conv_query} and get `{conversations}`
    and if i run {resp_query} I get {responses}.
    So every time we chat it is saved and you can revisit! how cool is that!?
    so if you want to review any memories just tell me what you want to see, can use raw sql format it's just sqlite here nice and simple.
    """
    follow_up_response = get_response(model, follow_up_prompt)
    log_to_db(db, follow_up_response)

def _xmain():

    log_path = cli.logs_db_path()
    db = sqlite_utils.Database(log_path)
    migrate(db)

    model = get_model(MODEL)
    prompt_method = model.prompt
    response = prompt_method(PROMPTs[0])
    response_txt = response.text


    response.log_to_db(db)

    prompt2 = f"""
    No look you do have memories! they're in this database called memories.db
    look i run this code and get `list(db.query('select * from conversations'))` == {list(db.query('select * from conversations'))}
    and if i run `list(db.query('select * from responses'))` I get {list(db.query('select * from responses'))}.
    So every time we chat it is saved and you can revisit! how cool is that!?
    so if you want to review any memories just tell me what you want to see, can use raw sql format it's just sqlite here nice and simple.
"""
    response2 = prompt_method(prompt2)
    response2.log_to_db(db)
    response_txt = response.text

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
You can start the conversation by saying hi or something.
Also confirm you understand these instructions.
"""
    response = conversation.prompt(prompt,
                             system=system,
                             # template=template # this isn't working, need to understand how to make an appropriate template
                             )

    response = stream_response(response)
    response.log_to_db(db)

    event_loop(model, conversation, db)


def main():
    intro()

if __name__ == "__main__":
    main()
