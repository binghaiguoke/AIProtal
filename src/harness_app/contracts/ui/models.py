from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MessageFactItem(BaseModel):
    label: str
    value: str


class MessageAction(BaseModel):
    id: str
    label: str
    message: str = ""
    variant: str = "primary"
    payload: dict[str, str] = Field(default_factory=dict)


class MessageFormField(BaseModel):
    name: str
    label: str
    kind: Literal["text", "textarea"] = "text"
    placeholder: str = ""
    required: bool = False
    value: str = ""


class MessageProcessStep(BaseModel):
    title: str
    detail: str = ""
    status: str = "pending"


class MessagePartText(BaseModel):
    type: Literal["text"] = "text"
    text: str


class MessagePartCard(BaseModel):
    type: Literal["card"] = "card"
    title: str
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    facts: list[MessageFactItem] = Field(default_factory=list)


class MessagePartActions(BaseModel):
    type: Literal["actions"] = "actions"
    title: str = ""
    description: str = ""
    actions: list[MessageAction] = Field(default_factory=list)


class MessagePartForm(BaseModel):
    type: Literal["form"] = "form"
    title: str
    description: str = ""
    submit_label: str = "提交"
    fields: list[MessageFormField] = Field(default_factory=list)


class MessagePartProcess(BaseModel):
    type: Literal["process"] = "process"
    title: str = "过程信息"
    steps: list[MessageProcessStep] = Field(default_factory=list)


MessagePart = Annotated[
    MessagePartText | MessagePartCard | MessagePartActions | MessagePartForm | MessagePartProcess,
    Field(discriminator="type"),
]


class StructuredMessageEnvelope(BaseModel):
    reply: str = ""
    parts: list[MessagePart] = Field(default_factory=list)
