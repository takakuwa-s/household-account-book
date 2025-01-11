import datetime
import json
from linebot.v3.messaging.models.text_message import TextMessage
from src.app.model import (
    db_model as db,
    usecase_model as uc,
)

MESSAGE_JSON_PATH = "resource/message.json"


class MessageRepository:
    message_pool = {}

    def __init__(self):
        with open(MESSAGE_JSON_PATH, "r") as f:
            self.message_pool = json.load(f)

    def get_message(self, key: str) -> str:
        message = self.message_pool.get(key)
        if message is None:
            message = self.message_pool.get("[message_not_found_error]")
        return message

    def get_error_message(self, e: Exception) -> str:
        messages = self.get_message("[unknown_error]")
        messages[2]["text"] = messages[2]["text"].replace("{error}", str(e))
        return messages

    def get_follow_message(self, user_name: str) -> str:
        messages = self.get_message("[follow]")
        messages[0]["text"] = f"{user_name}さんフォローありがとうございます！"
        return messages

    def get_register_user_message(self, user_name: str, line_name: str) -> str:
        messages = self.get_message("[register_user]")
        messages[0]["text"] = (
            f"「{user_name}」を{line_name}さんのスプレッドシートでの名前として、ユーザー登録が完了しました！"
        )
        return messages

    def get_reciept_confirm_message(self, record: db.TemporalExpenditure) -> list[dict]:
        """
        家計簿登録確認メッセージを作成します。
        Args:
            record (db.TemporalExpenditure): 仮の家計簿レコード
        Returns:
            list[dict]: 家計簿登録確認メッセージ
        """

        if record.status == db.TemporalExpenditure.Status.INVALID_IMAGE:
            return self.get_message("[not_receipt_error]")

        response = self.get_message("[confirm_expenditure]")
        response.extend(self.__create_update_expenditure_items_menu(record))
        return response

    def get_complete_reciept_analysis_message(
        self, record: db.TemporalExpenditure
    ) -> list[dict]:
        """
        レシート解析完了メッセージを作成します。
        Args:
            record (db.TemporalExpenditure): 仮の家計簿レコード
        Returns:
            list[dict]: レシート解析完了メッセージ
        """

        if record.status == db.TemporalExpenditure.Status.INVALID_IMAGE:
            return self.get_message("[reciept_analysis_failed]")
        response = self.get_message("[reciept_analysis_complete]")
        response.extend(self.__create_update_expenditure_items_menu(record))
        return response

    def __create_update_expenditure_items_menu(
        self, record: db.TemporalExpenditure
    ) -> list[dict]:
        contents = []
        if record.status == db.TemporalExpenditure.Status.ANALYZING:
            # 更新ボタンの設定
            contents.append(
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "postback",
                        "label": "解析ステータス更新",
                        "data": (
                            uc.RegisterExpenditurePostback(
                                id=record.id,
                                type=uc.PostbackEventTypeEnum.RELOAD_STATUS,
                            ).model_dump_json()
                        ),
                        "displayText": "レシート解析ステータスを更新します",
                    },
                }
            )
        elif record.status == db.TemporalExpenditure.Status.ANALYZED:
            if len(record.data.items) > 0:
                # 登録ボタンの設定
                contents.append(
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "postback",
                            "label": "詳細項目含めて登録",
                            "data": uc.RegisterExpenditurePostback(
                                id=record.id
                            ).model_dump_json(),
                            "displayText": "家計簿に詳細項目を全て含め、登録します",
                        },
                    }
                )
            if record.data.total is not None:
                # 合計金額のみ登録ボタンの設定
                contents.append(
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "合計金額のみ登録",
                            "data": uc.RegisterExpenditurePostback(
                                id=record.id,
                                type=uc.PostbackEventTypeEnum.REGISTER_ONLY_TOTAL,
                            ).model_dump_json(),
                            "displayText": "家計簿に合計金額のみを登録します",
                        },
                    }
                )

        # 項目変更ボタンの設定
        contents.append(
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "項目変更",
                    "data": uc.RegisterExpenditurePostback(
                        id=record.id,
                        type=uc.PostbackEventTypeEnum.CHANGE_CLASSIFICATION,
                    ).model_dump_json(),
                    "displayText": "大項目・小項目を変更します",
                },
            }
        )

        # 誰向け変更ボタンの設定
        contents.append(
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "誰向け変更",
                    "data": uc.RegisterExpenditurePostback(
                        id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_FOR_WHOM
                    ).model_dump_json(),
                    "displayText": "誰向けの支払いかを変更します",
                },
            }
        )

        # 支払い者変更ボタンの設定
        contents.append(
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "支払い者変更",
                    "data": uc.RegisterExpenditurePostback(
                        id=record.id, type=uc.PostbackEventTypeEnum.CHANGE_PAYER
                    ).model_dump_json(),
                    "displayText": "支払い者を変更します",
                },
            }
        )

        # 支払い方法変更ボタンの設定
        contents.append(
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "支払い方法変更",
                    "data": uc.RegisterExpenditurePostback(
                        id=record.id,
                        type=uc.PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD,
                    ).model_dump_json(),
                    "displayText": "支払い方法を変更します",
                },
            }
        )

        if record.status == db.TemporalExpenditure.Status.ANALYZED:
            # 日付変更ボタンの設定
            contents.append(
                {
                    "type": "button",
                    "action": {
                        "type": "datetimepicker",
                        "label": "日付修正",
                        "data": uc.RegisterExpenditurePostback(
                            id=record.id, type=uc.PostbackEventTypeEnum.UPDATE_DATE
                        ).model_dump_json(),
                        "mode": "date",
                        "initial": record.data.date,
                        "max": datetime.date.today().isoformat(),
                        "min": "2020-01-01",
                    },
                }
            )

        # キャンセルボタンの設定
        contents.append(
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "キャンセル",
                    "data": (
                        uc.RegisterExpenditurePostback(
                            id=record.id, type=uc.PostbackEventTypeEnum.CANCEL
                        ).model_dump_json()
                    ),
                    "displayText": "家計簿登録をキャンセルします",
                },
            }
        )
        msg3: list[dict] = self.get_message("[update_expenditure_items_menu]")
        msg3[0]["contents"]["footer"]["contents"] = contents

        msg1 = TextMessage(text=record.data.get_common_info()).to_dict()
        if record.status == db.TemporalExpenditure.Status.ANALYZED:
            msg2 = TextMessage(text=record.data.get_receipt_info()).to_dict()
        else:
            msg2 = TextMessage(
                text="レシート解析中です。しばらくお待ちください。"
            ).to_dict()

        return [msg1, msg2, msg3[0]]

    def get_change_classification_message(
        self,
        data: uc.RegisterExpenditurePostback,
        classification_map: dict[str, list[db.ItemClassification]],
    ) -> list[dict]:
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
        response = self.get_message("[change_classification]")
        response[0]["contents"]["contents"] = contents
        return response

    def get_change_for_whom_message(
        self, data: uc.RegisterExpenditurePostback, users: list[db.User]
    ) -> list[dict]:
        contents = []
        for user in users:
            if user.name == "":
                continue
            contents.append(
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": f"{user.name}に変更",
                        "data": (
                            uc.RegisterExpenditurePostback(
                                id=data.id,
                                type=uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM,
                                updated_item=user.name,
                            ).model_dump_json()
                        ),
                        "displayText": f"誰向けの支払いかを{user.name}に変更します",
                    },
                }
            )
            contents.append(
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "共通に変更",
                        "data": (
                            uc.RegisterExpenditurePostback(
                                id=data.id,
                                type=uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM,
                                updated_item="共通",
                            ).model_dump_json()
                        ),
                        "displayText": "誰向けの支払いかを共通に変更します",
                    },
                }
            )
        response = self.get_message("[change_for_whom]")
        response[0]["contents"]["footer"]["contents"] = contents
        return response

    def get_change_payer_message(
        self, data: uc.RegisterExpenditurePostback, users: list[db.User]
    ) -> list[dict]:
        contents = []
        for user in users:
            if user.name == "":
                continue
            contents.append(
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": f"{user.name}に変更",
                        "data": (
                            uc.RegisterExpenditurePostback(
                                id=data.id,
                                type=uc.PostbackEventTypeEnum.UPDATE_PAYER,
                                updated_item=user.name,
                            ).model_dump_json()
                        ),
                        "displayText": f"支払い者を{user.name}に変更します",
                    },
                }
            )
        if len(contents) > 0:
            response = self.get_message("[change_payer]")
            response[0]["contents"]["footer"]["contents"] = contents
        else:
            response = self.get_message("[no_user_error]")
        return response

    def get_change_payment_method_message(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        response = self.get_message("[change_payment_method]")
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
