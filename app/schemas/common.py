"""Basi comuni agli schemi Pydantic."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Schema di lettura: sa costruirsi direttamente da un oggetto SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)
