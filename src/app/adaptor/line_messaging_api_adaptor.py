from dotenv import load_dotenv
import os
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApiBlob,
)

# .envファイルを読み込む
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)


def fetch_image(message_id: str) -> bytearray:
    """
    LINE Messaging APIからイメージデータを取得します。
    Args:
        message_id: メッセージID
    Returns:
        bytearray: イメージデータ
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApiBlob(api_client)
        binary = line_bot_api.get_message_content(
            message_id=message_id,
            _request_timeout=6,
        )
        print("lineからのイメージデータ取得に成功しました。")
        return binary
