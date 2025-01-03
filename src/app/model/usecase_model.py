import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PaymentMethodEnum(str, Enum):
    ADVANCE_PAYMENT = "建て替え"
    FAMILY_CARD = "家族カード"


class ReceiptResult(BaseModel):
    class Item(BaseModel):
        price: int = Field(default=0)
        name: str = Field(default="")
        remarks: str = Field(default="LINE経由。")

    items: List[Item] = Field(default=[])
    total: Optional[int] = Field(default=None)
    date: datetime.date = Field(default="")
    store: str = Field(default="")

    def set_total(self, total: Optional[int]):
        """
        合計金額を設定します。
        Args:
            total: 合計金額
        """
        self.total = total
        if total is not None:
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


class AccountBookInput(BaseModel):
    receipt_results: list[ReceiptResult] = Field(default=[])
    major_classification: str = Field(default="")
    minor_classification: str = Field(default="日用品")
    payer: str = Field(default="くん")
    for_whom: str = Field(default="共通")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.ADVANCE_PAYMENT)

    def to_string(self) -> str:
        """
        家計簿登録情報を文字列に変換します。
        Returns:
            家計簿登録情報の文字列
        """
        result = (
            "【共通情報】\n"
            f"大項目: {self.major_classification}\n"
            f"小項目: {self.minor_classification}\n"
            f"支払い者: {self.payer}\n"
            f"誰向け: {self.for_whom}\n"
            f"支払い方法: {self.payment_method.value}\n"
        )
        for idx, receipt in enumerate(self.receipt_results):
            result += (
                f"\n【{idx+1}枚目のレシート情報】\n"
                f"日付: {receipt.date}\n"
                f"合計: {receipt.total}円\n"
                f"店名: {receipt.store}\n"
                "---詳細情報---\n"
            )
            sum = 0
            for item in receipt.items:
                sum += item.price
                result += f"・{item.name}: {item.price}円\n"
            if receipt.total is not None and sum != receipt.total:
                result += f"※ 合計と各項目の和が一致しません。各項目の和: {sum}円\n"
        return result
