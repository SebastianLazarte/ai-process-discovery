"""HTTP contracts for the process template catalog (RS-95).

A template holds names, descriptions and the qualitative traits of each step. It never carries
minutes, rates, executions or an hourly cost: the person types every number for their company.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas.process import MAX_STEPS, LongText, StepTraits

Slug = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProcessTemplate(_Schema):
    slug: Slug
    name: str = Field(min_length=1, max_length=200)
    description: LongText = ""
    steps: list[StepTraits] = Field(min_length=1, max_length=MAX_STEPS)


class SectorTemplates(_Schema):
    id: Slug
    name: str = Field(min_length=1, max_length=200)
    templates: list[ProcessTemplate] = Field(min_length=1)
