from src.app.model.db_model import TemporalExpenditure
from src.app.model.usecase_model import AccountBookInput
from src.app.repository.base_table_repository import BaseTableRepository


class TemporalExpenditureTableRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=TemporalExpenditure)

    def create_from_account_book_input(
        self, input: AccountBookInput
    ) -> TemporalExpenditure:
        """
        会計帳簿の入力情報を保存します。
        Args:
            input (AccountBookInput): 会計帳簿の入力情報
        Returns:
            str: 保存したデータ
        """
        record = TemporalExpenditure(data=input)
        self.put_item(record.model_dump())
        return record
