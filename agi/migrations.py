# migrations.py
import datetime
from typing import Callable, List

from llm import migrations

MIGRATIONS: List[Callable] = []
migration = MIGRATIONS.append


@migration
def new_migration(db):  # example code from llm.migrations
    if db["newtable"].exists():
        # if "chat_id" not in db["log"].columns_dict: # should we do this  to relate it back to say logs table?
        #     db["log"].add_column("chat_id")
        return
    db["newtable"].create(
        {
            "one": str,
            "two": str,
            "three": str,
            "timestamp": str,
            "foreign1": str,
            "foreign2": str,
        },
        foreign_keys=[("foreign1", "foreign2")],
    )
