import os
from typing import Dict
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import (
    AnalyzeDocumentLROPoller,
    DocumentIntelligenceClient,
)
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    DocumentField,
    StringIndexType,
)

from src.app.config.logger import get_app_logger
from src.app.model.usecase_model import ReceiptResult

AZURE_DOCUMENT_INTEIGENCE_ENDPOINT = os.environ["AZURE_DOCUMENT_INTEIGENCE_ENDPOINT"]
AZURE_KEY_CREDENTIAL = os.environ["AZURE_KEY_CREDENTIAL"]
AZURE_API_VERSION = "2024-11-30"

document_intelligence_client: DocumentIntelligenceClient = DocumentIntelligenceClient(
    endpoint=AZURE_DOCUMENT_INTEIGENCE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY_CREDENTIAL),
    api_version=AZURE_API_VERSION,
)
logger = get_app_logger(__name__)


def analyze_receipt(data: bytes) -> list[ReceiptResult]:
    """
    レシートを読み取り、結果を返します。
    Args:
        data: レシートのバイナリデータ
    Returns:
        レシートの読み取り結果
    """
    if data is None:
        return None

    poller: AnalyzeDocumentLROPoller[AnalyzeResult] = (
        document_intelligence_client.begin_analyze_document(
            model_id="prebuilt-receipt",
            analyze_request=AnalyzeDocumentRequest(bytes_source=data),
            string_index_type=StringIndexType.UNICODE_CODE_POINT,
        )
    )
    result: AnalyzeResult = poller.result()
    receipt_list: list[ReceiptResult] = []

    if result.documents:
        for document in result.documents:
            field: Dict[str, DocumentField] = document.fields
            if field is None:
                continue
            receipt = ReceiptResult()
            sum = 0
            for value in field.get("Items", {}).get("valueArray", []):
                value_object = value.get("valueObject", {})
                price = (
                    value_object.get("TotalPrice", {})
                    .get("valueCurrency", {})
                    .get("amount")
                )
                if price is None:
                    continue
                price = int(price)
                sum += price
                if price < 0:
                    receipt.items[-1].price += price
                    receipt.items[-1].remarks += f"{price}円の割引。"
                else:
                    item = ReceiptResult.Item()
                    item.name = value_object.get("Description", {}).get(
                        "valueString", ""
                    )
                    item.price = price
                    receipt.items.append(item)
            receipt.date = field.get("TransactionDate", {}).get("valueDate")
            receipt.store = field.get("MerchantName", {}).get("valueString", "不明")
            receipt.set_total(
                field.get("Total", {}).get("valueCurrency", {}).get("amount")
            )

            # 消費税の設定
            receipt.append_tax(sum)
            if receipt.total is None and len(receipt.items) == 0:
                continue
            logger.info(
                f"{receipt.date}に{receipt.store}で購入した合計{receipt.total}円のレシートに関して、解析に成功しました"
            )
            receipt_list.append(receipt)
    if len(receipt_list) == 0:
        logger.info("レシートの解析ができませんでした。")
        return None
    logger.info("AIによる画像に写っている全てのレシート解析が完了しました。")
    return receipt_list
