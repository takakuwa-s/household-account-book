import json
import os
import sys
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApiBlob,
)
from linebot.v3.messaging.api.messaging_api import MessagingApi
from linebot.v3.messaging.models.rich_menu_id_response import RichMenuIdResponse
from linebot.v3.messaging.models.rich_menu_list_response import RichMenuListResponse
from linebot.v3.messaging.models.rich_menu_request import RichMenuRequest
from linebot.v3.messaging.models.set_webhook_endpoint_request import (
    SetWebhookEndpointRequest,
)
from linebot.v3.messaging.models.test_webhook_endpoint_request import (
    TestWebhookEndpointRequest,
)
from linebot.v3.messaging.models.test_webhook_endpoint_response import (
    TestWebhookEndpointResponse,
)

CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)


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


def set_webhook_endpoint(url: str):
    """
    LINE Messaging APIのWebhookエンドポイントを設定します。
    Args:
        url: WebhookエンドポイントのURL
    """
    request = SetWebhookEndpointRequest(endpoint=url)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.set_webhook_endpoint(set_webhook_endpoint_request=request)
        print(f"LINE Messaging APIのWebhookエンドポイントを設定しました。url: {url}")


def test_webhook_endpoint(url: str = None) -> bool:
    """
    LINE Messaging APIのWebhookエンドポイントをテストします。
    Args:
        url: WebhookエンドポイントのURL
    """
    request = None if url is None else TestWebhookEndpointRequest(endpoint=url)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        response: TestWebhookEndpointResponse = line_bot_api.test_webhook_endpoint(
            request
        )
        if response.success:
            print(
                f"LINE Messaging APIのWebhookエンドポイントのテストに成功しました。response: {response}"
            )
        else:
            print(
                f"LINE Messaging APIのWebhookエンドポイントのテストに失敗しました。response: {response}"
            )
        return response.success


def set_rich_menu():
    """
    リッチメニューを設定します。
    """
    folder_path = "../../scripts"

    # デフォルトのリッチメニュー設定を解除
    cancel_default_rich_menu()

    # リッチメニューを削除
    menus: RichMenuListResponse = get_rich_menu_list()
    for menu in menus.richmenus:
        delete_rich_menu(menu.rich_menu_id)

    # リッチメニューを検証
    with open(f"{folder_path}/rich_menu.json", "r") as file:
        data = json.load(file)
    rich_menu_id = validate_rich_menu_object(data)

    # リッチメニューを作成
    rich_menu_id = create_rich_menu(data)

    # リッチメニューの画像を設定
    with open(f"{folder_path}/richmenu.png", "rb") as file:
        image = file.read()
    set_rich_menu_image(rich_menu_id, image)

    # デフォルトのリッチメニューを設定
    set_default_rich_menu(rich_menu_id)


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        url = args[1]
        set_webhook_endpoint(url)
        set_rich_menu()
        test_webhook_endpoint(url)
    else:
        print("Argument is invalid, args: ", args)
