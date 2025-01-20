from typing import Optional
from pydantic import BaseModel, Field


class CommonModel(BaseModel):
    def get(self, field_name: str, default=None):
        value = getattr(self, field_name)
        if not value:
            return default
        return value


class LogExtraInfo(CommonModel):
    line_user_id: Optional[str] = Field(default=None)
    line_message_id: Optional[str] = Field(default=None)
    temporal_expenditure_id: Optional[str] = Field(default=None)

    def __str__(self):
        json_str = self.model_dump_json(exclude_none=True)
        # もし何もセットされていなければ、json_str = {} となる
        if len(json_str) == 2:
            return ""
        return f" context: {json_str}"


class LogMessage(CommonModel):
    timestamp: str = Field(default="")
    level: str = Field(default="")
    message: str = Field(default="")
    file: str = Field(default="")
    line: int = Field(default=None)
    function: str = Field(default="")
    extra_info: LogExtraInfo = LogExtraInfo()
