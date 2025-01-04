from linebot.v3.messaging.models.message import Message
from linebot.v3.webhooks.models.image_message_content import ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_content import PostbackContent
from src.app.usecase.hundle_line_message_usecase import HundleLineMessageUsecase
from src.app.model import (
    usecase_model as uc,
)


def test_group_message():
    usecase = HundleLineMessageUsecase()
    reslut: list[Message] = usecase.group_message()
    print(reslut)
    assert len(reslut) > 0


def test_handle_default_event():
    usecase = HundleLineMessageUsecase()
    reslut: list[Message] = usecase.handle_default_event()
    print(reslut)
    assert len(reslut) > 0


def test_handle_image_message():
    usecase = HundleLineMessageUsecase()
    input = {
        "type": "image",
        "id": "354718705033693859",
        "quoteToken": "q3Plxr4AgKd...",
        "contentProvider": {"type": "line"},
    }
    reslut: list[Message] = usecase.handle_image_message(
        ImageMessageContent.from_dict(input), "user_id"
    )
    print(reslut)
    assert len(reslut) > 0


def test_handle_text_message():
    usecase = HundleLineMessageUsecase()
    input = {
        "id": "444573844083572737",
        "type": "text",
        "quoteToken": "q3Plxr4AgKd...",
        "text": "rフィアlfl",
    }
    reslut: list[Message] = usecase.handle_text_message(
        TextMessageContent.from_dict(input), "user_id"
    )
    print(reslut)
    assert len(reslut) > 0


def test_handle_postback_event():
    usecase = HundleLineMessageUsecase()

    data = uc.RegisterExpenditurePostback(
        **{
            "id": "444573844083572737",
            "type": "change_classification",
        }
    )
    postback = PostbackContent(data=data.model_dump_json())
    reslut: list[Message] = usecase.handle_postback_event(postback)
    print(reslut)
    assert len(reslut) > 0
