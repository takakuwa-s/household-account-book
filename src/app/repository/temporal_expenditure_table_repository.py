from src.app.model.db_model import TemporalExpenditure
from src.app.repository.base_table_repository import BaseTableRepository


class TemporalExpenditureTableRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=TemporalExpenditure)
