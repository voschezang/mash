from dataclasses import dataclass

Environment = dict


@dataclass
class Environment2:
    vars: dict
    funs: dict

    # def copy(self):
    #     return Environment(self.vars.copy(), self.funs.copy())
