import os
import boto3
from dotenv import load_dotenv

sqs = boto3.client("sqs")

# .envファイルを読み込む
load_dotenv()
QUEUE_URL = os.environ["SQS_QUEUE_URL"]


def send_message_to_sqs(message_body: str):
    """
    SQSにメッセージを送信する
    Args:
        message_body (str): メッセージ本文
    Returns:
        dict: SQSからのレスポンス
    """
    response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
    print("Message sent to SQS.")
    return response


def send_messages_to_sqs(message_bodies: list[str]):
    """
    SQSにメッセージを複数送信する
    Args:
        message_bodies (list[str]): メッセージ本文のリスト
    Returns:
        dict: SQSからのレスポンス
    """
    response = sqs.send_message_batch(
        QueueUrl=QUEUE_URL,
        Entries=[
            {"Id": str(i), "MessageBody": message_body}
            for i, message_body in enumerate(message_bodies)
        ],
    )
    print(f"{len(message_bodies)} messages sent to SQS.")
    return response
