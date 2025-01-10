from linebot.v3.messaging.models.message import Message
from src.app.model.db_model import TemporalExpenditure
from src.app.repository.message_repository import MessageRepository

target = MessageRepository()


def test_get_complete_reciept_analysis_message():
    record: TemporalExpenditure = TemporalExpenditure()
    message_dicts: list[dict] = target.get_complete_reciept_analysis_message(record)
    result = [Message.from_dict(m) for m in message_dicts]
    print(result)
    assert len(result) > 0
