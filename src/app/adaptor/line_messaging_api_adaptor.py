import os
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApiBlob,
)

from linebot.v3.messaging.api.messaging_api import MessagingApi
from linebot.v3.messaging.models.user_profile_response import UserProfileResponse
from linebot.v3.messaging.models.show_loading_animation_request import (
    ShowLoadingAnimationRequest,
)

from linebot.v3.messaging.models.push_message_request import PushMessageRequest
from linebot.v3.messaging.models.message import Message

from src.app.config.logger import get_app_logger

CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
logger = get_app_logger(__name__)


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
        logger.info("lineからのイメージデータ取得に成功しました。")
        return binary


def fetch_user_profile(user_id: str) -> UserProfileResponse:
    """
    LINE Messaging APIからユーザ情報を取得します。
    Args:
        user_id: ユーザーID
    Returns:
        UserProfileResponse: ユーザ情報
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        profile = line_bot_api.get_profile(
            user_id=user_id,
            _request_timeout=6,
        )
        logger.info(f"lineからのユーザー情報の取得に成功しました。: {profile}")
        return profile


def show_loading_animation(user_id: str):
    """
    ユーザーとのチャット時に、ローディングを表示します。
    Args:
        user_id: ユーザーID
    Returns:
        None
    """
    request = ShowLoadingAnimationRequest(
        chat_id=user_id,
        loading_seconds=10,
    )
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        response = line_bot_api.show_loading_animation(
            show_loading_animation_request=request
        )
        logger.info(
            f"ローディング表示を有効にしました。user_id: {user_id}, response: {response}"
        )


def push_message(user_id: str, message: list[Message]):
    """
    ユーザーにメッセージを送信します。
    Args:
        user_id: ユーザーID
        message: 送信するメッセージ
    """
    push_message_request = PushMessageRequest(to=user_id, messages=message)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.push_message(push_message_request=push_message_request)
            print(f"メッセージを送信しました。user_id: {user_id}, message: {message}")
        except Exception as e:
            # NOTE メッセージ送信エラーは無視する
            print(
                f"メッセージの送信に失敗しました。user_id: {user_id}, message: {message}, error: {e}"
            )
