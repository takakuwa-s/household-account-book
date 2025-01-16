from src.app.model.db_model import ImageSet, TemporalExpenditure
from src.app.repository.base_table_repository import BaseTableRepository


class ImageSetsRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=ImageSet)

    def update_image_meta_data_status(
        self, image_set_id: str, line_image_id: str, status: TemporalExpenditure.Status
    ) -> ImageSet:
        """
        画像メタデータのステータスを更新します。
        Args:
            image_set_id (str): 画像セットID
            line_image_id (str): LINE画像ID
            status (str): ステータス
        """
        # 画像セットを取得
        image_set: ImageSet = self.get_item(image_set_id)
        if image_set is None:
            return

        # 画像メタデータを更新
        for image_meta_data in image_set.image_meta_data:
            if image_meta_data.line_image_id == line_image_id:
                image_meta_data.status = status
                break

        # 画像セットを更新
        self.put_item(image_set.model_dump())
        return image_set
