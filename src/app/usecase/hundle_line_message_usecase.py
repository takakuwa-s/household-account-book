import json
import traceback
import boto3
from linebot.v3.messaging.models.message import Message
from linebot.v3.webhooks.models.image_message_content import ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent

from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.adaptor.google_sheets_api_adaptor import register_expenditure
from src.app.adaptor.line_messaging_api_adaptor import fetch_image
from src.app.model import (
    db_model as db,
    usecase_model as usecase,
)
from src.app.repository.item_classification_table_repository import (
    ItemClassificationTableRepository,
)

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
MESSAGE_JSON_PATH = "resource/message.json"


class HundleLineMessageUsecase:
    message_pool = {}

    def __init__(self):
        self.item_classification_table_repository = ItemClassificationTableRepository(
            dynamodb
        )
        with open(MESSAGE_JSON_PATH, "r") as f:
            self.message_pool = json.load(f)

    def to_message(function):
        def _wrapper(*args, **keywords):
            self = args[0]
            try:
                messages = function(*args, **keywords)
                if messages is None:
                    messages = self.message_pool.get("[message_not_found_error]")
            except Exception as e:
                messages = self.message_pool.get("[unknown_error]")
                messages[2]["text"] = messages[2]["text"].replace("{error}", str(e))
                traceback.print_exc()
            return [Message.from_dict(m) for m in messages]

        return _wrapper

    @to_message
    def group_message(self) -> list[Message]:
        return self.message_pool.get("[group_error]")

    @to_message
    def handle_text_message(
        self, message: TextMessageContent, user_id: str
    ) -> list[Message]:
        return self.message_pool.get(message.text)

    @to_message
    def handle_image_message(
        self, message: ImageMessageContent, user_id: str
    ) -> list[Message]:
        if message.image_set is not None and message.image_set.id is not None:
            return self.message_pool["[image_set_error]"]
        data = fetch_image(message.id)
        print("lineからのイメージデータを取得しました。")
        result: usecase.ReceiptResult = analyze_receipt(data)

        input: usecase.AccountBookInput = usecase.AccountBookInput()
        input.receipt_results = result

        classification: db.ItemClassification = (
            self.item_classification_table_repository.get_item(
                input.minor_classification
            )
        )
        input.major_classification = classification.major
        print("dynamo dbがらデータを取得しました")

        register_expenditure(input)
        response_messages = self.message_pool.get("[image]")
        response_messages[1]["text"] = response_messages[1]["text"].replace(
            "{result}", input.to_string()
        )
        return response_messages

    @to_message
    def handle_default_event(self) -> list[Message]:
        return self.message_pool.get("[message_not_found_error]")


def test():
    file_path = "/Users/takakuwashun/app/python/3.12.2/household-account-book/src/app/adaptor/test_receipt.png"
    with open(file_path, "rb") as image_file:
        data = image_file.read()

    results: list[usecase.ReceiptResult] = analyze_receipt(data)
    input: usecase.AccountBookInput = usecase.AccountBookInput()
    input.receipt_results = results

    classification: db.ItemClassification = ItemClassificationTableRepository(
        dynamodb
    ).get_item(input.minor_classification)
    input.major_classification = classification.major
    print("dynamo dbがらデータを取得しました")

    print(input.to_string())
    register_expenditure(input)
