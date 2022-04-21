# dc_schema

[![CI](https://github.com/Peter554/dc_schema/actions/workflows/ci.yaml/badge.svg)](https://github.com/Peter554/dc_schema/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/Peter554/dc_schema/branch/master/graph/badge.svg?token=YLT3N0HWO9)](https://codecov.io/gh/Peter554/dc_schema)

Tiny library to generate [JSON schema](https://json-schema.org/) (2020-12) from python 
[dataclasses](https://docs.python.org/3/library/dataclasses.html). No other dependencies, standard library only.

```
pip install dc-schema 
```

## Assumptions

* python 3.9+ 

## Motivation

Create a lightweight, focused solution to generate JSON schema from plain dataclasses. [pydantic](https://pydantic-docs.helpmanual.io/) is a much more mature option, however it also does a lot of other things I didn't want to include here. Deepen my understanding of python dataclasses, typing and JSON schema.

## Usage

### Basics

Create a regular python dataclass and pass it to `get_schema`.

```py
import dataclasses
import datetime
import json

from dc_schema import get_schema

@dataclasses.dataclass
class Book:
    title: str
    published: bool = False

@dataclasses.dataclass
class Author:
    name: str
    age: int
    dob: datetime.date
    books: list[Book]

print(json.dumps(get_schema(Author), indent=2))
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "title": "Author",
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "integer"
    },
    "dob": {
      "type": "string",
      "format": "date"
    },
    "books": {
      "type": "array",
      "items": {
        "allOf": [
          {
            "$ref": "#/$defs/Book"
          }
        ]
      }
    }
  },
  "required": [
    "name",
    "age",
    "dob",
    "books"
  ],
  "$defs": {
    "Book": {
      "type": "object",
      "title": "Book",
      "properties": {
        "title": {
          "type": "string"
        },
        "published": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "title"
      ]
    }
  }
}
```

### Annotations

You can use [typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated) + `SchemaAnnotation` to attach
metadata to the schema, such as field descriptions, examples, validation (min/max length, regex pattern, ...), etc. 
Consult [the code](https://github.com/Peter554/dc_schema/blob/master/dc_schema/__init__.py) for full details.

```py
import dataclasses
import datetime
import json
import typing as t

from dc_schema import get_schema, SchemaAnnotation

@dataclasses.dataclass
class Author:
    name: t.Annotated[str, SchemaAnnotation(title="Full name", description="The authors full name")]
    age: t.Annotated[int, SchemaAnnotation(minimum=0)]
    dob: t.Annotated[t.Optional[datetime.date], SchemaAnnotation(examples=["1990-01-17"])] = None

print(json.dumps(get_schema(Author), indent=2))
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "title": "Author",
  "properties": {
    "name": {
      "type": "string",
      "title": "Full name",
      "description": "The authors full name"
    },
    "age": {
      "type": "integer",
      "minimum": 0
    },
    "dob": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "examples": [
        "1990-01-17"
      ]
    }
  },
  "required": [
    "name",
    "age"
  ]
}
```

To customize the metadata of a dataclass itself, use a `SchemaConfig`.

```py
import dataclasses
import json

from dc_schema import get_schema, SchemaAnnotation

@dataclasses.dataclass
class User:
    name: str

    class SchemaConfig:
        annotation = SchemaAnnotation(title="System user", description="A user of the system")

print(json.dumps(get_schema(User), indent=2))
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "title": "System user",
  "description": "A user of the system",
  "properties": {
    "name": {
      "type": "string"
    }
  },
  "required": [
    "name"
  ]
}
```

### Further examples

See the [tests](https://github.com/Peter554/dc_schema/blob/master/tests/test_dc_schema.py) for full example usage.

## CLI

```
dc_schema <file_path> <dataclass>
```

e.g.

```
dc_schema ./schema.py Author
```

## Other tools

For working with dataclasses or JSON schema:

* https://github.com/konradhalas/dacite - create data classes from dictionaries.
* https://python-jsonschema.readthedocs.io/en/stable/ - validate an object against a JSON schema.
* https://json-schema.org/understanding-json-schema/index.html - nice reference for understanding JSON schema. 
