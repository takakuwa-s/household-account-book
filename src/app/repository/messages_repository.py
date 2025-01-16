import datetime
import json
from src.app.model import (
    db_model as db,
    usecase_model as uc,
)

MESSAGE_JSON_PATH = "resource/message.json"


class MessagesRepository:
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

    def get_start_user_registration_message(self) -> str:
        messages = self.get_message("[start_user_registration]")
        messages[0]["quickReply"]["items"][0]["action"]["data"] = (
            uc.CancelUserRegistrationPostback().model_dump_json()
        )
        return messages

    def get_register_user_message(self, user_name: str, line_name: str) -> str:
        messages = self.get_message("[register_user]")
        messages[0]["text"] = (
            f"「{user_name}」を{line_name}さんのスプレッドシートでの名前として、ユーザー登録が完了しました！"
        )
        return messages

    def get_temporal_expenditure_list(
        self, records: list[db.TemporalExpenditure]
    ) -> list[dict]:
        """
        仮の家計簿リストメッセージを作成します。
        Args:
            records (list[db.TemporalExpenditure]): 仮の家計簿レコードリスト
        Returns:
            list[dict]: 仮の家計簿リストメッセージ
        """
        if len(records) == 0:
            return self.get_message("[no_temporal_expenditure]")
        contents = []
        for idx, record in enumerate(records):
            buttons = []

            # ステータスごとに処理
            match record.status:
                case db.TemporalExpenditure.Status.NEW:
                    table_contents_data = [("ステータス", "レシート受付待")]
                case db.TemporalExpenditure.Status.ANALYZED:
                    note = record.data.get_note()
                    if not note:
                        note = "※ 特になし"
                    table_contents_data = [
                        ("ステータス", "解析済"),
                        ("日付", record.data.get("date", "不明")),
                        ("店名", record.data.get("store", "不明")),
                        ("合計", f"{record.data.get("total", "?")}円"),
                        (
                            "大項目",
                            record.data.get("major_classification", "不明"),
                        ),
                        (
                            "小項目",
                            record.data.get("minor_classification", "不明"),
                        ),
                        ("支払い者", record.data.get("payer", "不明")),
                        ("誰向け", record.data.get("for_whom", "不明")),
                        ("支払い方法", record.data.payment_method.value),
                        ("備考", note),
                    ]
                    # 登録ボタンの設定
                    buttons.append(self.__get_register_button(record.id))
                    # 合計金額のみ登録ボタンの設定
                    buttons.append(self.__get_register_only_total_button(record.id))
                    # 詳細表示ボタンの設定
                    buttons.append(self.__get_show_details_button(record.id, False))
                case db.TemporalExpenditure.Status.ANALYZING:
                    table_contents_data = [
                        ("ステータス", "解析中"),
                        (
                            "大項目",
                            record.data.get("major_classification", "不明"),
                        ),
                        (
                            "小項目",
                            record.data.get("minor_classification", "不明"),
                        ),
                        ("支払い者", record.data.get("payer", "不明")),
                        ("誰向け", record.data.get("for_whom", "不明")),
                        ("支払い方法", record.data.payment_method.value),
                    ]
                    # 詳細表示ボタンの設定
                    buttons.append(self.__get_show_details_button(record.id, False))
                case db.TemporalExpenditure.Status.INVALID_IMAGE:
                    table_contents_data = [("ステータス", "不正な画像")]
            # 破棄ボタンの設定
            buttons.append(self.__get_register_cancel_button(record.id))

            # ボディ部のテーブル作成
            table_contents = [
                {
                    "type": "text",
                    "text": f"レシート #{idx + 1}",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#555555",
                }
            ]
            for data in table_contents_data:
                table_contents.append(
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "md",
                        "contents": [
                            {"type": "text", "text": data[0]},
                            {"type": "text", "text": data[1], "wrap": True},
                        ],
                    }
                )
                table_contents.append({"type": "separator"})
            table_contents.pop()

            bubble = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": table_contents,
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": buttons,
                },
            }
            contents.append(bubble)
        response = self.get_message("[temporal_expenditure_list]")
        response[0]["contents"]["contents"] = contents
        return response

    def get_reciept_analysis_message(
        self,
        temporal_expenditure_id: str,
        status: db.TemporalExpenditure.Status,
        num_receipts: int = 0,
    ) -> list[dict]:
        """
        レシート解析完了メッセージを作成します。
        Args:
            temporal_expenditure_id (str): 仮の家計簿レコードのID
            status (db.TemporalExpenditure.Status): 仮の家計簿レコードのステータス
            num_receipts (int): 解析したレシートの数
        Returns:
            list[dict]: レシート解析完了メッセージ
        """
        items = [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "登録途中のレシート一覧",
                    "text": "登録途中のレシート一覧",
                },
            },
            {
                "type": "action",
                "action": self.__get_show_details_button(
                    temporal_expenditure_id, False, True
                ),
            },
        ]
        match status:
            case db.TemporalExpenditure.Status.ANALYZING:
                response = self.get_message("[reciept_analysis_started]")
            case db.TemporalExpenditure.Status.ANALYZED:
                response = self.get_message("[reciept_analysis_complete]")
                if num_receipts > 1:
                    response[0]["text"] = (
                        response[0]["text"]
                        + f"\n\n ※ 画像の中には{num_receipts}枚のレシートが含まれており、それらも登録途中のレシートとして保存しているます。「登録途中のレシート一覧」をタップして確認してみて下さい。"
                    )
            case db.TemporalExpenditure.Status.INVALID_IMAGE:
                response = self.get_message("[reciept_analysis_failed]")
        if status != db.TemporalExpenditure.Status.ANALYZED:
            items.append(
                {
                    "type": "action",
                    "action": self.__get_register_cancel_button(
                        temporal_expenditure_id, True
                    ),
                },
            )
        response[-1]["quickReply"] = {"items": items}
        return response

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

        contents = []
        if record.status == db.TemporalExpenditure.Status.ANALYZING:
            # 詳細表示ボタンの設定
            contents.append(self.__get_show_details_button(record.id, True))
        elif record.status == db.TemporalExpenditure.Status.ANALYZED:
            if len(record.data.items) > 0:
                # 登録ボタンの設定
                contents.append(self.__get_register_button(record.id))
            if record.data.total is not None:
                # 合計金額のみ登録ボタンの設定
                contents.append(self.__get_register_only_total_button(record.id))

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

        # 破棄ボタンの設定
        contents.append(self.__get_register_cancel_button(record.id))

        response = self.get_message("[confirm_expenditure]")
        response[1]["text"] = record.data.get_common_info()
        if record.status == db.TemporalExpenditure.Status.ANALYZED:
            response[2]["text"] = record.data.get_receipt_info()
        else:
            response[2]["text"] = "レシート解析中です。しばらくお待ちください。"
        response[3]["contents"]["footer"]["contents"] = contents
        return response

    def __get_show_details_button(
        self, id: str, for_reload: bool, only_action=False
    ) -> dict:
        """
        家計簿詳細表示ボタンを作成します。
        Args:
            id (str): 仮の家計簿レコードのID
        Returns:
            dict: 家計簿詳細表示ボタン
        """
        action = {
            "type": "postback",
            "label": "解析ステータス更新" if for_reload else "詳細表示",
            "data": (
                uc.RegisterExpenditurePostback(
                    id=id,
                    type=uc.PostbackEventTypeEnum.DETAIL_EXPENDITURE,
                ).model_dump_json()
            ),
            "displayText": "レシート解析ステータスを更新します"
            if for_reload
            else "登録レシート情報の詳細を表示します",
        }
        if only_action:
            return action
        return {
            "type": "button",
            "style": "primary" if for_reload else "link",
            "action": action,
        }

    def __get_register_button(self, id: str) -> dict:
        """
        家計簿登録ボタンを作成します。
        Args:
            id (str): 仮の家計簿レコードのID
        Returns:
            dict: 家計簿登録ボタン
        """
        return {
            "type": "button",
            "style": "primary",
            "action": {
                "type": "postback",
                "label": "詳細項目含めて登録",
                "data": uc.RegisterExpenditurePostback(id=id).model_dump_json(),
                "displayText": "家計簿に詳細項目を全て含め、登録します",
            },
        }

    def __get_register_only_total_button(self, id: str) -> dict:
        """
        合計のみの家計簿登録ボタンを作成します。
        Args:
            id (str): 仮の家計簿レコードのID
        Returns:
            dict: 合計のみの家計簿登録ボタン
        """
        return {
            "type": "button",
            "style": "secondary",
            "action": {
                "type": "postback",
                "label": "合計金額のみ登録",
                "data": uc.RegisterExpenditurePostback(
                    id=id,
                    type=uc.PostbackEventTypeEnum.REGISTER_ONLY_TOTAL,
                ).model_dump_json(),
                "displayText": "家計簿に合計金額のみを登録します",
            },
        }

    def __get_register_cancel_button(self, id: str, only_action=False) -> dict:
        """
        家計簿登録キャンセルボタンを作成します。
        Args:
            id (str): 仮の家計簿レコードのID
        Returns:
            dict: 家計簿登録キャンセルボタン
        """
        action = {
            "type": "postback",
            "label": "破棄",
            "data": (
                uc.RegisterExpenditurePostback(
                    id=id,
                    type=uc.PostbackEventTypeEnum.DELETE_UNREGISTEED_EXPENDITURE,
                ).model_dump_json()
            ),
            "displayText": "登録途中のレシートを破棄します",
        }
        if only_action:
            return action
        return {
            "type": "button",
            "action": action,
        }

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
