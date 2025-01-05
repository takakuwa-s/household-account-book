from src.app.functions.analyze_receipt import (
    lambda_handler as analyze_receipt_lambda_handler,
)
from src.app.functions.submit_reciepts import (
    lambda_handler as submit_reciepts_lambda_handler,
)


def analyze_receipt(event, context):
    return analyze_receipt_lambda_handler(event, context)


def submit_reciepts(event, context):
    return submit_reciepts_lambda_handler(event, context)
