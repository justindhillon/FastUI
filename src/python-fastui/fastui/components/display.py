import enum
import typing as _t
from abc import ABC

import annotated_types as _at
import pydantic
import typing_extensions as _te

from .. import class_name as _class_name
from .. import events

__all__ = 'DisplayMode', 'DisplayLookup', 'Display', 'Details'


class DisplayMode(str, enum.Enum):
    auto = 'auto'  # default, same as None below
    plain = 'plain'
    datetime = 'datetime'
    date = 'date'
    duration = 'duration'
    as_title = 'as_title'
    markdown = 'markdown'
    json = 'json'
    inline_code = 'inline_code'


class DisplayBase(pydantic.BaseModel, ABC, defer_build=True):
    mode: _t.Union[DisplayMode, None] = None
    title: _t.Union[str, None] = None
    on_click: _t.Union[events.AnyEvent, None] = pydantic.Field(default=None, serialization_alias='onClick')


class DisplayLookup(DisplayBase, extra='forbid'):
    """
    Description of how to display a value looked up from data, either in a table or detail view.
    """

    field: str
    # percentage width - 0 to 100, specific to tables
    table_width_percent: _t.Union[_te.Annotated[int, _at.Interval(ge=0, le=100)], None] = pydantic.Field(
        default=None, serialization_alias='tableWidthPercent'
    )


class Display(DisplayBase, extra='forbid'):
    """
    Description of how to display a value, either in a table or detail view.
    """

    value: _t.Any = pydantic.Field(None, json_schema_extra={'type': 'JSON'})
    type: _t.Literal['Display'] = 'Display'


DataModel = _t.TypeVar('DataModel', bound=pydantic.BaseModel)


class Details(pydantic.BaseModel, _t.Generic[DataModel], extra='forbid'):
    data: DataModel
    fields: _t.Union[_t.List[DisplayLookup], None] = None
    class_name: _class_name.ClassNameField = None
    type: _t.Literal['Details'] = 'Details'

    @pydantic.model_validator(mode='after')
    def fill_fields(self) -> _te.Self:
        if self.fields is None:
            self.fields = [
                DisplayLookup(field=name, title=field.title) for name, field in self.data.model_fields.items()
            ]
        else:
            # add pydantic titles to fields that don't have them
            for field in (c for c in self.fields if c.title is None):
                pydantic_field = self.data.model_fields.get(field.field)
                if pydantic_field and pydantic_field.title:
                    field.title = pydantic_field.title
        return self
