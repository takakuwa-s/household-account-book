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
from src.app.adaptor.google_sheets_api_adaptor import (
    register_expenditure,
    register_only_total,
)
from src.app.adaptor.sqs_adaptor import send_message_to_sqs, send_messages_to_sqs
from src.app.model import (
    db_model as db,
    usecase_model as uc,
)
from src.app.repository.item_classifications_repository import (
    ItemClassificationsRepository,
)
from src.app.repository.messages_repository import MessagesRepository
from src.app.repository.message_sessions_repository import (
    MessageSessionsRepository,
)
from src.app.repository.temporal_expenditures_repository import (
    TemporalExpendituresRepository,
)
from src.app.repository.image_sets_repository import (
    ImageSetsRepository,
)
from src.app.repository.users_reposioty import UsersRepository

# DynamoDBリソースの作成
dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


class HundleLineMessageUsecase:
    def __init__(self):
        self.item_classifications_repository = ItemClassificationsRepository(dynamodb)
        self.temporal_expenditures_repository = TemporalExpendituresRepository(dynamodb)
        self.users_repository = UsersRepository(dynamodb)
        self.message_sessions_repository = MessageSessionsRepository(dynamodb)
        self.image_sets_repository = ImageSetsRepository(dynamodb)
        self.message_repository = MessagesRepository()

    def to_message(function):
        def _wrapper(*args, **keywords):
            self = args[0]
            try:
                messages = function(*args, **keywords)
            except Exception as e:
                messages = self.message_repository.get_error_message(e)
                traceback.print_exc()
            if messages:
                return [Message.from_dict(m) for m in messages]
            return None

        return _wrapper

    @to_message
    def group_message(self) -> list[Message]:
        return self.message_repository.get_message("[group_error]")

    @to_message
    def handle_follow_event(self, user_id: str) -> list[Message]:
        profile: UserProfileResponse = fetch_user_profile(user_id)
        user: db.User = db.User(line_user_id=user_id, line_name=profile.display_name)
        self.users_repository.put_item(user.model_dump())
        return self.message_repository.get_follow_message(user.line_name)

    @to_message
    def handle_text_message(
        self, message: TextMessageContent, user_id: str
    ) -> list[Message]:
        session: db.MessageSession = self.message_sessions_repository.get_item(user_id)
        if session is not None:
            self.message_sessions_repository.delete_item(user_id)
            match session.type:
                case db.MessageSession.SessionType.REGISTER_USER:
                    user: db.User = self.users_repository.get_item(user_id)
                    user.name = message.text
                    self.users_repository.put_item(user.model_dump())
                    return self.message_repository.get_register_user_message(
                        message.text, user.line_name
                    )
        if message.text == uc.KeywordsEnum.REGISTER_USER.value:
            session: db.MessageSession = db.MessageSession(line_user_id=user_id)
            self.message_sessions_repository.put_item(session.model_dump())
            return self.message_repository.get_start_user_registration_message()
        elif message.text == uc.KeywordsEnum.GET_TEMPORALLY_EXPENDITURES.value:
            records: list[db.TemporalExpenditure] = (
                self.temporal_expenditures_repository.get_all_by_line_user_id(user_id)
            )
            return self.message_repository.get_temporal_expenditure_list(records)
        elif uc.KeywordsEnum.is_for_register_receipt(message.text):
            major_classification, minor_classification, is_common_for_whom = (
                uc.KeywordsEnum.get_setting_from_keyword(message.text)
            )
            return self.__set_default_expenditure_setting(
                user_id, major_classification, minor_classification, is_common_for_whom
            )
        else:
            return self.message_repository.get_message(message.text)

    def __set_default_expenditure_setting(
        self,
        user_id: str,
        major_classification: str,
        minor_classification: str,
        is_common_for_whom: bool,
    ) -> list[dict]:
        user: db.User = self.users_repository.get_item(user_id)
        payer = "" if user is None else user.name
        for_whom = "共通" if is_common_for_whom else payer
        data = uc.AccountBookInput(
            payer=payer,
            for_whom=for_whom,
            major_classification=major_classification,
            minor_classification=minor_classification,
        )
        record = db.TemporalExpenditure(data=data, line_user_id=user_id)
        self.temporal_expenditures_repository.put_item(record.model_dump())
        session: db.MessageSession = db.MessageSession(
            line_user_id=user_id,
            temporal_expenditure_id=record.id,
            type=db.MessageSession.SessionType.REGISTER_EXPENDITURE,
        )
        self.message_sessions_repository.put_item(session.model_dump())
        return self.message_repository.get_message("[register_receipt]")

    @to_message
    def handle_image_message(
        self, message: ImageMessageContent, user_id: str
    ) -> list[Message]:
        # NOTE: 画像が複数枚の場合
        if message.image_set is not None and message.image_set.id is not None:
            image_set: db.ImageSet = self.image_sets_repository.get_item(
                message.image_set.id
            )
            if image_set is None:
                image_set = db.ImageSet(
                    image_set_id=message.image_set.id,
                    total=message.image_set.total,
                    image_meta_data=[
                        db.ImageSet.ImageMetaData(line_image_id=message.id)
                    ],
                )
                self.image_sets_repository.put_item(image_set.model_dump())
                return
            else:
                image_set.image_meta_data.append(
                    db.ImageSet.ImageMetaData(line_image_id=message.id)
                )
                self.image_sets_repository.put_item(image_set.model_dump())
                if len(image_set.image_meta_data) != image_set.total:
                    return

        # NOTE: セッションが存在する場合、セッションを削除し、かつTemporalExpenditureを取得（あれば）
        # - 登録方法に指定がある場合が該当。
        record = None
        session: db.MessageSession = self.message_sessions_repository.get_item(user_id)
        if session is not None:
            self.message_sessions_repository.delete_item(user_id)
            if (
                session.type == db.MessageSession.SessionType.REGISTER_EXPENDITURE
                and session.temporal_expenditure_id is not None
            ):
                record: db.TemporalExpenditure = (
                    self.temporal_expenditures_repository.get_item(
                        session.temporal_expenditure_id
                    )
                )
                record.line_image_id = message.id
                record.status = db.TemporalExpenditure.Status.ANALYZING

        # NOTE: 元々登録方法に指定がなかった場合、処理用にTemporalExpenditureを作成
        if record is None:
            user: db.User = self.users_repository.get_item(user_id)
            payer = "" if user is None else user.name
            data = uc.AccountBookInput(payer=payer)
            record = db.TemporalExpenditure(
                line_image_id=message.id,
                line_user_id=user_id,
                data=data,
                status=db.TemporalExpenditure.Status.ANALYZING,
            )

        # NOTE: 画像が複数の場合と一枚の場合を分けて処理する
        if message.image_set is not None and message.image_set.id is not None:
            record.image_set_id = message.image_set.id
            records = [record.model_dump()]
            temporal_expenditure_ids = [record.id]
            for data in image_set.image_meta_data:
                if data.line_image_id == message.id:
                    continue
                another_record = db.TemporalExpenditure.from_another(record)
                another_record.line_image_id = data.line_image_id
                records.append(another_record.model_dump())
                temporal_expenditure_ids.append(another_record.id)
            self.temporal_expenditures_repository.batch_write_items(records)
            send_messages_to_sqs(temporal_expenditure_ids)
        else:
            self.temporal_expenditures_repository.put_item(record.model_dump())
            send_message_to_sqs(record.id)
        return self.message_repository.get_reciept_analysis_message(
            record.id, record.status
        )

    @to_message
    def handle_postback_event(
        self, postback: PostbackContent, user_id: str
    ) -> list[Message]:
        data_dict: dict = json.loads(postback.data)
        if data_dict["type"] == uc.PostbackEventTypeEnum.CANCEL_USER_REGISTRATION:
            self.message_sessions_repository.delete_item(user_id)
            return self.message_repository.get_message("[cancel_user_registration]")
        elif uc.PostbackEventTypeEnum.is_for_receipt_registration(data_dict["type"]):
            data = uc.RegisterExpenditurePostback(**data_dict)
            record: db.TemporalExpenditure = (
                self.temporal_expenditures_repository.get_item(data.id)
            )
            if record is None:
                return self.message_repository.get_message(
                    "[not_found_expenditure_error]"
                )
            match data_dict["type"]:
                case uc.PostbackEventTypeEnum.REGISTER_EXPENDITURE:
                    register_expenditure(record.data)
                    self.temporal_expenditures_repository.delete_item(data.id)
                    return self.message_repository.get_message("[register]")
                case uc.PostbackEventTypeEnum.REGISTER_ONLY_TOTAL:
                    register_only_total(record.data)
                    self.temporal_expenditures_repository.delete_item(data.id)
                    return self.message_repository.get_message("[register_only_total]")
                case uc.PostbackEventTypeEnum.DETAIL_EXPENDITURE:
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.CHANGE_CLASSIFICATION:
                    classifications = self.item_classifications_repository.get_all_major_to_minors_map()
                    return self.message_repository.get_change_classification_message(
                        data, classifications
                    )
                case uc.PostbackEventTypeEnum.UPDATE_CLASSIFICATION:
                    major_classification = (
                        self.item_classifications_repository.get_major(
                            data.updated_item
                        )
                    )
                    record = (
                        self.temporal_expenditures_repository.update_classification(
                            id=record.id,
                            minar_classification=data.updated_item,
                            major_classification=major_classification,
                        )
                    )
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.CHANGE_FOR_WHOM:
                    users: list[db.User] = self.users_repository.get_all()
                    return self.message_repository.get_change_for_whom_message(
                        data, users
                    )
                case uc.PostbackEventTypeEnum.UPDATE_FOR_WHOM:
                    record = self.temporal_expenditures_repository.update_for_whom(
                        id=record.id, for_whom=data.updated_item
                    )
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.CHANGE_PAYER:
                    users: list[db.User] = self.users_repository.get_all()
                    return self.message_repository.get_change_payer_message(data, users)
                case uc.PostbackEventTypeEnum.UPDATE_PAYER:
                    record = self.temporal_expenditures_repository.update_payer(
                        id=record.id, payer=data.updated_item
                    )
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.UPDATE_DATE:
                    record = self.temporal_expenditures_repository.update_date(
                        record.id, postback.params["date"]
                    )
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.CHANGE_PAYMENT_METHOD:
                    return self.message_repository.get_change_payment_method_message(
                        data
                    )
                case uc.PostbackEventTypeEnum.UPDATE_PAYMENT_METHOD:
                    record = (
                        self.temporal_expenditures_repository.update_payment_method(
                            id=record.id, payment_method=data.updated_item
                        )
                    )
                    return self.message_repository.get_reciept_confirm_message(record)
                case uc.PostbackEventTypeEnum.DELETE_UNREGISTEED_EXPENDITURE:
                    self.temporal_expenditures_repository.delete_item(data.id)
                    return self.message_repository.get_message(
                        "[delete_unregisterrd_expenditure]"
                    )
        else:
            return self.message_repository.get_message("[postback_error]")

    @to_message
    def handle_default_event(self) -> list[Message]:
        return self.message_repository.get_message("[message_not_found_error]")
