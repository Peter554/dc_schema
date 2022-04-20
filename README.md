# dataclass_schema

Generate [JSON schema](https://json-schema.org/) (2020-12) from python 
[dataclasses](https://docs.python.org/3/library/dataclasses.html). No dependencies, standard library only.

```
pip install dataclass_schema 
```

## Assumptions

* python 3.9+
* [`from __future__ import annotations`](https://peps.python.org/pep-0563/)

## Usage

### Basics

Create a regular python dataclass and pass it to `get_schema`.

```py
from __future__ import annotations

import dataclasses
import datetime
import json

from dataclass_schema.dataclass_schema import get_schema


@dataclasses.dataclass
class Author:
    name: str
    age: int
    dob: datetime.date
    books: list[Book]

@dataclasses.dataclass
class Book:
    title: str
    published: bool = False

print(json.dumps(get_schema(Author), indent=2))
```

```
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

You can use [typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated) + `annotation` to attach
metadata to the schema, such as field descriptions, examples, validation (min/max length, regex pattern, ...), etc. 
Consult [the code](https://github.com/Peter554/dataclass_schema/blob/master/dataclass_schema/dataclass_schema.py) for full details.

```py
from __future__ import annotations

import dataclasses
import datetime
import json
import typing as t

from dataclass_schema.dataclass_schema import get_schema, annotation


@dataclasses.dataclass
class Author:
    name: t.Annotated[str, annotation(title="Full name", description="The authors full name")]
    age: t.Annotated[int, annotation(minimum=0)]
    dob: t.Annotated[t.Optional[datetime.date], annotation(examples=["1990-01-17"])] = None

print(json.dumps(get_schema(Author), indent=2))
```

```
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

### Further examples

See the [tests](https://github.com/Peter554/dataclass_schema/blob/master/tests/test_dataclass_schema.py) for full example usage.


## Other tools

For working with dataclasses or JSON schema:

* https://python-jsonschema.readthedocs.io/en/stable/ - validate an object against a JSON schema.
* https://github.com/konradhalas/dacite - create data classes from dictionaries.