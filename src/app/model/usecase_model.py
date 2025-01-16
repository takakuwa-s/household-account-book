from enum import Enum
from typing import Optional
from pydantic import Field

from src.app.model.common_model import CommonModel


class KeywordsEnum(str, Enum):
    REGISTER_USER = "ユーザー登録"
    GET_TEMPORALLY_EXPENDITURES = "登録途中のレシート一覧"
    REGISTER_COMMON_FOOD = "共用の食費で使ったレシート登録"
    REGISTER_COMMON_DAILY_NECESSALITIES = "共用の日用品で使ったレシート登録"
    REGISTER_MY_DAILY_NECESSALITIES = "私用の日用品で使ったレシート登録"
    REGISTER_COMMON_FURNITURES = "共用の家具・家電で使ったレシート登録"
    REGISTER_COMMON_ALCOHOL = "共用の家飲みで使ったレシート登録"
    REGISTER_MY_FASHION = "私用のファッションで使ったレシート登録"
    REGISTER_MY_BEAUTY = "私用の美容費で使ったレシート登録"
    REGISTER_MY_SNACK = "私用のおやつで使ったレシート登録"
    REGISTER_COMMON_ENTERTAINMENT = "共用の交際費で使ったレシート登録"
    REGISTER_COMMON_EATING_OUT = "共用の外食費で使ったレシート登録"
    CANCEL = "キャンセル"

    @staticmethod
    def is_for_register_receipt(keyword: str) -> bool:
        """
        レシート登録に関連するキーワードかどうかを判定します。
        Args:
            keyword: キーワード
        Returns:
            当てはまる場合はTrue
        """
        return keyword in [
            KeywordsEnum.REGISTER_COMMON_FOOD.value,
            KeywordsEnum.REGISTER_COMMON_DAILY_NECESSALITIES.value,
            KeywordsEnum.REGISTER_MY_DAILY_NECESSALITIES.value,
            KeywordsEnum.REGISTER_COMMON_FURNITURES.value,
            KeywordsEnum.REGISTER_COMMON_ALCOHOL.value,
            KeywordsEnum.REGISTER_MY_FASHION.value,
            KeywordsEnum.REGISTER_MY_BEAUTY.value,
            KeywordsEnum.REGISTER_MY_SNACK.value,
            KeywordsEnum.REGISTER_COMMON_ENTERTAINMENT.value,
            KeywordsEnum.REGISTER_COMMON_EATING_OUT.value,
        ]

    @staticmethod
    def get_setting_from_keyword(keyword: str) -> tuple[str, str, str]:
        """
        キーワードに対応する設定を取得します。
        Args:
            keyword: キーワード
        Returns:
            大項目, 小項目, 共通かどうかの設定
        """
        match keyword:
            case KeywordsEnum.REGISTER_COMMON_FOOD.value:
                return "生活費", "食費", True
            case KeywordsEnum.REGISTER_COMMON_DAILY_NECESSALITIES.value:
                return "生活費", "日用品", True
            case KeywordsEnum.REGISTER_MY_DAILY_NECESSALITIES.value:
                return "生活費", "日用品", False
            case KeywordsEnum.REGISTER_COMMON_FURNITURES.value:
                return "生活費", "家具・家電", True
            case KeywordsEnum.REGISTER_COMMON_ALCOHOL.value:
                return "娯楽", "家飲み", True
            case KeywordsEnum.REGISTER_MY_FASHION.value:
                return "生活費", "ファッション", False
            case KeywordsEnum.REGISTER_MY_BEAUTY.value:
                return "生活費", "美容費", True
            case KeywordsEnum.REGISTER_MY_SNACK.value:
                return "娯楽", "おやつ", False
            case KeywordsEnum.REGISTER_COMMON_ENTERTAINMENT.value:
                return "娯楽", "交際費", True
            case KeywordsEnum.REGISTER_COMMON_EATING_OUT.value:
                return "娯楽", "外食費", True
            case _:
                return "", "", True


class PaymentMethodEnum(str, Enum):
    ADVANCE_PAYMENT = "建て替え"
    FAMILY_CARD = "家族カード"

    @classmethod
    def value_of(cls, key_name: str) -> "PaymentMethodEnum":
        for name, enum in cls.__members__.items():
            if key_name == name:
                return enum
        else:
            raise ValueError(f"'{key_name}' enum not found")


class ReceiptResult(CommonModel):
    class Item(CommonModel):
        price: int = Field(default=0)
        name: str = Field(default="")
        remarks: str = Field(default="LINE経由。")

    items: list[Item] = Field(default=[])
    total: Optional[int] = Field(default=None)
    date: str = Field(default="")
    store: str = Field(default="")

    def set_total(self, total: Optional[float]):
        """
        合計金額を設定します。
        Args:
            total: 合計金額
        """
        if total is not None:
            total = int(total)
            self.total = total
            for item in self.items:
                item.remarks += f"合計{total}円"

    def append_tax(self, sum: int):
        """
        合計金額が設定されている場合、合計金額と各項目の和が一致するように、消費税を追加し調整します。
        Args:
            sum: 各項目の金額の和
        """
        if self.total is not None and self.total > sum:
            item = ReceiptResult.Item()
            item.name = "消費税"
            item.price = self.total - sum
            item.remarks += f"合計{self.total}円"
            self.items.append(item)

    def get_note(self) -> str:
        sum = 0
        for item in self.items:
            sum += item.price
        if self.total is None:
            return "※ 合計金額は読み取れませんでした"
        elif len(self.items) == 0:
            return "※ レシートの各種詳細項目は読み取れませんでした"
        elif sum != self.total:
            return f"※ 合計と各項目の和が一致しません。各項目の和: {sum}円"
        return ""


class AccountBookInput(ReceiptResult):
    major_classification: str = Field(default="生活費")
    minor_classification: str = Field(default="食費")
    payer: str = Field(default="")
    for_whom: str = Field(default="共通")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.ADVANCE_PAYMENT)

    @staticmethod
    def from_another(another: "AccountBookInput") -> "AccountBookInput":
        """
        他の家計簿登録情報をコピーします。
        Args:
            another: コピー元の家計簿登録情報
        Returns:
            コピー後の家計簿登録情報
        """
        return AccountBookInput(
            items=another.items,
            total=another.total,
            date=another.date,
            store=another.store,
            major_classification=another.major_classification,
            minor_classification=another.minor_classification,
            payer=another.payer,
            for_whom=another.for_whom,
            payment_method=another.payment_method,
        )

    def get_common_info(self) -> str:
        """
        家計簿登録の基本情報を文字列に変換します。
        Returns:
            家計簿登録基本情報の文字列
        """
        return (
            "【共通情報】\n"
            f"大項目: {self.major_classification}\n"
            f"小項目: {self.minor_classification}\n"
            f"支払い者: {self.payer}\n"
            f"誰向け: {self.for_whom}\n"
            f"支払い方法: {self.payment_method.value}"
        )

    def get_receipt_info(self) -> str:
        """
        家計簿登録用のレシートの情報を文字列に変換します。
        Returns:
            家計簿登録用のレシートの情報の文字列
        """
        result = ""
        result += (
            f"【レシート解析結果】\n"
            f"日付: {self.date}\n"
            f"合計: {self.total}円\n"
            f"店名: {self.store}\n"
            "\n---詳細情報---\n"
        )
        sum = 0
        for item in self.items:
            sum += item.price
            result += f"・{item.name}: {item.price}円\n"
        note = self.get_note()
        if note:
            result += "\n" + note
        return result


class PostbackEventTypeEnum(str, Enum):
    CANCEL_USER_REGISTRATION = "cancel_user_registration"

    REGISTER_EXPENDITURE = "register_expenditure"
    REGISTER_ONLY_TOTAL = "register_only_total"
    DETAIL_EXPENDITURE = "detail_expenditure"
    CHANGE_CLASSIFICATION = "change_classification"
    UPDATE_CLASSIFICATION = "update_classification"
    CHANGE_FOR_WHOM = "change_for_whom"
    UPDATE_FOR_WHOM = "update_for_whom"
    CHANGE_PAYER = "change_payer"
    UPDATE_PAYER = "update_payer"
    UPDATE_DATE = "update_date"
    CHANGE_PAYMENT_METHOD = "change_payment_method"
    UPDATE_PAYMENT_METHOD = "update_payment_method"
    DELETE_UNREGISTEED_EXPENDITURE = "delete_unregisterrd_expenditure"

    @staticmethod
    def is_for_receipt_registration(type: str) -> bool:
        """
        レシート登録に関連するイベントかどうかを判定します。
        Args:
            type: イベントの種類
        Returns:
            レシート登録に関連するイベントの場合はTrue
        """
        return type in [
            PostbackEventTypeEnum.REGISTER_EXPENDITURE,
            PostbackEventTypeEnum.REGISTER_ONLY_TOTAL,
            PostbackEventTypeEnum.DETAIL_EXPENDITURE,
            PostbackEventTypeEnum.CHANGE_CLASSIFICATION,
            PostbackEventTypeEnum.UPDATE_CLASSIFICATION,
            PostbackEventTypeEnum.CHANGE_FOR_WHOM,
            PostbackEventTypeEnum.UPDATE_FOR_WHOM,
            PostbackEventTypeEnum.CHANGE_PAYER,
            PostbackEventTypeEnum.UPDATE_PAYER,
            PostbackEventTypeEnum.UPDATE_DATE,
            PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD,
            PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD,
            PostbackEventTypeEnum.DELETE_UNREGISTEED_EXPENDITURE,
        ]


class RegisterExpenditurePostback(CommonModel):
    type: PostbackEventTypeEnum = Field(
        default=PostbackEventTypeEnum.REGISTER_EXPENDITURE
    )
    id: str = Field(default="")
    updated_item: Optional[str] = Field(default=None)


class CancelUserRegistrationPostback(CommonModel):
    type: PostbackEventTypeEnum = Field(
        default=PostbackEventTypeEnum.CANCEL_USER_REGISTRATION
    )
