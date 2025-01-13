import boto3
from src.app.model.db_model import TemporalExpenditure
from src.app.repository.temporal_expenditure_repository import (
    TemporalExpenditureRepository,
)

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
target = TemporalExpenditureRepository(dynamodb)


def test_get_all_by_line_user_id():
    line_user_id = "test"
    test = TemporalExpenditure(line_user_id=line_user_id)
    target.put_item(test.model_dump())
    result = target.get_all_by_line_user_id(line_user_id)
    # print(result)
    assert len(result) > 0

    target.delete_item(test.id)
