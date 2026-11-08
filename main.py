from datetime import date, datetime
from pathlib import Path
from typing import Literal
from unicodedata import name
from uuid import uuid4

from fastapi import FastAPI
from pydantic import (
    BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator,
)


app = FastAPI(title="Обращения абонентов")
DATA_DIR = Path(__file__).resolve().parent / "requests"

Reason = Literal["нет доступа к сети", "не работает телефон", "не приходят письма"]


class SubscriberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_name: str
    first_name: str
    birth_date: date
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    email: EmailStr
    reasons: list[Reason] | None = Field(default=None, min_length=1)
    detected_at: datetime | None = None

    @field_validator("last_name", "first_name")
    @classmethod
    def check_name(cls, value: str) -> str:
        if not value or not value[0].isupper() or any(
            not char.isalpha() or not name(char, "").startswith("CYRILLIC ")
            for char in value
        ):
            raise ValueError("Нужны только кириллические буквы, первая — заглавная.")
        return value

    @field_validator("birth_date")
    @classmethod
    def check_birth_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Дата рождения не может быть в будущем.")
        return value

    @field_validator("birth_date", mode="before")
    @classmethod
    def check_date_format(cls, value):
        if not isinstance(value, str) or len(value) != 10 or value[4] != "-" or value[7] != "-":
            raise ValueError("Укажите дату рождения в формате ГГГГ-ММ-ДД.")
        return value

    @field_validator("detected_at", mode="before")
    @classmethod
    def require_time(cls, value):
        if value is not None and (
            not isinstance(value, str) or len(value) < 16 or value[10] != "T"
        ):
            raise ValueError("Укажите дату и время в формате ГГГГ-ММ-ДДTчч:мм.")
        return value

    @model_validator(mode="after")
    def check_problem_details(self):
        if (self.reasons is None) != (self.detected_at is None):
            raise ValueError("Укажите причины и время обнаружения вместе.")
        return self


@app.post("/requests/", status_code=201)
def create_request(request: SubscriberRequest):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{uuid4().hex}.json"
    path.write_text(
        request.model_dump_json(indent=2, exclude_unset=True), encoding="utf-8"
    )
    return {"file": path.name}
