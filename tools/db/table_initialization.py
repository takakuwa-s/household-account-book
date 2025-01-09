"""
各種テーブルの初期化を行う。
実行コマンド: python -m tools.db.table_initialization
"""

import boto3
import csv
from src.app.repository.item_classification_repository import (
    ItemClassificationRepository,
)
from src.app.repository.message_session_repository import (
    MessageSessionRepository,
)
from src.app.repository.temporal_expenditure_repository import (
    TemporalExpenditureRepository,
)
from src.app.repository.user_reposioty import UserRepository

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


def read_csv_to_list(filepath: str) -> list[list]:
    """
    CSVファイルを読み取り、二次元配列としてデータを格納します。

    Args:
        filepath (str): CSVファイルのパス。

    Returns:
        list: 二次元配列リスト
    """
    data = []
    with open(filepath, "r", encoding="utf-8") as file:  # UTF-8エンコーディングを指定
        reader = csv.reader(file)
        for row in reader:
            data.append((row))
    return data


def create_item_classification_table():
    """
    ItemClassificationテーブルの作成を行う。
    """
    repository = ItemClassificationRepository(dynamodb)
    # repository.drop_table()
    # repository.create_table()

    # データの追加
    items = read_csv_to_list("tools/db/classifications.csv")
    for item in items:
        item_dict = {
            "minor": item[1],
            "major": item[0],
            "color": item[2],
        }
        repository.put_item(item_dict)

    print(repository.get_all())


def create_temporal_expenditure_table():
    """
    TemporalExpenditureテーブルの作成を行う。
    """
    repository = TemporalExpenditureRepository(dynamodb)
    # repository.drop_table()
    # repository.create_table()
    repository.delete_item("bcf46ac4-79d7-41cf-84a6-6cbad250b97f")
    print(repository.get_all())


def create_user_table():
    """
    Userテーブルの作成を行う。
    """
    repository = UserRepository(dynamodb)
    # repository.drop_table()
    repository.create_table()
    # print(repository.get_all())


def create_message_session_table():
    """
    MessageSessionテーブルの作成を行う。
    """
    repository = MessageSessionRepository(dynamodb)
    # repository.drop_table()
    # repository.create_table()
    print(repository.get_all())


if __name__ == "__main__":
    # create_item_classification_table()
    # create_temporal_expenditure_table()
    # create_user_table()
    create_message_session_table()
