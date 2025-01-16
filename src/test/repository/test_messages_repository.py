from linebot.v3.messaging.models.message import Message
from src.app.model.db_model import TemporalExpenditure
from src.app.repository.messages_repository import MessagesRepository

target = MessagesRepository()


def test_get_reciept_analysis_message():
    record: TemporalExpenditure = TemporalExpenditure(
        status=TemporalExpenditure.Status.ANALYZING
    )
    message_dicts: list[dict] = target.get_reciept_analysis_message(
        record.id, record.status
    )
    result = [Message.from_dict(m) for m in message_dicts]
    # print(result)
    assert len(result) > 0


def test_get_temporal_expenditure_list():
    records: list[TemporalExpenditure] = [
        TemporalExpenditure(status=TemporalExpenditure.Status.ANALYZED)
        for _ in range(3)
    ]
    message_dicts: list[dict] = target.get_temporal_expenditure_list(records)
    print(message_dicts)
    result = [Message.from_dict(m) for m in message_dicts]
    # print(result)
    assert len(result) > 0
