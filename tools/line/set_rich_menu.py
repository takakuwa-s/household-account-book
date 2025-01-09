import json
from linebot.v3.messaging.models.rich_menu_list_response import RichMenuListResponse
from src.app.adaptor.line_messaging_api_adaptor import (
    cancel_default_rich_menu,
    create_rich_menu,
    delete_rich_menu,
    get_rich_menu_list,
    set_default_rich_menu,
    set_rich_menu_image,
    validate_rich_menu_object,
)


def set_rich_menu():
    """
    リッチメニューを設定します。
    """
    # デフォルトのリッチメニュー設定を解除
    cancel_default_rich_menu()

    # リッチメニューを削除
    menus: RichMenuListResponse = get_rich_menu_list()
    for menu in menus.richmenus:
        delete_rich_menu(menu.rich_menu_id)

    # リッチメニューを検証
    with open("tools/line/rich_menu.json", "r") as file:
        data = json.load(file)
    rich_menu_id = validate_rich_menu_object(data)

    # リッチメニューを作成
    rich_menu_id = create_rich_menu(data)

    # リッチメニューの画像を設定
    with open("tools/line/richmenu.png", "rb") as file:
        image = file.read()
    set_rich_menu_image(rich_menu_id, image)

    # デフォルトのリッチメニューを設定
    set_default_rich_menu(rich_menu_id)


if __name__ == "__main__":
    set_rich_menu()
