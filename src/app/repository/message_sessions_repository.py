from src.app.model.db_model import MessageSession
from src.app.repository.base_table_repository import BaseTableRepository


class MessageSessionsRepository(BaseTableRepository):
    def __init__(self, dynamodb):
        super().__init__(dynamodb=dynamodb, table_model=MessageSession)
