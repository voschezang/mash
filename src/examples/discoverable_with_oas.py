#!/usr/bin/python3
from json import dumps

if __name__ == '__main__':
    import _extend_path  # noqa

from mash.filesystem.discoverable import observe
from mash.object_parser.factory import JSONFactory
from mash.object_parser.oas import OAS, path_create
from mash.shell import ShellWithFileSystem

from examples.discoverable import Organization


def main() -> str:
    shell = ShellWithFileSystem(data={'repository': Organization},
                                get_value_method=observe)
    obj = shell.repository
    result = obj.ll()
    obj.init_home(['repository'])

    path = []
    result = 'departments'

    for i in range(6):
        key = result.split('\n')[-1]
        path.append(key)
        result = obj.ll(*path)

    json = JSONFactory(Organization).build(obj)
    oas = OAS()
    oas.extend(json)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    return oas


if __name__ == '__main__':
    oas = main()
    print(dumps(oas))
