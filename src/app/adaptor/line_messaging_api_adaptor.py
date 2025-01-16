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
from linebot.v3.messaging.models.rich_menu_id_response import RichMenuIdResponse
from linebot.v3.messaging.models.rich_menu_list_response import (
    RichMenuListResponse,
)
from linebot.v3.messaging.models.rich_menu_request import RichMenuRequest

from linebot.v3.messaging.models.push_message_request import PushMessageRequest
from linebot.v3.messaging.models.message import Message

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


def validate_rich_menu_object(data: dict) -> str:
    """
    リッチメニューの設定情報が正しいか検証します。
    Args:
        data: リッチメニューの設定情報
    """
    rich_menu_request = RichMenuRequest.from_dict(data)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.validate_rich_menu_object(
            rich_menu_request=rich_menu_request,
        )
        print("リッチメニューは正しく構成されています")


def create_rich_menu(data: dict) -> str:
    """
    リッチメニューを設定します。
    Args:
        data: リッチメニューの設定情報
    Returns:
        リッチメニューID: str
    """
    rich_menu_request = RichMenuRequest.from_dict(data)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        response: RichMenuIdResponse = line_bot_api.create_rich_menu(
            rich_menu_request=rich_menu_request,
        )
        print(f"リッチメニューを作成しました。rich_menu_id: {response.rich_menu_id}")
        return response.rich_menu_id


def set_rich_menu_image(rich_menu_id: str, body: bytes):
    """
    リッチメニューの画像を設定します。
    Args:
        rich_menu_id: リッチメニューID
        body: リッチメニュー用の画像データ
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApiBlob(api_client)
        line_bot_api.set_rich_menu_image(
            rich_menu_id=rich_menu_id,
            body=bytearray(body),
            _headers={"Content-Type": "image/png"},
        )
        print(f"リッチメニューの画像を設定しました。rich_menu_id: {rich_menu_id}")


def set_default_rich_menu(rich_menu_id: str):
    """
    デフォルトのリッチメニューを設定します。
    Args:
        rich_menu_id: リッチメニューID
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.set_default_rich_menu(
            rich_menu_id=rich_menu_id,
        )
        print(f"デフォルトのリッチメニューを設定しました。rich_menu_id: {rich_menu_id}")


def delete_rich_menu(rich_menu_id: str):
    """
    リッチメニューを削除します。
    Args:
        rich_menu_id: リッチメニューID
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.delete_rich_menu(
            rich_menu_id=rich_menu_id,
        )
        print(f"リッチメニューを削除しました。rich_menu_id: {rich_menu_id}")


def cancel_default_rich_menu():
    """
    デフォルトのリッチメニュー設定を解除します。
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.cancel_default_rich_menu()
        print("デフォルトのリッチメニュー設定を解除しました。")


def get_rich_menu_list() -> RichMenuListResponse:
    """
    リッチメニューの一覧を取得します。
    Args:
        rich_menu_id: リッチメニューID
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        response: RichMenuListResponse = line_bot_api.get_rich_menu_list()
        print("リッチメニューの一覧を取得しました。")
        return response


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
