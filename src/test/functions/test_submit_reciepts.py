import json
from src.app.functions import submit_reciepts as target


def test_lambda_handler():
    path = "src/test/functions/input.json"
    with open(path) as f:
        event = json.load(f)

    result = target.lambda_handler(event, None)
    assert result == {"statusCode": 200, "body": '"OK"'}
