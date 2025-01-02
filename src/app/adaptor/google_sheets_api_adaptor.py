from dotenv import load_dotenv
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

from src.app.model.usecase_model import AccountBookInput

# .envファイルを読み込む
load_dotenv()
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
EXPENDITURE_SHEET_NAME = os.environ["EXPENDITURE_SHEET_NAME"]

# 認証情報のスコープ
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# 認証情報ファイルのパス
CREDS_FILE = "resource/gcp-credentials.json"


def append_data_to_spreadsheet(spreadsheet_id, sheet_name, data_list):
    """
    スプレッドシートの一番下の行に複数のデータを追加します。

    Args:
        spreadsheet_id: スプレッドシートのID。URLから取得できます。
        sheet_name: シート名。
        data_list: 追加するデータのリストのリスト。例: [['value1', 'value2'], ['value3', 'value4']]
    """
    # 認証情報を作成
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    # Google Sheets APIに接続
    client = gspread.authorize(creds)

    # スプレッドシートを開く
    spreadsheet = client.open_by_key(spreadsheet_id)
    # シートを取得
    sheet = spreadsheet.worksheet(sheet_name)

    sheet.append_rows(data_list)

    print(
        f"データをスプレッドシート '{spreadsheet_id}' のシート '{sheet_name}' に追加しました。"
    )


def append_house_hold_account_book(input: AccountBookInput):
    """
    家計簿のデータをスプレッドシートに追加します。
    Args:
        input: 家計簿のデータ。
    """
    data = []
    for result in input.receipt_results:
        for item in result.items:
            data.append(
                [
                    result.date.strftime("%Y/%m/%d"),
                    item.name,
                    result.store,
                    item.price,
                    input.major_classification,
                    input.minor_classification,
                    input.payer,
                    input.for_whom,
                    input.payment_method,
                    item.remarks,
                ]
            )
    append_data_to_spreadsheet(SPREADSHEET_ID, EXPENDITURE_SHEET_NAME, data)
