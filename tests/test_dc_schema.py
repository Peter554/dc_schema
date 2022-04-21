from __future__ import annotations

import datetime
import dataclasses
import typing as t
import enum

from jsonschema.validators import Draft202012Validator

from dc_schema import (
    get_schema,
    annotation,
)


@dataclasses.dataclass
class DcPrimitives:
    b: bool
    i: int
    f: float
    s: str


def test_get_schema_primitives():
    schema = get_schema(DcPrimitives)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcPrimitives",
        "properties": {
            "b": {"type": "boolean"},
            "i": {"type": "integer"},
            "f": {"type": "number"},
            "s": {"type": "string"},
        },
        "required": ["b", "i", "f", "s"],
    }


@dataclasses.dataclass
class DcOptional:
    a: int = 42
    b: int = dataclasses.field(default=42)
    c: int = dataclasses.field(default_factory=lambda: 42)
    d: str = "foo"
    e: bool = False
    f: None = None
    g: float = 1.1
    h: tuple[int, float] = (1, 1.1)


def test_get_schema_optional_fields():
    """optional field === field with a default (!== t.Optional)"""
    schema = get_schema(DcOptional)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcOptional",
        "properties": {
            "a": {"type": "integer", "default": 42},
            "b": {"type": "integer", "default": 42},
            "c": {"type": "integer"},
            "d": {"type": "string", "default": "foo"},
            "e": {"type": "boolean", "default": False},
            "f": {"type": "null", "default": None},
            "g": {"type": "number", "default": 1.1},
            "h": {
                "type": "array",
                "prefixItems": [{"type": "integer"}, {"type": "number"}],
                "minItems": 2,
                "maxItems": 2,
                "default": [1, 1.1],
            },
        },
    }


@dataclasses.dataclass
class DcUnion:
    a: t.Union[int, str]


def test_get_schema_union():
    schema = get_schema(DcUnion)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcUnion",
        "properties": {"a": {"anyOf": [{"type": "integer"}, {"type": "string"}]}},
        "required": ["a"],
    }


@dataclasses.dataclass
class DcNone:
    a: None
    b: t.Optional[int]
    c: t.Union[None, int]


def test_get_schema_nullable():
    schema = get_schema(DcNone)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcNone",
        "properties": {
            "a": {"type": "null"},
            "b": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "c": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
        },
        "required": ["a", "b", "c"],
    }


@dataclasses.dataclass
class DcDict:
    a: dict
    b: dict[str, int]


def test_get_schema_dict():
    schema = get_schema(DcDict)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcDict",
        "properties": {
            "a": {"type": "object"},
            "b": {"type": "object", "additionalProperties": {"type": "integer"}},
        },
        "required": ["a", "b"],
    }


@dataclasses.dataclass
class DcList:
    a: list
    b: list[bool]


def test_get_schema_list():
    schema = get_schema(DcList)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcList",
        "properties": {
            "a": {"type": "array"},
            "b": {"type": "array", "items": {"type": "boolean"}},
        },
        "required": ["a", "b"],
    }


@dataclasses.dataclass
class DcTuple:
    a: tuple
    b: tuple[int, ...]
    c: tuple[int, bool, str]


def test_get_schema_tuple():
    schema = get_schema(DcTuple)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcTuple",
        "properties": {
            "a": {"type": "array"},
            "b": {"type": "array", "items": {"type": "integer"}},
            "c": {
                "type": "array",
                "prefixItems": [
                    {"type": "integer"},
                    {"type": "boolean"},
                    {"type": "string"},
                ],
                "minItems": 3,
                "maxItems": 3,
            },
        },
        "required": ["a", "b", "c"],
    }


@dataclasses.dataclass
class DcRefsChild:
    c: str


@dataclasses.dataclass
class DcRefs:
    a: DcRefsChild
    b: list[DcRefsChild]


def test_get_schema_refs():
    schema = get_schema(DcRefs)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcRefs",
        "properties": {
            "a": {"allOf": [{"$ref": "#/$defs/DcRefsChild"}]},
            "b": {
                "type": "array",
                "items": {"allOf": [{"$ref": "#/$defs/DcRefsChild"}]},
            },
        },
        "required": ["a", "b"],
        "$defs": {
            "DcRefsChild": {
                "type": "object",
                "title": "DcRefsChild",
                "properties": {"c": {"type": "string"}},
                "required": ["c"],
            }
        },
    }


@dataclasses.dataclass
class DcRefsSelf:
    a: str
    b: t.Optional[DcRefsSelf]
    c: list[DcRefsSelf]


def test_get_schema_self_refs():
    schema = get_schema(DcRefsSelf)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcRefsSelf",
        "properties": {
            "a": {"type": "string"},
            "b": {"anyOf": [{"allOf": [{"$ref": "#"}]}, {"type": "null"}]},
            "c": {"type": "array", "items": {"allOf": [{"$ref": "#"}]}},
        },
        "required": ["a", "b", "c"],
    }


@dataclasses.dataclass
class DcLiteral:
    a: t.Literal[1, "two", 3, None]
    b: t.Literal[42, 43] = 42


def test_get_schema_literal():
    schema = get_schema(DcLiteral)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcLiteral",
        "properties": {
            "a": {"enum": [1, "two", 3, None]},
            "b": {"enum": [42, 43], "default": 42},
        },
        "required": ["a"],
    }


class MyEnum(enum.Enum):
    a = enum.auto()
    b = enum.auto()


@dataclasses.dataclass
class DcEnum:
    a: MyEnum
    b: MyEnum = MyEnum.a


def test_get_schema_enum():
    schema = get_schema(DcEnum)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcEnum",
        "properties": {
            "a": {"allOf": [{"$ref": "#/$defs/MyEnum"}]},
            "b": {"allOf": [{"$ref": "#/$defs/MyEnum"}], "default": 1},
        },
        "required": ["a"],
        "$defs": {"MyEnum": {"title": "MyEnum", "enum": [1, 2]}},
    }


@dataclasses.dataclass
class DcSet:
    a: set
    b: set[int]


def test_get_schema_set():
    schema = get_schema(DcSet)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcSet",
        "properties": {
            "a": {"type": "array", "uniqueItems": True},
            "b": {"type": "array", "items": {"type": "integer"}, "uniqueItems": True},
        },
        "required": ["a", "b"],
    }


@dataclasses.dataclass
class DcStrAnnotated:
    a: t.Annotated[str, annotation(min_length=3, max_length=5)]
    b: t.Annotated[str, annotation(format_="date", pattern=r"^\d.*")] = "2000-01-01"


def test_get_schema_str_annotation():
    schema = get_schema(DcStrAnnotated)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcStrAnnotated",
        "properties": {
            "a": {"type": "string", "minLength": 3, "maxLength": 5},
            "b": {
                "type": "string",
                "default": "2000-01-01",
                "pattern": "^\\d.*",
                "format": "date",
            },
        },
        "required": ["a"],
    }


@dataclasses.dataclass
class DcNumberAnnotated:
    a: t.Annotated[int, annotation(minimum=1, exclusive_maximum=11)]
    b: list[t.Annotated[int, annotation(minimum=0)]]
    c: t.Optional[t.Annotated[int, annotation(minimum=0)]]
    d: t.Annotated[
        float, annotation(maximum=12, exclusive_minimum=17, multiple_of=5)
    ] = 33.1


def test_get_schema_number_annotation():
    schema = get_schema(DcNumberAnnotated)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcNumberAnnotated",
        "properties": {
            "a": {"type": "integer", "minimum": 1, "exclusiveMaximum": 11},
            "b": {"type": "array", "items": {"type": "integer", "minimum": 0}},
            "c": {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]},
            "d": {
                "type": "number",
                "default": 33.1,
                "maximum": 12,
                "exclusiveMinimum": 17,
                "multipleOf": 5,
            },
        },
        "required": ["a", "b", "c"],
    }


@dataclasses.dataclass
class DcDateTime:
    a: datetime.datetime
    b: datetime.date


def test_get_schema_date_time():
    schema = get_schema(DcDateTime)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcDateTime",
        "properties": {
            "a": {"type": "string", "format": "date-time"},
            "b": {"type": "string", "format": "date"},
        },
        "required": ["a", "b"],
    }


@dataclasses.dataclass
class DcAnnotatedBook:
    title: t.Annotated[str, annotation(title="Title")]


class DcAnnotatedAuthorHobby(enum.Enum):
    CHESS = "chess"
    SOCCER = "soccer"


@dataclasses.dataclass
class DcAnnotatedAuthor:
    name: t.Annotated[
        str,
        annotation(description="the name of the author", examples=["paul", "alice"]),
    ]
    books: t.Annotated[
        list[DcAnnotatedBook],
        annotation(description="all the books the author has written"),
    ]
    hobby: t.Annotated[DcAnnotatedAuthorHobby, annotation(deprecated=True)]
    age: t.Annotated[t.Union[int, float], annotation(description="age in years")] = 42


def test_get_schema_annotation():
    schema = get_schema(DcAnnotatedAuthor)
    print(schema)
    Draft202012Validator.check_schema(schema)
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": "DcAnnotatedAuthor",
        "properties": {
            "name": {
                "type": "string",
                "description": "the name of the author",
                "examples": ["paul", "alice"],
            },
            "books": {
                "type": "array",
                "items": {"allOf": [{"$ref": "#/$defs/DcAnnotatedBook"}]},
                "description": "all the books the author has written",
            },
            "hobby": {
                "allOf": [{"$ref": "#/$defs/DcAnnotatedAuthorHobby"}],
                "deprecated": True,
            },
            "age": {
                "anyOf": [{"type": "integer"}, {"type": "number"}],
                "default": 42,
                "description": "age in years",
            },
        },
        "required": ["name", "books", "hobby"],
        "$defs": {
            "DcAnnotatedBook": {
                "type": "object",
                "title": "DcAnnotatedBook",
                "properties": {"title": {"type": "string", "title": "Title"}},
                "required": ["title"],
            },
            "DcAnnotatedAuthorHobby": {
                "title": "DcAnnotatedAuthorHobby",
                "enum": ["chess", "soccer"],
            },
        },
    }
