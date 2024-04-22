import json
from typing import Any


def recover(msg: str) -> dict[str, Any]:
    blob = {}
    # Assuming the padding takes up a lot of the message, try and recover if data corruption
    # happened in the padding
    if "padd" in msg:
        if ", \"padd" in msg:
            padding_beginning = ', "padd'
        else:
            padding_beginning = ", 'padd'"
        rest_of_msg = msg.split(padding_beginning)[0]
        proper_msg = rest_of_msg + "}"
        print(proper_msg)
        blob = json.loads(proper_msg)
    else:
        raise json.JSONDecodeError("The message does not have padding in it!", msg, 0)
    return blob
