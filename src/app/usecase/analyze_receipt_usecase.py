import traceback
import boto3
from linebot.v3.messaging.models.message import Message
from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.adaptor.line_messaging_api_adaptor import fetch_image, push_message
from src.app.config.logger import LogContext, get_app_logger
from src.app.model.usecase_model import ReceiptResult
from src.app.model.db_model import ImageSet, TemporalExpenditure
from src.app.repository.image_sets_repository import ImageSetsRepository
from src.app.repository.temporal_expenditures_repository import (
    TemporalExpendituresRepository,
)
from src.app.repository.messages_repository import (
    MessagesRepository,
)

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


class AnalyzeReceiptUsecase:
    def __init__(self):
        self.temporal_expenditure_table_repository = TemporalExpendituresRepository(
            dynamodb
        )
        self.image_sets_repository = ImageSetsRepository(dynamodb)
        self.message_repository = MessagesRepository()
        self.logger = get_app_logger(__name__)

    def execute(self, id: str) -> bool:
        """
        レシートを解析します。
        Args:
            id (str): 仮支出データのID
        Returns:
            bool: 解析が完了したかどうか
        """
        LogContext.set(temporal_expenditure_id=id)
        self.logger.info(f"レシート解析を開始します。id = {id}")
        try:
            # 1. 仮支出データを取得
            record: TemporalExpenditure = (
                self.temporal_expenditure_table_repository.get_item(id)
            )
            if record is None:
                self.logger.info("仮支出データが見つかりません")
                return True

            # 2. レシート画像を取得
            binary = fetch_image(record.line_image_id)

            # 3. レシートを解析
            result: list[ReceiptResult] = analyze_receipt(binary)

            # 4. 解析結果を保存
            if result is None:
                record = (
                    self.temporal_expenditure_table_repository.update_analysis_failure(
                        id
                    )
                )
            else:
                record = (
                    self.temporal_expenditure_table_repository.update_analysis_success(
                        id, result[0]
                    )
                )
                if len(result) > 1:
                    new_records: list[TemporalExpenditure] = []
                    for r in result[1:]:
                        new_record: TemporalExpenditure = (
                            TemporalExpenditure.from_another(record)
                        )
                        new_record.data.items = r.items
                        new_record.data.total = r.total
                        new_record.data.date = r.date
                        new_record.data.store = r.store
                        new_records.append(new_record)
                    self.temporal_expenditure_table_repository.batch_write_items(
                        new_records
                    )

            # 5. 画像が複数枚連携されているかを確認
            if record.image_set_id is None:
                status = record.status
            else:
                status = (
                    TemporalExpenditure.Status.INVALID_IMAGE
                    if result is None
                    else TemporalExpenditure.Status.ANALYZED
                )
                image_set: ImageSet = (
                    self.image_sets_repository.update_image_meta_data_status(
                        record.image_set_id, record.line_image_id, status
                    )
                )
                status = image_set.get_overall_status()
                if status == TemporalExpenditure.Status.ANALYZING:
                    self.logger.info(
                        f"画像が複数枚連携されているため、通知せずに処理を終了します。id = {id}"
                    )
                    return
                self.image_sets_repository.delete_item(record.image_set_id)

            # 6. 通知メッセージを取得
            message_dicts: list[dict] = (
                self.message_repository.get_reciept_analysis_message(
                    record.id, status, len(result)
                )
            )
            message = [Message.from_dict(m) for m in message_dicts]

            # 7. 通知メッセージを送信
            push_message(record.line_user_id, message)
            self.logger.info(f"全てのレシート解析処理が完了しました。id = {id}")

        except Exception:
            self.logger.info(f"レシート解析処理に失敗しました。id = {id}")
            traceback.print_exc()
            return False
        return True
