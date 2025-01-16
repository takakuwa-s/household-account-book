from pydantic import BaseModel


class CommonModel(BaseModel):
    def get(self, field_name: str, default=None):
        value = getattr(self, field_name)
        if not value:
            return default
        return value
