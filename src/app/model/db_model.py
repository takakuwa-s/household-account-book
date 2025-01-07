from enum import Enum
import time
import uuid
from pydantic import BaseModel, Field
from src.app.model import usecase_model as uc


def calculate_ttl_timestamp(delete_hour: int = 24, delete_date: int = 30) -> int:
    """
    TTLのタイムスタンプを計算します。
    Args:
        delete_date (int): 何日後に削除するか
        delete_hour (int): 何時間後に削除するか
    Returns:
        int: TTLのタイムスタンプ
    """
    return int(time.time()) + 60 * 60 * delete_hour * delete_date


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


class User(BaseTable):
    line_user_id: str = Field(default="")  # パーティションキー
    line_name: str = Field(default="")
    name: str = Field(default="")

    @staticmethod
    def get_name() -> str:
        return "user"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "line_user_id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None


class MessageSession(BaseTable):
    class SessionType(str, Enum):
        REGISTER_USER = "REGISTER_USER"

    line_user_id: str = Field(default="")  # パーティションキー
    session_type: SessionType = Field(default=SessionType.REGISTER_USER)

    # およそ14.4分後に削除される
    ttl_timestamp: int = Field(
        default_factory=lambda: calculate_ttl_timestamp(delete_hour=1, delete_date=1)
    )

    @staticmethod
    def get_name() -> str:
        return "message_session"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "line_user_id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None
