from dotenv import load_dotenv
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
        print(f"lineからのユーザー情報の取得に成功しました。: {profile}")
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
        print(
            f"ローディング表示を有効にしました。user_id: {user_id}, response: {response}"
        )
