from boto3.dynamodb.conditions import Attr
from src.app.model.db_model import TemporalExpenditure, calculate_ttl_timestamp
from src.app.model.usecase_model import PaymentMethodEnum, ReceiptResult
from src.app.repository.base_table_repository import BaseTableRepository


class TemporalExpendituresRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=TemporalExpenditure)

    def get_all_by_line_user_id(self, line_user_id: str) -> list[TemporalExpenditure]:
        """
        LINEユーザーIDで全ての仮支出データを取得します。
        Args:
            line_user_id (str): LINEユーザーID
        Returns:
            仮支出データのリスト
        """
        # filter_expression: str = Attr("line_user_id").eq(line_user_id) & ~Attr(
        #     "status"
        # ).eq(TemporalExpenditure.Status.NEW)
        filter_expression: str = Attr("line_user_id").eq(line_user_id)
        return self.scan_items(filter_expression)

    def update_date(self, id: str, date: str) -> TemporalExpenditure:
        """
        日付を更新します。
        Args:
            id (str): ID
            date (str): 日付
        Returns:
            更新されたレコード
        """
        return self.update_item(
            update_expression="SET #data.#date = :updated",
            expression_attribute_names={
                "#data": "data",
                "#date": "date",
            },
            expression_attribute_values={":updated": date},
            partition_key_value=id,
        )

    def update_classification(
        self, id: str, minar_classification: str, major_classification: str
    ) -> TemporalExpenditure:
        """
        分類を更新します。
        Args:
            id (str): ID
            minar_classification (str): 小分類
            major_classification (str): 大分類
        Returns:
            更新されたレコード
        """
        return self.update_item(
            update_expression="SET #data.#minor_classification = :updated_minor, #data.#major_classification = :updated_major",
            expression_attribute_names={
                "#data": "data",
                "#minor_classification": "minor_classification",
                "#major_classification": "major_classification",
            },
            expression_attribute_values={
                ":updated_minor": minar_classification,
                ":updated_major": major_classification,
            },
            partition_key_value=id,
        )

    def update_for_whom(self, id: str, for_whom: str) -> TemporalExpenditure:
        """
        誰向けの支出かを更新します。
        Args:
            id (str): ID
            for_whom (str): 誰向けの支出か
        Returns:
            更新されたレコード
        """
        return self.update_item(
            update_expression="SET #data.#for_whom = :updated",
            expression_attribute_names={
                "#data": "data",
                "#for_whom": "for_whom",
            },
            expression_attribute_values={":updated": for_whom},
            partition_key_value=id,
        )

    def update_payer(self, id: str, payer: str) -> TemporalExpenditure:
        """
        支払者を更新します。
        Args:
            id (str): ID
            payer (str): 支払者
        Returns:
            更新されたレコード
        """
        return self.update_item(
            update_expression="SET #data.#payer = :updated",
            expression_attribute_names={
                "#data": "data",
                "#payer": "payer",
            },
            expression_attribute_values={":updated": payer},
            partition_key_value=id,
        )

    def update_payment_method(
        self, id: str, payment_method: str
    ) -> TemporalExpenditure:
        """
        支払方法を更新します。
        Args:
            id (str): ID
            payment_method (str): 支払方法
        Returns:
            更新されたレコード
        """
        return self.update_item(
            update_expression="SET #data.#payment_method = :updated",
            expression_attribute_names={
                "#data": "data",
                "#payment_method": "payment_method",
            },
            expression_attribute_values={
                ":updated": PaymentMethodEnum.value_of(payment_method)
            },
            partition_key_value=id,
        )

    def update_analysis_failure(self, id: str) -> TemporalExpenditure:
        """
        解析失敗として、レコードを更新します。
        Args:
            id (str): 仮支出データのID
        Returns:
            更新されたレコード
        """
        ttl = calculate_ttl_timestamp(delete_date=1)
        return self.update_item(
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

    def update_analysis_success(
        self, id: str, result: ReceiptResult
    ) -> TemporalExpenditure:
        """
        解析成功として、レコードを更新します。
        Args:
            id (str): 仮支出データのID
            result (ReceiptResult): レシート解析結果
        Returns:
            更新されたレコード
        """
        items = [i.model_dump() for i in result.items]
        return self.update_item(
            update_expression="SET #status = :updated_status, #data.#total = :updated_total, #data.#date = :updated_date, #data.#store = :updated_store, #data.#items = :updated_items",
            expression_attribute_names={
                "#status": "status",
                "#data": "data",
                "#total": "total",
                "#date": "date",
                "#store": "store",
                "#items": "items",
            },
            expression_attribute_values={
                ":updated_status": TemporalExpenditure.Status.ANALYZED,
                ":updated_total": result.total,
                ":updated_date": result.date,
                ":updated_store": result.store,
                ":updated_items": items,
            },
            partition_key_value=id,
        )
