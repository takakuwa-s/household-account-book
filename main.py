from src.app.functions.analyze_receipt import (
    lambda_handler as analyze_receipt_lambda_handler,
)
from src.app.functions.line_bot_handler import (
    lambda_handler as line_bot_handler_lambda_handler,
)


def analyze_receipt(event, context):
    return analyze_receipt_lambda_handler(event, context)


def line_bot_handler(event, context):
    return line_bot_handler_lambda_handler(event, context)
