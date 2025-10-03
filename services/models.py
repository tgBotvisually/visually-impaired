from typing import List, Optional
from pydantic import BaseModel


class ItemOption(BaseModel):
    id: str
    label: str


class Validation(BaseModel):
    type: str


class ConditionItem(BaseModel):
    type: str
    operator: Optional[str] = None
    condition: Optional[str] = None
    question: Optional[str] = None
    value: Optional[str] = None


class Condition(BaseModel):
    operator: str
    items: List[ConditionItem]


class FormItem(BaseModel):
    id: str
    label: str
    hidden: bool
    type: str
    widget: Optional[str] = None
    items: Optional[List[ItemOption]] = None
    validations: Optional[List[Validation]] = None
    conditions: Optional[List[Condition]] = None
    multiline: Optional[bool] = None


class Page(BaseModel):
    items: List[FormItem]


class Texts(BaseModel):
    submit: str
    back: str
    next: str


class FormData(BaseModel):
    id: str
    name: str
    teaser: bool
    footer: bool
    iframe: bool
    texts: Texts
    pages: List[Page]
