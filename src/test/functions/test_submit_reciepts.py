import json
from src.app.functions import submit_reciepts as target


def test_callback():
    path = "src/test/functions/input.json"
    with open(path) as f:
        event = json.load(f)

    result = target.callback(event, None)
    assert result == {"statusCode": 200, "body": '"OK"'}
