from dataclasses import dataclass


@dataclass
class Environment:
    vars: dict
    funs: dict
