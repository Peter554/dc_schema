import argparse
import json

from dc_schema import get_schema


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "file_path", help="The path to the python file containing the dataclass"
    )
    arg_parser.add_argument(
        "dataclass", help="The name of the dataclass to generate the schema"
    )
    args = arg_parser.parse_args()

    exec(open(args.file_path).read(), locals())

    schema = get_schema(locals()[args.dataclass])
    print(json.dumps(schema, indent=2), end=None)
