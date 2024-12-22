from src.app.adaptor.azure_ducument_intelligence_client import analyze_receipt
from src.app.model.usecase_model import ReceiptResult

def register_expenditure():
    file_path = "/Users/takakuwashun/app/python/3.12.2/household-account-book/src/app/adaptor/test_receipt.png"
    with open(file_path, "rb") as image_file:
      data = image_file.read()
    
    result: ReceiptResult = analyze_receipt(data)
    print(result)
    