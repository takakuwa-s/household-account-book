from contextvars import ContextVar
from datetime import datetime
import json
from logging import config, Formatter, getLogger
from src.app.model.common_model import LogExtraInfo, LogMessage


class LogContext:
    context: ContextVar = ContextVar("logging_context", default=LogExtraInfo())

    @classmethod
    def set(
        cls,
        lambda_function_name: str = None,
        line_user_id: str = None,
        line_message_id: str = None,
        temporal_expenditure_id: str = None,
    ):
        """ログコンテキストを設定する"""
        info: LogExtraInfo = LogContext.context.get()
        if lambda_function_name:
            info.lambda_function_name = lambda_function_name
        if line_user_id:
            info.line_user_id = line_user_id
        if line_message_id:
            info.line_message_id = line_message_id
        if temporal_expenditure_id:
            info.temporal_expenditure_id = temporal_expenditure_id
        cls.context.set(info)


class CustomFormatter(Formatter):
    def format(self, record):
        """ログレコードのフォーマットをカスタマイズする
            参考: https://docs.python.org/ja/3.13/library/logging.html#logrecord-attributes
        Args:
            record (LogRecord): ログレコード
        Returns:
            str: フォーマット後のログメッセージ
        """
        info: LogExtraInfo = LogContext.context.get()
        # ログメッセージのモデルをJSON形式で作成
        message = LogMessage(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            file=record.filename,
            line=record.lineno,
            function=record.funcName,
            extra_info=info,
        )
        return message.model_dump_json(exclude_none=True)


def get_app_logger(name=None):
    """アプリケーション用のロガーを取得する
    Args:
        name (str): ロガー名
    Returns:
        Logger: ロガー
    """
    with open("./src/app/config/log_config.json", "r") as f:
        json_config = json.load(f)
    config.dictConfig(json_config)
    return getLogger(name)


if __name__ == "__main__":
    logger = get_app_logger(__name__)
    logger.info("test")
