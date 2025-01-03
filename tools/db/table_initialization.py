"""
各種テーブルの初期化を行う。
実行コマンド: python -m tools.db.table_initialization
"""

import boto3
import csv
from src.app.repository.item_classification_table_repository import (
    ItemClassificationTableRepository,
)

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


def create_tables():
    """
    テーブルの作成を行う。
    """
    repository = ItemClassificationTableRepository(dynamodb)
    # repository.drop_table()
    # repository.create_table()

    # データの追加
    items = read_csv_to_list("tools/db/classifications.csv")
    for item in items:
        item_dict = {
            "minor": item[1],
            "major": item[0],
        }
        repository.put_item(item_dict)

    print(repository.get_all())


if __name__ == "__main__":
    create_tables()
