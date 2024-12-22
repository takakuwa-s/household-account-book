import os
from typing import Dict
from dotenv import load_dotenv
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

from src.app.model.usecase_model import ReceiptResult

# .envファイルを読み込む
load_dotenv()
AZURE_DOCUMENT_INTEIGENCE_ENDPOINT = os.environ["AZURE_DOCUMENT_INTEIGENCE_ENDPOINT"]
AZURE_KEY_CREDENTIAL = os.environ["AZURE_KEY_CREDENTIAL"]
AZURE_API_VERSION = os.environ["AZURE_API_VERSION"]

document_intelligence_client: DocumentIntelligenceClient = DocumentIntelligenceClient(
    endpoint=AZURE_DOCUMENT_INTEIGENCE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY_CREDENTIAL),
    api_version=AZURE_API_VERSION,
)


def analyze_receipt(data: bytes) -> list[ReceiptResult]:
    poller: AnalyzeDocumentLROPoller[AnalyzeResult] = (
        document_intelligence_client.begin_analyze_document(
            model_id="prebuilt-receipt",
            analyze_request=AnalyzeDocumentRequest(bytes_source=data),
            string_index_type=StringIndexType.UNICODE_CODE_POINT,
        )
    )
    receipts: AnalyzeResult = poller.result()

    result = []
    if receipts.documents:
        for document in receipts.documents:
            field: Dict[str, DocumentField] = document.fields
            if field is None:
                continue
            print(field)
            receipt = ReceiptResult()
            receipt.date = field.get("TransactionDate", {}).get("valueDate", "")
            receipt.store = field.get("MerchantName", {}).get("valueString", "")
            receipt.total = (
                field.get("Total", {}).get("valueCurrency", {}).get("amount", "")
            )
            receipt.items = []
            for value in field.get("Items", {}).get("valueArray", []):
                value_object = value.get("valueObject", {})
                item = ReceiptResult.Item()
                item.name = value_object.get("Description", {}).get("valueString", "")
                item.price = (
                    value_object.get("TotalPrice", {})
                    .get("valueCurrency", {})
                    .get("amount", "")
                )
                receipt.items.append(item)
            result.append(receipt)
    return result
