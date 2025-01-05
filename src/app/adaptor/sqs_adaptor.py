import os
import boto3
from dotenv import load_dotenv

sqs = boto3.client("sqs")

# .envファイルを読み込む
load_dotenv()
QUEUE_URL = os.environ["SQS_QUEUE_URL"]


def send_message_to_sqs(message_body):
    """
    SQSにメッセージを送信する
    Args:
        message_body (str): メッセージ本文
    Returns:
        dict: SQSからのレスポンス
    """
    response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
    return response
