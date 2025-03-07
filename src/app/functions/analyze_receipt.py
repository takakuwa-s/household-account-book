import os
import boto3

from src.app.config.logger import LogContext, get_app_logger
from src.app.usecase.analyze_receipt_usecase import AnalyzeReceiptUsecase

QUEUE_URL = os.environ["SQS_QUEUE_URL"]

# SQSクライアントを作成
sqs = boto3.client("sqs")
usecase = AnalyzeReceiptUsecase()
logger = get_app_logger(__name__)


def lambda_handler(event, context):
    LogContext.set(lambda_function_name="analyze_receipt")
    logger.info(f"sqsからデータを受信しました。event = {event}")

    for record in event["Records"]:
        receipt_handle = record["receiptHandle"]
        body = record["body"]
        completed = usecase.execute(body)

        # メッセージを削除
        if completed:
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

    return {"statusCode": 200, "body": "Message processed successfully"}
