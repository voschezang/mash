from dataclasses import dataclass


@dataclass
class Environment:
    vars: dict
    funs: dict

    # def copy(self):
    #     return Environment(self.vars.copy(), self.funs.copy())
