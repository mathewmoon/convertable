import json
from typing import Any

import jq
import toml
import yaml


class Parser:
    loaders = {
        "json": json.loads,
        "yaml": yaml.safe_load,
        "toml": toml.loads,
    }
    dumpers = {
        "json": json.dumps,
        "yaml": yaml.dump,
        "toml": toml.dumps,
    }

    def __init__(
        self,
        data: str | None = None,
        filepath: str | None = None,
        data_type: str = "json",
    ):

        if not data and not filepath:
            raise ValueError("Must provide either data or a filepath.")

        self.data_type = data_type

        try:
            self.loader = self.loaders[self.data_type]
        except KeyError:
            raise ValueError(f"Invalid data type: {data_type}")

        self.filepath = filepath

        self._data = self.load_file(filepath) if self.filepath else self.loader(data)

    @property
    def data(self) -> dict:
        return self._data

    def load_file(self, filepath: str, /, **optargs) -> dict | list:
        with open(filepath, "r") as f:
            return self.loader(f, **optargs)

    def dump(self, data_type: str, expression: str = "", **optargs) -> str:
        if expression and expression != ".":
            data = self.jq_parse(expression)
        else:
            data = self.data
        try:
            dumper = self.dumpers[data_type]
        except KeyError:
            raise ValueError(f"Invalid data type: {data_type}")

        return dumper(data, **optargs)

    def jq_parse(self, expression: str) -> Any:
        """
        Applies a user-supplied expression to the JSON data
        """

        data = jq.compile(expression).input_value(self.data).text()
        res = json.loads(data)

        return res
