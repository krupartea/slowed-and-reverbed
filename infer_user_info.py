import pandas as pd
from pathlib import Path
import pickle

MESSAGES_DIR = Path(r"messages")

def get_user_df(user_id):
    messages = []
    for filename in (MESSAGES_DIR / str(user_id)).iterdir():
        with filename.open("rb") as f:
            message = pickle.loads(f.read())
            messages.append(vars(message))
    df = pd.DataFrame(messages)

    return df


def infer_mode(user_id):
    pass


get_user_df(7057257486)
pass