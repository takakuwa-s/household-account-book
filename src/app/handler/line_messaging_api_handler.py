from dotenv import load_dotenv
import os

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    ApiException,
    Configuration,
    ErrorResponse,
    Message,
    MessagingApi,
    ReplyMessageRequest,
)
from linebot.v3.webhooks import MessageEvent, ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from src.app.usecase.hundle_line_message_usecase import HundleLineMessageUsecase

# .envファイルを読み込む
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=CHANNEL_SECRET)
usecase = HundleLineMessageUsecase()


def reply_message(reply_token: str, messages: list[Message]):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=messages,
                )
            )
        except ApiException as e:
            print(
                f"LINE Messagigng APIでエラーが発生しました。status code = {str(e.status)}, body = {str(ErrorResponse.from_json(e.body))}"
            )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    if event.source.type == "user":
        messages = usecase.handle_text_message(event.message, event.source.user_id)
    else:
        messages = usecase.group_message()
    reply_message(event.reply_token, messages)


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event: MessageEvent):
    if event.source.type == "user":
        messages = usecase.handle_image_message(event.message, event.source.user_id)
    else:
        messages = usecase.group_message()
    reply_message(event.reply_token, messages)


@handler.default()
def default(event: MessageEvent):
    messages = usecase.handle_default_event()
    reply_message(event.reply_token, messages)
