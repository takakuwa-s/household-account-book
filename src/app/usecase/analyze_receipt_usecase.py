import traceback
import boto3
from linebot.v3.messaging.models.message import Message
from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.adaptor.line_messaging_api_adaptor import fetch_image, push_message
from src.app.model.usecase_model import ReceiptResult
from src.app.model.db_model import TemporalExpenditure
from src.app.repository.temporal_expenditure_repository import (
    TemporalExpenditureRepository,
)
from src.app.repository.message_repository import (
    MessageRepository,
)

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


class AnalyzeReceiptUsecase:
    def __init__(self):
        self.temporal_expenditure_table_repository = TemporalExpenditureRepository(
            dynamodb
        )
        self.message_repository = MessageRepository()

    def execute(self, id: str) -> bool:
        """
        レシートを解析します。
        Args:
            id (str): 仮支出データのID
        Returns:
            bool: 解析が完了したかどうか
        """
        print(f"レシート解析を開始します。id = {id}")
        try:
            # 1. 仮支出データを取得
            record: TemporalExpenditure = (
                self.temporal_expenditure_table_repository.get_item(id)
            )
            if record is None:
                print(f"仮支出データが見つかりません。id = {id}")
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

            # 5. 通知メッセージを取得
            message_dicts: list[dict] = (
                self.message_repository.get_complete_reciept_analysis_message(record)
            )
            message = [Message.from_dict(m) for m in message_dicts]

            # 6. 通知メッセージを送信
            push_message(record.line_user_id, message)
            print(f"全てのレシート解析処理が完了しました。id = {id}")
        except Exception:
            print(f"レシート解析処理に失敗しました。id = {id}")
            traceback.print_exc()
            return False
        return True
