from src.app.model.db_model import TemporalExpenditure
from src.app.model.usecase_model import PaymentMethodEnum
from src.app.repository.base_table_repository import BaseTableRepository


class TemporalExpenditureRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=TemporalExpenditure)

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
