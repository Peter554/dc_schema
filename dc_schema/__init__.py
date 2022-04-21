from __future__ import annotations

import datetime
import enum
import dataclasses
import numbers
import typing as t


_MISSING = dataclasses.MISSING


def get_schema(dc):
    return _GetSchema()(dc)


_Format = t.Literal[
    "date-time",
    "time",
    "date",
    "duration",
    "email",
    "idn-email",
    "hostname",
    "idn-hostname",
    "ipv4",
    "ipv6",
    "uuid",
    "uri",
    "uri-reference",
    "iri",
    "iri-reference",
]


@dataclasses.dataclass(frozen=True)
class SchemaAnnotation:
    title: t.Optional[str] = None
    description: t.Optional[str] = None
    examples: t.Optional[list[t.Any]] = None
    deprecated: t.Optional[bool] = None
    min_length: t.Optional[int] = None
    max_length: t.Optional[int] = None
    pattern: t.Optional[str] = None
    format: t.Optional[_Format] = None
    minimum: t.Optional[numbers.Number] = None
    maximum: t.Optional[numbers.Number] = None
    exclusive_minimum: t.Optional[numbers.Number] = None
    exclusive_maximum: t.Optional[numbers.Number] = None
    multiple_of: t.Optional[numbers.Number] = None
    min_items: t.Optional[int] = None
    max_items: t.Optional[int] = None
    unique_items: t.Optional[bool] = None

    def schema(self):
        key_map = {
            "min_length": "minLength",
            "max_length": "maxLength",
            "exclusive_minimum": "exclusiveMinimum",
            "exclusive_maximum": "exclusiveMaximum",
            "multiple_of": "multipleOf",
            "min_items": "minItems",
            "max_items": "maxItems",
            "unique_items": "uniqueItems",
        }
        return {
            key_map.get(k, k): v
            for k, v in dataclasses.asdict(self).items()
            if v is not None
        }


class _GetSchema:
    def __call__(self, dc):
        self.root = dc
        self.seen_root = False

        self.defs = {}
        schema = self.get_dc_schema(dc, SchemaAnnotation())
        if self.defs:
            schema["$defs"] = self.defs

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            **schema,
        }

    def get_dc_schema(self, dc, annotation):
        if dc == self.root:
            if self.seen_root:
                return {"allOf": [{"$ref": "#"}], **annotation.schema()}
            else:
                self.seen_root = True
                schema = self.create_dc_schema(dc)
                return schema
        else:
            if dc.__name__ not in self.defs:
                schema = self.create_dc_schema(dc)
                self.defs[dc.__name__] = schema
            return {
                "allOf": [{"$ref": f"#/$defs/{dc.__name__}"}],
                **annotation.schema(),
            }

    def create_dc_schema(self, dc):
        if hasattr(dc, "SchemaConfig"):
            annotation = getattr(dc.SchemaConfig, "annotation", SchemaAnnotation())
        else:
            annotation = SchemaAnnotation()
        schema = {
            "type": "object",
            "title": dc.__name__,
            **annotation.schema(),
            "properties": {},
            "required": [],
        }
        type_hints = t.get_type_hints(dc, include_extras=True)
        for field in dataclasses.fields(dc):
            type_ = type_hints[field.name]
            schema["properties"][field.name] = self.get_field_schema(
                type_, field.default, SchemaAnnotation()
            )
            field_is_optional = (
                field.default is not _MISSING or field.default_factory is not _MISSING
            )
            if not field_is_optional:
                schema["required"].append(field.name)
        if not schema["required"]:
            schema.pop("required")
        return schema

    def get_field_schema(self, type_, default, annotation):
        if dataclasses.is_dataclass(type_):
            return self.get_dc_schema(type_, annotation)
        if t.get_origin(type_) == t.Union:
            return self.get_union_schema(type_, default, annotation)
        if t.get_origin(type_) == t.Literal:
            return self.get_literal_schema(type_, default, annotation)
        if t.get_origin(type_) == t.Annotated:
            return self.get_annotated_schema(type_, default)
        elif type_ == dict or t.get_origin(type_) == dict:
            return self.get_dict_schema(type_, annotation)
        elif type_ == list or t.get_origin(type_) == list:
            return self.get_list_schema(type_, annotation)
        elif type_ == tuple or t.get_origin(type_) == tuple:
            return self.get_tuple_schema(type_, default, annotation)
        elif type_ == set or t.get_origin(type_) == set:
            return self.get_set_schema(type_, annotation)
        elif type_ is None or type_ == type(None):
            return self.get_none_schema(default, annotation)
        elif type_ == str:
            return self.get_str_schema(default, annotation)
        elif type_ == bool:
            return self.get_bool_schema(default, annotation)
        elif type_ == int:
            return self.get_int_schema(default, annotation)
        elif issubclass(type_, numbers.Number):
            return self.get_number_schema(default, annotation)
        elif issubclass(type_, enum.Enum):
            return self.get_enum_schema(type_, default, annotation)
        elif issubclass(type_, datetime.datetime):
            return self.get_datetime_schema(annotation)
        elif issubclass(type_, datetime.date):
            return self.get_date_schema(annotation)
        else:
            raise NotImplementedError(f"field type '{type_}' not implemented")

    def get_union_schema(self, type_, default, annotation):
        args = t.get_args(type_)
        if default is _MISSING:
            return {
                "anyOf": [
                    self.get_field_schema(arg, _MISSING, SchemaAnnotation())
                    for arg in args
                ],
                **annotation.schema(),
            }
        else:
            return {
                "anyOf": [
                    self.get_field_schema(arg, _MISSING, SchemaAnnotation())
                    for arg in args
                ],
                "default": default,
                **annotation.schema(),
            }

    def get_literal_schema(self, type_, default, annotation):
        if default is _MISSING:
            schema = {**annotation.schema()}
        else:
            schema = {"default": default, **annotation.schema()}
        args = t.get_args(type_)
        return {"enum": list(args), **schema}

    def get_dict_schema(self, type_, annotation):
        args = t.get_args(type_)
        assert len(args) in (0, 2)
        if args:
            assert args[0] == str
            return {
                "type": "object",
                "additionalProperties": self.get_field_schema(
                    args[1], _MISSING, SchemaAnnotation()
                ),
                **annotation.schema(),
            }
        else:
            return {"type": "object", **annotation.schema()}

    def get_list_schema(self, type_, annotation):
        args = t.get_args(type_)
        assert len(args) in (0, 1)
        if args:
            return {
                "type": "array",
                "items": self.get_field_schema(args[0], _MISSING, SchemaAnnotation()),
                **annotation.schema(),
            }
        else:
            return {"type": "array", **annotation.schema()}

    def get_tuple_schema(self, type_, default, annotation):
        if default is _MISSING:
            schema = {**annotation.schema()}
        else:
            schema = {"default": list(default), **annotation.schema()}
        args = t.get_args(type_)
        if args and len(args) == 2 and args[1] is ...:
            schema = {
                "type": "array",
                "items": self.get_field_schema(args[0], _MISSING, SchemaAnnotation()),
                **schema,
            }
        elif args:
            schema = {
                "type": "array",
                "prefixItems": [
                    self.get_field_schema(arg, _MISSING, SchemaAnnotation())
                    for arg in args
                ],
                "minItems": len(args),
                "maxItems": len(args),
                **schema,
            }
        else:
            schema = {"type": "array", **schema}
        return schema

    def get_set_schema(self, type_, annotation):
        args = t.get_args(type_)
        assert len(args) in (0, 1)
        if args:
            return {
                "type": "array",
                "items": self.get_field_schema(args[0], _MISSING, SchemaAnnotation()),
                "uniqueItems": True,
                **annotation.schema(),
            }
        else:
            return {"type": "array", "uniqueItems": True, **annotation.schema()}

    def get_none_schema(self, default, annotation):
        if default is _MISSING:
            return {"type": "null", **annotation.schema()}
        else:
            return {"type": "null", "default": default, **annotation.schema()}

    def get_str_schema(self, default, annotation):
        if default is _MISSING:
            return {"type": "string", **annotation.schema()}
        else:
            return {"type": "string", "default": default, **annotation.schema()}

    def get_bool_schema(self, default, annotation):
        if default is _MISSING:
            return {"type": "boolean", **annotation.schema()}
        else:
            return {"type": "boolean", "default": default, **annotation.schema()}

    def get_int_schema(self, default, annotation):
        if default is _MISSING:
            return {"type": "integer", **annotation.schema()}
        else:
            return {"type": "integer", "default": default, **annotation.schema()}

    def get_number_schema(self, default, annotation):

        if default is _MISSING:
            return {"type": "number", **annotation.schema()}
        else:
            return {"type": "number", "default": default, **annotation.schema()}

    def get_enum_schema(self, type_, default, annotation):
        if type_.__name__ not in self.defs:
            self.defs[type_.__name__] = {
                "title": type_.__name__,
                "enum": [v.value for v in type_],
            }
        if default is _MISSING:
            return {
                "allOf": [{"$ref": f"#/$defs/{type_.__name__}"}],
                **annotation.schema(),
            }
        else:
            return {
                "allOf": [{"$ref": f"#/$defs/{type_.__name__}"}],
                "default": default.value,
                **annotation.schema(),
            }

    def get_annotated_schema(self, type_, default):
        args = t.get_args(type_)
        assert len(args) == 2
        return self.get_field_schema(args[0], default, args[1])

    def get_datetime_schema(self, annotation):
        return {"type": "string", "format": "date-time", **annotation.schema()}

    def get_date_schema(self, annotation):
        return {"type": "string", "format": "date", **annotation.schema()}
