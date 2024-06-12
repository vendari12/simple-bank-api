from pydantic import BaseModel, model_validator


class BaseSchema(BaseModel):
    """Exposes a shared interface for request validations
       Do not use this class for schemas that return from the DB
       only those validating user request inputs

    Args:
        BaseModel (_type_): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    @model_validator(mode="before")
    @classmethod
    def validate_sql_injection_attack(cls, values):
        for key in values:
            value = values[key]
            if isinstance(value, str) and "delete from" in value.lower():
                raise ValueError("Our terms strictly prohobit SQLInjection Attacks")
        return values
