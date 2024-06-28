# think.py
import sys
import asyncio
from agi.db import get_db
from agi.log import get_logger_async


def stream_response(response):
    for chunk in response:
        print(chunk, end='')
        sys.stdout.flush()
    print("")
    return response


# async def stream_response(response):
#     loop = asyncio.get_event_loop()
#     # Run the blocking operation in an executor
#     await loop.run_in_executor(None, lambda: list(response))
#     for chunk in response._chunks:  # Assuming _chunks holds all the output after forced iteration
#         print(chunk, end='')
#         sys.stdout.flush()
#     print("")
#     return response

async def think(text, conversation):
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
