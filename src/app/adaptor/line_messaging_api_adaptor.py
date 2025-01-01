from dotenv import load_dotenv
import os
from linebot.v3.messaging import (
    ApiClient,
    ApiException,
    Configuration,
    ErrorResponse,
    MessagingApiBlob,
)

# .envファイルを読み込む
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)


def fetch_image(message_id: str) -> bytearray:
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApiBlob(api_client)
        try:
            return line_bot_api.get_message_content(
                message_id=message_id,
                _request_timeout=6,
            )
        except ApiException as e:
            print(
                f"LINE Messagigng APIでエラーが発生しました。status code = {str(e.status)}, body = {str(ErrorResponse.from_json(e.body))}"
            )
