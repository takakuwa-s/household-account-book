from enum import Enum
import time
from typing import Optional
import uuid
from pydantic import Field
from src.app.model import usecase_model as uc
from src.app.model.common_model import CommonModel


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


class BaseTable(CommonModel):
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
        NEW = "NEW"
        ANALYZING = "ANALYZING"
        ANALYZED = "ANALYZED"
        INVALID_IMAGE = "INVALID_IMAGE"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # パーティションキー
    line_user_id: str = Field(default="")
    line_image_id: str = Field(default="")
    status: Status = Field(default=Status.NEW)
    data: uc.AccountBookInput = Field(default=uc.AccountBookInput())
    image_set_id: Optional[str] = Field(default=None)
    ttl_timestamp: int = Field(default_factory=calculate_ttl_timestamp)

    @staticmethod
    def get_name() -> str:
        return "temporal_expenditures"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None

    @staticmethod
    def from_another(another: "TemporalExpenditure") -> "TemporalExpenditure":
        """
        他の仮支出データをコピーします。
        Args:
            another: コピー元の仮支出データ
        Returns:
            コピー後の仮支出データ
        """
        return TemporalExpenditure(
            line_user_id=another.line_user_id,
            line_image_id=another.line_image_id,
            status=TemporalExpenditure.Status(another.status),
            data=uc.AccountBookInput.from_another(another.data),
            ttl_timestamp=another.ttl_timestamp,
        )


class User(BaseTable):
    line_user_id: str = Field(default="")  # パーティションキー
    line_name: str = Field(default="")
    name: str = Field(default="")

    @staticmethod
    def get_name() -> str:
        return "users"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "line_user_id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None


class MessageSession(BaseTable):
    class SessionType(str, Enum):
        REGISTER_USER = "REGISTER_USER"
        REGISTER_EXPENDITURE = "REGISTER_EXPENDITURE"

    line_user_id: str = Field(default="")  # パーティションキー
    type: SessionType = Field(default=SessionType.REGISTER_USER)
    temporal_expenditure_id: Optional[str] = Field(default=None)

    # およそ14.4分後に削除される
    ttl_timestamp: int = Field(
        default_factory=lambda: calculate_ttl_timestamp(delete_hour=1, delete_date=1)
    )

    @staticmethod
    def get_name() -> str:
        return "message_sessions"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "line_user_id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None


class ImageSet(BaseTable):
    class ImageMetaData(CommonModel):
        line_image_id: str = Field(default="")
        status: TemporalExpenditure.Status = Field(
            default=TemporalExpenditure.Status.ANALYZING
        )

    image_set_id: str = Field(default="")  # パーティションキー
    total: int = Field(default="")
    image_meta_data: list[ImageMetaData] = Field(default=[])

    # およそ14.4分後に削除される
    ttl_timestamp: int = Field(
        default_factory=lambda: calculate_ttl_timestamp(delete_hour=1, delete_date=1)
    )

    @staticmethod
    def get_name() -> str:
        return "image_sets"

    @staticmethod
    def get_parttion_key() -> tuple[str, str, str]:
        return "image_set_id", "HASH", "S"

    @staticmethod
    def get_sort_key() -> tuple[str, str, str]:
        return None

    def get_overall_status(self) -> TemporalExpenditure.Status:
        """
        全画像をまとめた解析ステータスを取得します。
        Returns:
            TemporalExpenditure.Status: 全体の解析ステータス
        """
        invalid_image_exists = False
        for image_meta_data in self.image_meta_data:
            if image_meta_data.status == TemporalExpenditure.Status.ANALYZING:
                return TemporalExpenditure.Status.ANALYZING
            elif image_meta_data.status == TemporalExpenditure.Status.INVALID_IMAGE:
                invalid_image_exists = True
        if invalid_image_exists:
            return TemporalExpenditure.Status.INVALID_IMAGE
        else:
            return TemporalExpenditure.Status.ANALYZED
