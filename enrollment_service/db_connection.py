import sqlite3
import contextlib
# import logging

# logging.basicConfig(filename=f'{__name__}.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def get_db():
    with contextlib.closing(sqlite3.connect("./var/enrollment_local.db")) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        #db.set_trace_callback(logging.debug)
        yield db