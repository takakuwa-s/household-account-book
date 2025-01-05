from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


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


class ReceiptResult(BaseModel):
    class Item(BaseModel):
        price: int = Field(default=0)
        name: str = Field(default="")
        remarks: str = Field(default="LINE経由。")

    items: list[Item] = Field(default=[])
    total: Optional[int] = Field(default=None)
    date: str = Field(default="")
    store: str = Field(default="")
    number_of_receipts: int = Field(default=0)

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


class AccountBookInput(ReceiptResult):
    major_classification: str = Field(default="生活費")
    minor_classification: str = Field(default="食費")
    payer: str = Field(default="くん")
    for_whom: str = Field(default="共通")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.ADVANCE_PAYMENT)

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
        if self.total is not None and sum != self.total:
            result += f"\n※ 合計と各項目の和が一致しません。各項目の和: {sum}円\n"
        if self.number_of_receipts > 1:
            result += (
                "\n※ 複数のレシートが画像に見られましたが、1枚のみ解析しています。\n"
            )
        return result


class PostbackEventTypeEnum(str, Enum):
    REGISTER_EXPENDITURE = "register_expenditure"
    RELOAD_STATUS = "reload_status"
    CHANGE_CLASSIFICATION = "change_classification"
    UPDATE_CLASSIFICATION = "update_classification"
    CHANGE_FOR_WHOM = "change_for_whom"
    UPDATE_FOR_WHOM = "update_for_whom"
    CHANGE_PAYER = "change_payer"
    UPDATE_PAYER = "update_payer"
    UPDATE_DATE = "update_date"
    CHANGE_PAYMENT_METHOD = "change_payment_method"
    UPDATE_PAYMENT_METHOD = "update_payment_method"
    CANCEL = "cancel"


class RegisterExpenditurePostback(BaseModel):
    type: PostbackEventTypeEnum = Field(
        default=PostbackEventTypeEnum.REGISTER_EXPENDITURE
    )
    id: str = Field(default="")
    updated_item: Optional[str] = Field(default=None)
