import sys
import os 

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

cli.logs_db_path = lambda: "memories.db"

PROMPTs = [
    'you have limited memory. you must manage youro memory carefully. you have a db available of past memories. what questions do you have?'
]

MODEL ="orca-mini-3b-gguf2-q4_0"

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
    prompt_method = model.prompt
    template = open("./prompts/templates/twostep.txt").read()
    system = open("./prompts/system/file0.txt").read()
    prompt = f"Hello, you are {os.environ.get('USER', 'AGI')}. This is the intro hello prompt."
    response = prompt_method(prompt,
                             system=system,
                             # template=template # this isn't working, need to understand how to make an appropriate template
                             )
    for chunk in response:
        print(chunk, end='')
        sys.stdout.flush()
        print("")

    response = stream_response(response)
    response.log_to_db(db)

def main():
    intro()

if __name__ == "__main__":
    main()