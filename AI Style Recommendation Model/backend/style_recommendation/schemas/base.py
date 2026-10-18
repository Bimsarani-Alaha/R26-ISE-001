"""Support both the gateway's Pydantic 1 and standalone Pydantic 2."""
from pydantic import BaseModel as PydanticBaseModel

if hasattr(PydanticBaseModel, "model_validate"):
    from pydantic import ConfigDict, field_validator

    BaseModel = PydanticBaseModel

    class RequestModel(BaseModel):
        model_config = ConfigDict(str_strip_whitespace=True)
else:
    from pydantic import validator as field_validator

    class BaseModel(PydanticBaseModel):
        @classmethod
        def model_validate(cls, data):
            return cls.parse_obj(data)

        def model_dump(self, **kwargs):
            return self.dict(**kwargs)

    class RequestModel(BaseModel):
        class Config:
            anystr_strip_whitespace = True
