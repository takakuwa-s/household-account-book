"""
各種テーブルの初期化を行う。
実行コマンド: python -m tools.db.table_initialization
"""

import boto3
import csv
from src.app.repository.item_classifications_repository import (
    ItemClassificationsRepository,
)
from src.app.repository.message_sessions_repository import (
    MessageSessionsRepository,
)
from src.app.repository.temporal_expenditures_repository import (
    TemporalExpendituresRepository,
)
from src.app.repository.users_reposioty import UsersRepository
from src.app.repository.image_sets_repository import ImageSetsRepository

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


def create_item_classifications_table():
    """
    ItemClassificationsテーブルの作成を行う。
    """
    repository = ItemClassificationsRepository(dynamodb)
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


def create_temporal_expenditures_table():
    """
    TemporalExpendituresテーブルの作成を行う。
    """
    repository = TemporalExpendituresRepository(dynamodb)
    # repository.drop_table()
    repository.create_table()
    # repository.delete_item("bcf46ac4-79d7-41cf-84a6-6cbad250b97f")
    print(repository.get_all())


def create_users_table():
    """
    Usersテーブルの作成を行う。
    """
    repository = UsersRepository(dynamodb)
    # repository.drop_table()
    repository.create_table()
    print(repository.get_all())


def create_message_sessions_table():
    """
    MessageSessionsテーブルの作成を行う。
    """
    repository = MessageSessionsRepository(dynamodb)
    # repository.drop_table()
    repository.create_table()
    print(repository.get_all())


def create_image_sets_table():
    """
    ImageSetsRepositoryテーブルの作成を行う。
    """
    repository = ImageSetsRepository(dynamodb)
    # repository.drop_table()
    repository.create_table()
    print(repository.get_all())


if __name__ == "__main__":
    # create_item_classifications_table()
    create_temporal_expenditures_table()
    create_users_table()
    create_message_sessions_table()
    create_image_sets_table()
