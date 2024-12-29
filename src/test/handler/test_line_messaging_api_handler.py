import json
from linebot.models.events import MessageEvent
from src.app.handler import line_messaging_api_handler as target


def test_handle_text_message():
    path = "src/test/handler/input.json"
    with open(path) as f:
        event = json.load(f)

    event = MessageEvent()
    target.handle_text_message(event)
