import json
import traceback
from linebot.v3.messaging.models.message import Message
from linebot.v3.webhooks.models.image_message_content import ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
# from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
# from src.app.model.usecase_model import ReceiptResult

MESSAGE_JSON_PATH = "resource/message.json"


class HundleLineMessageUsecase:
    messages = {}

    def __init__(self):
        with open(MESSAGE_JSON_PATH, "r") as f:
            self.messages = json.load(f)

    def to_message(function):
        def _wrapper(*args, **keywords):
            self = args[0]
            try:
                messages = function(*args, **keywords)
                if messages is None:
                    messages = self.messages.get("[message_not_found_error]")
            except Exception as e:
                messages = self.messages.get("[unknown_error]")
                messages[2]["text"] = messages[2]["text"].replace("{error}", str(e))
                traceback.print_exc()
            return [Message.from_dict(m) for m in messages]

        return _wrapper

    @to_message
    def group_message(self) -> list[Message]:
        return self.messages.get("[group_error]")

    @to_message
    def handle_text_message(
        self, message: TextMessageContent, user_id: str
    ) -> list[Message]:
        return self.messages.get(message.text)

    @to_message
    def handle_image_message(
        self, message: ImageMessageContent, user_id: str
    ) -> list[Message]:
        if message.image_set is not None and message.image_set.id is not None:
            return self.messages["[image_set_error]"]

        # result: ReceiptResult = analyze_receipt(message.content)
        # if result is not None:
        #     return self.messages["[success]"]
        return self.messages["[image]"]

    @to_message
    def handle_default_event(self) -> list[Message]:
        return self.messages.get("[message_not_found_error]")


# def register_expenditure():
#     file_path = "/Users/takakuwashun/app/python/3.12.2/household-account-book/src/app/adaptor/test_receipt.png"
#     with open(file_path, "rb") as image_file:
#       data = image_file.read()

#     result: ReceiptResult = analyze_receipt(data)
#     print(result)
