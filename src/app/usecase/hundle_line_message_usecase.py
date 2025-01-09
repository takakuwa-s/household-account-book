import json
import traceback
import boto3
from linebot.v3.messaging.models.message import Message
from linebot.v3.webhooks.models.image_message_content import ImageMessageContent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_content import PostbackContent
from linebot.v3.messaging.models.user_profile_response import UserProfileResponse

from src.app.adaptor.line_messaging_api_adaptor import (
    fetch_user_profile,
)
from src.app.adaptor.google_sheets_api_adaptor import register_expenditure
from src.app.adaptor.sqs_adaptor import send_message_to_sqs
from src.app.model import (
    db_model as db,
    usecase_model as uc,
)
from src.app.repository.item_classification_repository import (
    ItemClassificationRepository,
)
from src.app.repository.message_repository import MessageRepository
from src.app.repository.message_session_repository import (
    MessageSessionRepository,
)
from src.app.repository.temporal_expenditure_repository import (
    TemporalExpenditureRepository,
)
from src.app.repository.user_reposioty import UserRepository

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


class HundleLineMessageUsecase:
    def __init__(self):
        self.item_classification_repository = ItemClassificationRepository(dynamodb)
        self.temporal_expenditure_repository = TemporalExpenditureRepository(dynamodb)
        self.user_repository = UserRepository(dynamodb)
        self.message_session_repository = MessageSessionRepository(dynamodb)
        self.message_repository = MessageRepository()

    def to_message(function):
        def _wrapper(*args, **keywords):
            self = args[0]
            try:
                messages = function(*args, **keywords)
                if messages is None:
                    messages = self.message_repository.get_message(
                        "[message_not_found_error]"
                    )
            except Exception as e:
                messages = self.message_repository.get_error_message(e)
                traceback.print_exc()
            return [Message.from_dict(m) for m in messages]

        return _wrapper

    @to_message
    def group_message(self) -> list[Message]:
        return self.message_repository.get_message("[group_error]")

    @to_message
    def handle_follow_event(self, user_id: str) -> list[Message]:
        profile: UserProfileResponse = fetch_user_profile(user_id)
        user: db.User = db.User(line_user_id=user_id, line_name=profile.display_name)
        self.user_repository.put_item(user.model_dump())
        return self.message_repository.get_follow_message(user.line_name)

    @to_message
    def handle_text_message(
        self, message: TextMessageContent, user_id: str
    ) -> list[Message]:
        session: db.MessageSession = self.message_session_repository.get_item(user_id)
        if session is not None:
            self.message_session_repository.delete_item(user_id)
            match session.type:
                case db.MessageSession.SessionType.REGISTER_USER:
                    user: db.User = self.user_repository.get_item(user_id)
                    user.name = message.text
                    self.user_repository.put_item(user.model_dump())
                    return self.message_repository.get_register_user_message(
                        message.text, user.line_name
                    )
        match message.text:
            case uc.KeywordsEnum.REGISTER_USER.value:
                session: db.MessageSession = db.MessageSession(line_user_id=user_id)
                self.message_session_repository.put_item(session.model_dump())
                response: list[dict] = self.message_repository.get_message(message.text)
            case uc.KeywordsEnum.REGISTER_COMMON_FOOD.value:
                response: list[dict] = self.__set_default_expenditure_setting(
                    user_id, "生活費", "食費", True
                )
            case uc.KeywordsEnum.REGISTER_COMMON_DAILY_NECESSALITIES.value:
                response: list[dict] = self.__set_default_expenditure_setting(
                    user_id, "生活費", "日用品", True
                )
            case uc.KeywordsEnum.REGISTER_MY_DAILY_NECESSALITIES.value:
                response: list[dict] = self.__set_default_expenditure_setting(
                    user_id, "生活費", "日用品", False
                )
            case uc.KeywordsEnum.REGISTER_COMMON_ALCOHOL.value:
                response: list[dict] = self.__set_default_expenditure_setting(
                    user_id, "娯楽", "家飲み", True
                )
            case uc.KeywordsEnum.REGISTER_MY_FASHION.value:
                response: list[dict] = self.__set_default_expenditure_setting(
                    user_id, "生活費", "ファッション", False
                )
            case _:
                response: list[dict] = self.message_repository.get_message(message.text)
        return response

    def __set_default_expenditure_setting(
        self,
        user_id: str,
        major_classification: str,
        minor_classification: str,
        is_common_for_whom: bool,
    ) -> list[dict]:
        user: db.User = self.user_repository.get_item(user_id)
        payer = "" if user is None else user.name
        for_whom = "共通" if is_common_for_whom else payer
        data = uc.AccountBookInput(
            payer=payer,
            for_whom=for_whom,
            major_classification=major_classification,
            minor_classification=minor_classification,
        )
        record = db.TemporalExpenditure(data=data)
        self.temporal_expenditure_repository.put_item(record.model_dump())
        session: db.MessageSession = db.MessageSession(
            line_user_id=user_id,
            memo=record.id,
            type=db.MessageSession.SessionType.REGISTER_EXPENDITURE,
        )
        self.message_session_repository.put_item(session.model_dump())
        return self.message_repository.get_message("[register_receipt]")

    @to_message
    def handle_image_message(
        self, message: ImageMessageContent, user_id: str
    ) -> list[Message]:
        if message.image_set is not None and message.image_set.id is not None:
            return self.message_repository.get_message("[image_set_error]")

        session: db.MessageSession = self.message_session_repository.get_item(user_id)
        if session is not None:
            self.message_session_repository.delete_item(user_id)
            if session.type == db.MessageSession.SessionType.REGISTER_EXPENDITURE:
                record: db.TemporalExpenditure = (
                    self.temporal_expenditure_repository.get_item(session.memo)
                )
                record.line_image_id = message.id
        if record is None:
            user: db.User = self.user_repository.get_item(user_id)
            payer = "" if user is None else user.name
            data = uc.AccountBookInput(payer=payer)
            record = db.TemporalExpenditure(line_image_id=message.id, data=data)
        self.temporal_expenditure_repository.put_item(record.model_dump())
        send_message_to_sqs(record.id)

        return self.message_repository.get_recipt_confirm_message(record)

    @to_message
    def handle_postback_event(self, postback: PostbackContent) -> list[Message]:
        data: dict = json.loads(postback.data)
        match data["type"]:
            case uc.PostbackEventTypeEnum.REGISTER_EXPENDITURE:
                return self.__register_expenditure(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.RELOAD_STATUS:
                return self.__reload_status(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.CHANGE_CLASSIFICATION:
                classifications = (
                    self.item_classification_repository.get_all_major_to_minors_map()
                )
                return self.message_repository.get_change_classification_message(
                    uc.RegisterExpenditurePostback(**data), classifications
                )
            case uc.PostbackEventTypeEnum.UPDATE_CLASSIFICATION:
                return self.__update_classification(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.CHANGE_FOR_WHOM:
                users: list[db.User] = self.user_repository.get_all()
                return self.message_repository.get_change_for_whom_message(
                    uc.RegisterExpenditurePostback(**data), users
                )
            case uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM:
                return self.__update_for_whom(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.CHANGE_PAYER:
                users: list[db.User] = self.user_repository.get_all()
                return self.message_repository.get_change_payer_message(
                    uc.RegisterExpenditurePostback(**data), users
                )
            case uc.PostbackEventTypeEnum.UPDATE_PAYER:
                return self.__update_payer(uc.RegisterExpenditurePostback(**data))
            case uc.PostbackEventTypeEnum.UPDATE_DATE:
                return self.__update_date(
                    uc.RegisterExpenditurePostback(**data), postback.params["date"]
                )
            case uc.PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD:
                return self.message_repository.get_change_payment_method_message(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD:
                return self.__update_payment_method(
                    uc.RegisterExpenditurePostback(**data)
                )
            case uc.PostbackEventTypeEnum.CANCEL:
                return self.__cancel_expenditure(uc.RegisterExpenditurePostback(**data))
            case _:
                return self.message_repository.get_message("[postback_error]")

    def __register_expenditure(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        register_expenditure(record.data)
        self.temporal_expenditure_repository.delete_item(data.id)
        return self.message_repository.get_message("[register]")

    def __reload_status(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        return self.message_repository.get_recipt_confirm_message(record)

    def __update_date(
        self, data: uc.RegisterExpenditurePostback, date: str
    ) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        record = self.temporal_expenditure_repository.update_item(
            update_expression="SET #data.#date = :updated",
            expression_attribute_names={
                "#data": "data",
                "#date": "date",
            },
            expression_attribute_values={":updated": date},
            partition_key_value=record.id,
        )
        return self.message_repository.get_recipt_confirm_message(record)

    def __update_classification(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        major_classification = self.item_classification_repository.get_major(
            data.updated_item
        )
        record = self.temporal_expenditure_repository.update_item(
            update_expression="SET #data.#minor_classification = :updated_minor, #data.#major_classification = :updated_major",
            expression_attribute_names={
                "#data": "data",
                "#minor_classification": "minor_classification",
                "#major_classification": "major_classification",
            },
            expression_attribute_values={
                ":updated_minor": data.updated_item,
                ":updated_major": major_classification,
            },
            partition_key_value=record.id,
        )
        return self.message_repository.get_recipt_confirm_message(record)

    def __update_for_whom(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        record = self.temporal_expenditure_repository.update_item(
            update_expression="SET #data.#for_whom = :updated",
            expression_attribute_names={
                "#data": "data",
                "#for_whom": "for_whom",
            },
            expression_attribute_values={":updated": data.updated_item},
            partition_key_value=record.id,
        )
        return self.message_repository.get_recipt_confirm_message(record)

    def __update_payer(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        record = self.temporal_expenditure_repository.update_item(
            update_expression="SET #data.#payer = :updated",
            expression_attribute_names={
                "#data": "data",
                "#payer": "payer",
            },
            expression_attribute_values={":updated": data.updated_item},
            partition_key_value=record.id,
        )
        return self.message_repository.get_recipt_confirm_message(record)

    def __update_payment_method(
        self, data: uc.RegisterExpenditurePostback
    ) -> list[dict]:
        record: db.TemporalExpenditure = self.temporal_expenditure_repository.get_item(
            data.id
        )
        if record is None:
            return self.message_repository.get_message("[not_found_expenditure_error]")
        record = self.temporal_expenditure_repository.update_item(
            update_expression="SET #data.#payment_method = :updated",
            expression_attribute_names={
                "#data": "data",
                "#payment_method": "payment_method",
            },
            expression_attribute_values={
                ":updated": uc.PaymentMethodEnum.value_of(data.updated_item)
            },
            partition_key_value=record.id,
        )
        return self.message_repository.get_recipt_confirm_message(record)

    def __cancel_expenditure(self, data: uc.RegisterExpenditurePostback) -> list[dict]:
        self.temporal_expenditure_repository.delete_item(data.id)
        return self.message_repository.get_message("[cancel]")

    @to_message
    def handle_default_event(self) -> list[Message]:
        return self.message_repository.get_message("[message_not_found_error]")
