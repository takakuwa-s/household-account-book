from src.app.model.db_model import ItemClassification
from src.app.repository.base_table_repository import BaseTableRepository


class ItemClassificationsRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=ItemClassification)

    def get_major(self, minor: str) -> str:
        """
        マイナーからメジャーを取得します。
        Args:
            minor (str): マイナー
        Returns:
            str: メジャー
        """
        response: ItemClassification = self.get_item(minor)
        return response.major

    def get_all_major_to_minors_map(self) -> dict[str, list[ItemClassification]]:
        """
        全てのマイナーメジャー分類をメジャーをキーとしたdict形式で取得します。
        Returns:
            dict: アイテム分類
        """
        classifications: list[ItemClassification] = self.get_all()
        response = {}
        for classification in classifications:
            if classification.major in response:
                response[classification.major].append(classification)
            else:
                response[classification.major] = [classification]
        return response
