from __future__ import annotations

import datetime
import enum
import json
import dataclasses
import numbers
import typing as t


MISSING = dataclasses.MISSING


def get_schema(dc):
    return _GetSchema()(dc)


Format = t.Literal[
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


def annotation(
    *,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    examples: t.Optional[list[t.Any]] = None,
    deprecated: t.Optional[bool] = None,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
    pattern: t.Optional[str] = None,
    format_: t.Optional[Format] = None,
    minimum: t.Optional[numbers.Number] = None,
    maximum: t.Optional[numbers.Number] = None,
    exclusive_minimum: t.Optional[numbers.Number] = None,
    exclusive_maximum: t.Optional[numbers.Number] = None,
    multiple_of: t.Optional[numbers.Number] = None,
):
    extra = {
        "title": title,
        "description": description,
        "examples": examples,
        "deprecated": deprecated,
        "minLength": min_length,
        "maxLength": max_length,
        "pattern": pattern,
        "format": format_,
        "minimum": minimum,
        "maximum": maximum,
        "exclusiveMinimum": exclusive_minimum,
        "exclusiveMaximum": exclusive_maximum,
        "multipleOf": multiple_of,
    }
    extra = {k: v for k, v in extra.items() if v is not None}
    return json.dumps(extra)


class _GetSchema:
    def __call__(self, dc):
        self.root = dc
        self.seen_root = False

        self.defs = {}
        schema = self.get_dc_schema(dc, None)
        if self.defs:
            schema["$defs"] = self.defs

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            **schema,
        }

    def get_dc_schema(self, dc, extra):
        extra = json.loads(extra) if extra else {}
        if dc == self.root:
            if self.seen_root:
                return {"allOf": [{"$ref": "#"}], **extra}
            else:
                self.seen_root = True
                schema = self.create_dc_schema(dc)
                return schema
        else:
            if dc.__name__ not in self.defs:
                schema = self.create_dc_schema(dc)
                self.defs[dc.__name__] = schema
            return {"allOf": [{"$ref": f"#/$defs/{dc.__name__}"}], **extra}

    def create_dc_schema(self, dc):
        schema = {
            "type": "object",
            "title": dc.__name__,
            "properties": {},
            "required": [],
        }
        type_hints = t.get_type_hints(dc, include_extras=True)
        for field in dataclasses.fields(dc):
            type_ = type_hints[field.name]
            schema["properties"][field.name] = self.get_field_schema(
                type_, field.default, None
            )
            field_is_optional = (
                field.default is not MISSING or field.default_factory is not MISSING
            )
            if not field_is_optional:
                schema["required"].append(field.name)
        if not schema["required"]:
            schema.pop("required")
        return schema

    def get_field_schema(self, type_, default, extra):
        if dataclasses.is_dataclass(type_):
            return self.get_dc_schema(type_, extra)
        if t.get_origin(type_) == t.Union:
            return self.get_union_schema(type_, default, extra)
        if t.get_origin(type_) == t.Literal:
            return self.get_literal_schema(type_, default, extra)
        if t.get_origin(type_) == t.Annotated:
            return self.get_annotated_schema(type_, default)
        elif type_ == dict or t.get_origin(type_) == dict:
            return self.get_dict_schema(type_, extra)
        elif type_ == list or t.get_origin(type_) == list:
            return self.get_list_schema(type_, extra)
        elif type_ == tuple or t.get_origin(type_) == tuple:
            return self.get_tuple_schema(type_, default, extra)
        elif type_ == set or t.get_origin(type_) == set:
            return self.get_set_schema(type_, extra)
        elif type_ is None or type_ == type(None):
            return self.get_none_schema(default, extra)
        elif type_ == str:
            return self.get_str_schema(default, extra)
        elif type_ == bool:
            return self.get_bool_schema(default, extra)
        elif type_ == int:
            return self.get_int_schema(default, extra)
        elif issubclass(type_, numbers.Number):
            return self.get_number_schema(default, extra)
        elif issubclass(type_, enum.Enum):
            return self.get_enum_schema(type_, default, extra)
        elif issubclass(type_, datetime.datetime):
            return self.get_datetime_schema(extra)
        elif issubclass(type_, datetime.date):
            return self.get_date_schema(extra)
        else:
            raise NotImplementedError(f"field type '{type_}' not implemented")

    def get_union_schema(self, type_, default, extra):
        extra = json.loads(extra) if extra else {}
        args = t.get_args(type_)
        if default is MISSING:
            return {
                "anyOf": [self.get_field_schema(arg, MISSING, None) for arg in args],
                **extra,
            }
        else:
            return {
                "anyOf": [self.get_field_schema(arg, MISSING, None) for arg in args],
                "default": default,
                **extra,
            }

    def get_literal_schema(self, type_, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            schema = {**extra}
        else:
            schema = {"default": default, **extra}
        args = t.get_args(type_)
        return {"enum": list(args), **schema}

    def get_dict_schema(self, type_, extra):
        extra = json.loads(extra) if extra else {}
        args = t.get_args(type_)
        assert len(args) in (0, 2)
        if args:
            assert args[0] == str
            return {
                "type": "object",
                "additionalProperties": self.get_field_schema(args[1], MISSING, None),
                **extra,
            }
        else:
            return {"type": "object", **extra}

    def get_list_schema(self, type_, extra):
        extra = json.loads(extra) if extra else {}
        args = t.get_args(type_)
        assert len(args) in (0, 1)
        if args:
            return {
                "type": "array",
                "items": self.get_field_schema(args[0], MISSING, None),
                **extra,
            }
        else:
            return {"type": "array", **extra}

    def get_tuple_schema(self, type_, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            schema = {**extra}
        else:
            schema = {"default": list(default), **extra}
        args = t.get_args(type_)
        if args and len(args) == 2 and args[1] is ...:
            schema = {
                "type": "array",
                "items": self.get_field_schema(args[0], MISSING, None),
                **schema,
            }
        elif args:
            schema = {
                "type": "array",
                "prefixItems": [
                    self.get_field_schema(arg, MISSING, None) for arg in args
                ],
                "minItems": len(args),
                "maxItems": len(args),
                **schema,
            }
        else:
            schema = {"type": "array", **schema}
        return schema

    def get_set_schema(self, type_, extra):
        extra = json.loads(extra) if extra else {}
        args = t.get_args(type_)
        assert len(args) in (0, 1)
        if args:
            return {
                "type": "array",
                "items": self.get_field_schema(args[0], MISSING, None),
                "uniqueItems": True,
                **extra,
            }
        else:
            return {"type": "array", "uniqueItems": True, **extra}

    def get_none_schema(self, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            return {"type": "null", **extra}
        else:
            return {"type": "null", "default": default, **extra}

    def get_str_schema(self, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            return {"type": "string", **extra}
        else:
            return {"type": "string", "default": default, **extra}

    def get_bool_schema(self, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            return {"type": "boolean", **extra}
        else:
            return {"type": "boolean", "default": default, **extra}

    def get_int_schema(self, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            return {"type": "integer", **extra}
        else:
            return {"type": "integer", "default": default, **extra}

    def get_number_schema(self, default, extra):
        extra = json.loads(extra) if extra else {}
        if default is MISSING:
            return {"type": "number", **extra}
        else:
            return {"type": "number", "default": default, **extra}

    def get_enum_schema(self, type_, default, extra):
        extra = json.loads(extra) if extra else {}
        if type_.__name__ not in self.defs:
            self.defs[type_.__name__] = {
                "title": type_.__name__,
                "enum": [v.value for v in type_],
            }
        if default is MISSING:
            return {"allOf": [{"$ref": f"#/$defs/{type_.__name__}"}], **extra}
        else:
            return {
                "allOf": [{"$ref": f"#/$defs/{type_.__name__}"}],
                "default": default.value,
                **extra,
            }

    def get_annotated_schema(self, type_, default):
        args = t.get_args(type_)
        assert len(args) == 2
        return self.get_field_schema(args[0], default, args[1])

    def get_datetime_schema(self, extra):
        extra = json.loads(extra) if extra else {}
        return {"type": "string", "format": "date-time", **extra}

    def get_date_schema(self, extra):
        extra = json.loads(extra) if extra else {}
        return {"type": "string", "format": "date", **extra}
