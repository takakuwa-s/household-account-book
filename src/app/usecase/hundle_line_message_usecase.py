import datetime
import json
import traceback
import boto3
from linebot.v3.messaging.models.message import Message
from linebot.v3.webhooks.models.image_message_content import ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_content import PostbackContent

from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.adaptor.google_sheets_api_adaptor import register_expenditure
from src.app.adaptor.line_messaging_api_adaptor import fetch_image
from src.app.model import (
    db_model as db,
    usecase_model as uc,
)
from src.app.repository.item_classification_table_repository import (
    ItemClassificationTableRepository,
)
from src.app.repository.temporal_expenditure_table_repository import (
    TemporalExpenditureTableRepository,
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
        self.temporal_expenditure_table_repository = TemporalExpenditureTableRepository(
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
        binary = fetch_image(message.id)
        print("lineからのイメージデータを取得しました。")
        result: list[uc.ReceiptResult] = analyze_receipt(binary)

        input: uc.AccountBookInput = uc.AccountBookInput(receipt_results=result)
        input.major_classification = (
            self.item_classification_table_repository.get_major(
                input.minor_classification
            )
        )
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.create_from_account_book_input(
                input
            )
        )
        return self.__create_confirm_response(record)

    def __create_confirm_response(self, record: db.TemporalExpenditure) -> list[dict]:
        """
        家計簿登録確認メッセージを作成します。
        Args:
            record (db.TemporalExpenditure): 仮の家計簿レコード
        Returns:
            list[dict]: 家計簿登録確認メッセージ
        """
        response = self.message_pool.get("[confirm_expenditure]")
        response[1]["text"] = record.data.get_common_info()
        response[2]["text"] = record.data.get_receipt_info()

        # 登録ボタンの設定
        response[3]["contents"]["footer"]["contents"][0]["action"]["data"] = (
            uc.RegisterExpenditurePostback(id=record.id).model_dump_json()
        )

        # 項目変更ボタンの設定
        response[3]["contents"]["footer"]["contents"][1]["action"]["data"] = (
            uc.RegisterExpenditurePostback(
                id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_CLASSIFICATION
            ).model_dump_json()
        )

        # 誰向け変更ボタンの設定
        response[3]["contents"]["footer"]["contents"][2]["action"]["data"] = (
            uc.RegisterExpenditurePostback(
                id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_FOR_WHOM
            ).model_dump_json()
        )

        # 支払い者変更ボタンの設定
        response[3]["contents"]["footer"]["contents"][3]["action"]["data"] = (
            uc.RegisterExpenditurePostback(
                id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_PAYER
            ).model_dump_json()
        )

        # 日付変更ボタンの設定
        datetimepicker_action = response[3]["contents"]["footer"]["contents"][4][
            "action"
        ]
        if (
            len(record.data.receipt_results) > 0
            and record.data.receipt_results[0].date is not None
        ):
            datetimepicker_action["initial"] = record.data.receipt_results[
                0
            ].date.isoformat()
        datetimepicker_action["max"] = datetime.date.today().isoformat()
        datetimepicker_action["data"] = uc.RegisterExpenditurePostback(
            id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_DATE
        ).model_dump_json()

        # 支払い方法変更ボタンの設定
        response[3]["contents"]["footer"]["contents"][5]["action"]["data"] = (
            uc.RegisterExpenditurePostback(
                id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD
            ).model_dump_json()
        )

        # キャンセルボタンの設定
        response[3]["contents"]["footer"]["contents"][6]["action"]["data"] = (
            uc.RegisterExpenditurePostback(
                id=record.id, type=uc.PostbackEventTypeEnum.CANCEL
            ).model_dump_json()
        )
        return response

    @to_message
    def handle_postback_event(self, postback: PostbackContent) -> list[Message]:
        data: dict = json.loads(postback.data)
        match data["type"]:
            case uc.PostbackEventTypeEnum.REGISTER_EXPENDITURE:
                return self.__register_expenditure(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.CHANGE_CLASSIFICATION:
                return self.__change_classification(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.UPDATE_CLASSIFICATION:
                return self.__update_classification(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.CHANGE_FOR_WHOM:
                return self.__change_for_whom(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM:
                return self.__update_for_whom(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.CHANGE_PAYER:
                return self.__change_payer(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.UPDATE_PAYER:
                return self.__update_payer(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.CHANGE_DATE:
                return self.__change_date(
                    uc.RegisterExpenditurePostback(**data), postback.params["date"]
                )
            case uc.PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD:
                return self.__change_payment_method(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD:
                return self.__update_payment_method(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.CANCEL:
                return self.__cancel_expenditure(uc.RegisterExpenditurePostback(**data))
            case _:
                return self.message_pool.get("[postback_error]")

    def __register_expenditure(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        register_expenditure(record.data)
        self.temporal_expenditure_table_repository.delete_item(data.id)
        response = self.message_pool.get("[register]")
        return response

    def __change_date(
        self, data: uc.RegisterExpenditurePostback, date_str: str
    ) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        date = datetime.date.fromisoformat(date_str)
        for receipt in record.data.receipt_results:
            receipt.date = date
        self.temporal_expenditure_table_repository.put_item(record.model_dump())
        return self.__create_confirm_response(record)

    def __change_classification(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        classification_map: dict[str, list[db.ItemClassification]] = (
            self.item_classification_table_repository.get_all_major_to_minors_map()
        )
        contents = []
        for major, items in classification_map.items():
            buttons = []
            for item in items:
                button = {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": item.minor,
                        "data": uc.RegisterExpenditurePostback(
                            id=data.id,
                            type=uc.PostbackEventTypeEnum.UPDATE_CLASSIFICATION,
                            updated_item=item.minor,
                        ).model_dump_json(),
                        "displayText": f"支払いの小項目を「{item.minor}」に変更します",
                    },
                }
                buttons.append(button)
            bubble = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"大項目: {major}",
                            "weight": "bold",
                            "size": "xl",
                            "color": items[0].color,
                        },
                        {
                            "type": "text",
                            "text": "下記から変更したい小項目を選択してください",
                            "wrap": True,
                        },
                    ],
                },
                "footer": {"type": "box", "layout": "vertical", "contents": buttons},
            }
            contents.append(bubble)
        response = self.message_pool.get("[change_classification]")
        response[0]["contents"]["contents"] = contents
        return response

    def __update_classification(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        record.data.minor_classification = data.updated_item
        record.data.major_classification = (
            self.item_classification_table_repository.get_major(
                record.data.minor_classification
            )
        )
        self.temporal_expenditure_table_repository.put_item(record.model_dump())
        return self.__create_confirm_response(record)

    def __change_for_whom(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        response = self.message_pool.get("[change_for_whom]")
        response[0]["template"]["actions"][0]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM,
            updated_item="くん",
        ).model_dump_json()
        response[0]["template"]["actions"][1]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM,
            updated_item="ちゃん",
        ).model_dump_json()
        response[0]["template"]["actions"][2]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM,
            updated_item="共通",
        ).model_dump_json()
        return response

    def __update_for_whom(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        record.data.for_whom = data.updated_item
        self.temporal_expenditure_table_repository.put_item(record.model_dump())
        return self.__create_confirm_response(record)

    def __change_payer(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        response = self.message_pool.get("[change_payer]")
        response[0]["template"]["actions"][0]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_PAYER,
            updated_item="くん",
        ).model_dump_json()
        response[0]["template"]["actions"][1]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_PAYER,
            updated_item="ちゃん",
        ).model_dump_json()
        return response

    def __update_payer(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        record.data.payer = data.updated_item
        self.temporal_expenditure_table_repository.put_item(record.model_dump())
        return self.__create_confirm_response(record)

    def __change_payment_method(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        response = self.message_pool.get("[change_payment_method]")
        response[0]["template"]["actions"][0]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD,
            updated_item=uc.PaymentMethodEnum.ADVANCE_PAYMENT.name,
        ).model_dump_json()
        response[0]["template"]["actions"][1]["data"] = uc.RegisterExpenditurePostback(
            id=data.id,
            type=uc.PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD,
            updated_item=uc.PaymentMethodEnum.FAMILY_CARD.name,
        ).model_dump_json()
        return response

    def __update_payment_method(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = (
            self.temporal_expenditure_table_repository.get_item(data.id)
        )
        if record is None:
            return self.message_pool.get("[not_found_expenditure_error]")
        record.data.payment_method = uc.PaymentMethodEnum.value_of(data.updated_item)
        self.temporal_expenditure_table_repository.put_item(record.model_dump())
        return self.__create_confirm_response(record)

    def __cancel_expenditure(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        self.temporal_expenditure_table_repository.delete_item(data.id)
        response = self.message_pool.get("[cancel]")
        return response

    @to_message
    def handle_default_event(self) -> list[Message]:
        return self.message_pool.get("[message_not_found_error]")
