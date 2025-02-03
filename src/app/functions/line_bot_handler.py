import json
import traceback


from linebot.v3.exceptions import InvalidSignatureError
from src.app.config.logger import LogContext, get_app_logger
from src.app.handler.line_messaging_api_handler import handler

logger = get_app_logger(__name__)


def lambda_handler(event, context):
    """
    AWS Lambdaのエントリーポイント。LINE Messaging APIのWebhookを受け取る。
    """
    LogContext.set(lambda_function_name="line_bot_handler")
    signature = event.get("headers", {}).get("x-line-signature", "")

    # get request body as text
    body = event.get("body", "")

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        traceback.print_exc()
        logger.error(
            "Invalid signature. Please check your channel access token/channel secret. signature = "
            + signature
        )

    return {"statusCode": 200, "body": json.dumps("OK")}
