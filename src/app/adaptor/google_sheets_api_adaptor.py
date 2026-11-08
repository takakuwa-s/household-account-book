import gspread
import os
from google.oauth2.service_account import Credentials

from src.app.config.logger import get_app_logger
from src.app.model.usecase_model import AccountBookInput

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
EXPENDITURE_SHEET_NAME = os.environ["EXPENDITURE_SHEET_NAME"]
NEW_ROW_COLOR = "#fff2cc"  # 新しい行の背景色（例: "#FFF2CC"）

# --- 認証とクライアントの初期化（ファイル内の別で定義してOKです） ---
CREDS_FILE = "resource/gcp-credentials.json"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
client = gspread.authorize(creds)

logger = get_app_logger(__name__)

def _get_target_range(sheet, data_list):
    """実際のデータの最終行を特定し、範囲を算出。
    シートの行数が足りない場合は自動的に行を追加します。
    """
    if not data_list:
        return None, 0, 0

    all_values = sheet.get_all_values()
    last_row = 0
    for i in range(len(all_values) - 1, -1, -1):
        if any(cell != "" for cell in all_values[i]):
            last_row = i + 1
            break

    start_row = last_row + 1 if last_row > 0 else 1
    num_rows_to_add = len(data_list)
    end_row = start_row + num_rows_to_add - 1
    max_col_idx = len(data_list[0]) if data_list[0] else 0

    if max_col_idx == 0:
        return None, 0, 0

    # 【追加】必要な行数が現在のシートの総行数を超えている場合、行を自動追加する
    current_total_rows = sheet.row_count
    if end_row > current_total_rows:
        # 足りない行数分（＋余裕を持たせるなら少し多め）を行末に追加
        rows_to_add_count = end_row - current_total_rows
        sheet.add_rows(rows_to_add_count)

    col_letter = gspread.utils.rowcol_to_a1(1, max_col_idx).rstrip('1')
    target_range = f"A{start_row}:{col_letter}{end_row}"

    return target_range, start_row, end_row


def _write_data_to_sheet(sheet, target_range, data_list):
    """指定された範囲にデータを書き込むプライベート関数。

    Args:
        sheet (gspread.Worksheet): 対象のワークシートオブジェクト。
        target_range (str): 書き込み先のA1形式の範囲（例: "A5:C6"）。
        data_list (list[list]): 追加するデータのリスト。

    Returns:
        None
    """
    sheet.update(
        range_name=target_range,
        values=data_list,
        value_input_option="USER_ENTERED"
    )


def _apply_row_background_color(sheet, target_range, background_color):
    """指定された範囲に背景色を設定するプライベート関数。

    Args:
        sheet (gspread.Worksheet): 対象のワークシートオブジェクト。
        target_range (str): 色を設定する範囲（例: "A5:C6"）。
        background_color (str, optional): 
            16進数カラーコード（例: "#FFF2CC"）。
            None の場合は何もしません。

    Returns:
        None
    """
    if not background_color or not target_range:
        return

    hex_str = background_color.lstrip('#')
    rgb_dict = {
        "red": int(hex_str[0:2], 16) / 255.0,
        "green": int(hex_str[2:4], 16) / 255.0,
        "blue": int(hex_str[4:6], 16) / 255.0
    }

    format_spec = {
        "backgroundColor": rgb_dict
    }
    
    sheet.format(target_range, format_spec)


def append_data_to_spreadsheet(spreadsheet_id, sheet_name, data_list, background_color=None):
    """スプレッドシートにデータを追加し、必要に応じて背景色を設定します。

    Args:
        spreadsheet_id (str): スプレッドシートのID。URLから取得できます。
        sheet_name (str): シート名。
        data_list (list[list]): 追加するデータのリストのリスト。例: [['value1', 'value2'], ['value3', 'value4']]
        background_color (str, optional): 背景色（例: "#FFF2CC" や "#FFCCCC" のような16進数カラーコード）。
                                          None の場合は背景色を設定しません。

    Returns:
        None
    """
    if not data_list:
        logger.info("追加するデータがありません。")
        return

    # スプレッドシートを開く
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.worksheet(sheet_name)

    # 1. 代入する行や範囲を特定する
    target_range, start_row, end_row = _get_target_range(sheet, data_list)
    if not target_range:
        logger.warning("有効な書き込み範囲を特定できませんでした。")
        return

    # 2. 値を導入（書き込み）する
    _write_data_to_sheet(sheet, target_range, data_list)

    # 3. 色を設定する（指定がある場合のみ）
    if background_color:
        _apply_row_background_color(sheet, target_range, background_color)
        logger.info(f"データを書き込み、行 {start_row}〜{end_row} に背景色を設定しました。")
    else:
        logger.info(f"データを書き込みました（行 {start_row}〜{end_row}）。")

def register_expenditure(input: AccountBookInput):
    """
    家計簿のスプレッドシートに支出データを追加します。
    Args:
        input: 支出データ。
    """
    data = []
    for item in input.items:
        data.append(
            [
                input.date.replace("-", "/"),
                item.name,
                input.store,
                item.price,
                "その他" if item.name == "消費税" else input.major_classification,
                "税金" if item.name == "消費税" else input.minor_classification,
                input.payer,
                input.for_whom,
                input.payment_method,
                "",
                item.remarks,
            ]
        )
    append_data_to_spreadsheet(SPREADSHEET_ID, EXPENDITURE_SHEET_NAME, data, NEW_ROW_COLOR)


def register_only_total(input: AccountBookInput):
    """
    家計簿のスプレッドシートに支出データを追加します。
    Args:
        input: 支出データ。
    """
    data = [
        [
            input.date.replace("-", "/"),
            f"{input.minor_classification}等",
            input.store,
            input.total,
            input.major_classification,
            input.minor_classification,
            input.payer,
            input.for_whom,
            input.payment_method,
            ""
            "LINE経由。レシートの合計のみ登録",
        ]
    ]
    append_data_to_spreadsheet(SPREADSHEET_ID, EXPENDITURE_SHEET_NAME, data, NEW_ROW_COLOR)
