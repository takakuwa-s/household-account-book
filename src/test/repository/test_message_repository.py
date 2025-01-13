from linebot.v3.messaging.models.message import Message
from src.app.model.db_model import TemporalExpenditure
from src.app.model.usecase_model import AccountBookInput
from src.app.repository.message_repository import MessageRepository

target = MessageRepository()


def test_get_complete_reciept_analysis_message():
    record: TemporalExpenditure = TemporalExpenditure()
    message_dicts: list[dict] = target.get_complete_reciept_analysis_message(record)
    result = [Message.from_dict(m) for m in message_dicts]
    # print(result)
    assert len(result) > 0


def test_get_temporal_expenditure_list():
    records: list[TemporalExpenditure] = [
        TemporalExpenditure(
            data=AccountBookInput(
                total=1000,
                date="2022-01-01",
                store="test",
            )
        )
        for _ in range(3)
    ]
    message_dicts: list[dict] = target.get_temporal_expenditure_list(records)
    print(message_dicts)
    result = [Message.from_dict(m) for m in message_dicts]
    # print(result)
    assert len(result) > 0
