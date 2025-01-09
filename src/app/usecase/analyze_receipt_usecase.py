import traceback
import boto3
from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.adaptor.line_messaging_api_adaptor import fetch_image
from src.app.model.usecase_model import ReceiptResult
from src.app.model.db_model import TemporalExpenditure, calculate_ttl_timestamp
from src.app.repository.temporal_expenditure_repository import (
    TemporalExpenditureRepository,
)

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


class AnalyzeReceiptUsecase:
    def __init__(self):
        self.temporal_expenditure_table_repository = TemporalExpenditureRepository(
            dynamodb
        )

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
            result: ReceiptResult = analyze_receipt(binary)

            # 4. 解析結果を保存
            if result is None:
                ttl = calculate_ttl_timestamp(delete_date=1)
                self.temporal_expenditure_table_repository.update_item(
                    update_expression="SET #status = :updated_status, #ttl_timestamp = :updated_ttl_timestamp",
                    expression_attribute_names={
                        "#status": "status",
                        "#ttl_timestamp": "ttl_timestamp",
                    },
                    expression_attribute_values={
                        ":updated_status": TemporalExpenditure.Status.INVALID_IMAGE,
                        ":updated_ttl_timestamp": ttl,
                    },
                    partition_key_value=id,
                )
            else:
                items = [i.model_dump() for i in result.items]
                self.temporal_expenditure_table_repository.update_item(
                    update_expression="SET #status = :updated_status, #data.#total = :updated_total, #data.#date = :updated_date, #data.#store = :updated_store, #data.#number_of_receipts = :updated_number_of_receipts, #data.#items = :updated_items",
                    expression_attribute_names={
                        "#status": "status",
                        "#data": "data",
                        "#total": "total",
                        "#date": "date",
                        "#store": "store",
                        "#number_of_receipts": "number_of_receipts",
                        "#items": "items",
                    },
                    expression_attribute_values={
                        ":updated_status": TemporalExpenditure.Status.ANALYZED,
                        ":updated_total": result.total,
                        ":updated_date": result.date,
                        ":updated_store": result.store,
                        ":updated_number_of_receipts": result.number_of_receipts,
                        ":updated_items": items,
                    },
                    partition_key_value=id,
                )
            print(f"全てのレシート解析処理が完了しました。id = {id}")
        except Exception:
            print(f"レシート解析処理に失敗しました。id = {id}")
            traceback.print_exc()
            return False
        return True
