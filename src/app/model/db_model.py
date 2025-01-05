from enum import Enum
import time
import uuid
from pydantic import BaseModel, Field
from src.app.model import usecase_model as uc


def calculate_ttl_timestamp(delete_date: int = 30) -> int:
    """
    TTLのタイムスタンプを計算します。
    Args:
        delete_date (int): 何日後に削除するか
    Returns:
        int: TTLのタイムスタンプ
    """
    return int(time.time()) + 60 * 60 * 24 * delete_date


class BaseTable(BaseModel):
    @staticmethod
    def get_name() -> str:
        raise NotImplementedError

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        """
        パーティションキーを持つ場合は、(パーティションキー名, パーティションキーの種類, パーティションキーの型)のタプルを返す。
        パーティションキーが存在しない場合はNoneを返す
        """
        raise NotImplementedError

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        """
        ソートキーを持つ場合は、(ソートキー名, ソートキーの種類, ソートキーの型)のタプルを返す。
        ソートキーが存在しない場合はNoneを返す
        """
        raise NotImplementedError


class ItemClassification(BaseTable):
    minor: str = Field(default="")  # パーティションキー
    major: str = Field(default="")
    color: str = Field(default="")

    @staticmethod
    def get_name() -> str:
        return "item_classifications"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "minor", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None


class TemporalExpenditure(BaseTable):
    class Status(str, Enum):
        ANALYZING = "ANALYZING"
        ANALYZED = "ANALYZED"
        INVALID_IMAGE = "INVALID_IMAGE"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # パーティションキー
    line_image_id: str = Field(default="")
    status: Status = Field(default=Status.ANALYZING)
    data: uc.AccountBookInput = Field(default=uc.AccountBookInput())
    ttl_timestamp: int = Field(default_factory=calculate_ttl_timestamp)

    @staticmethod
    def get_name() -> str:
        return "temporal_expenditure"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None
