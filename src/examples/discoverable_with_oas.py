#!/usr/bin/python3
from json import dumps

if __name__ == '__main__':
    import _extend_path

from mash.filesystem.discoverable import observe
from mash.object_parser.factory import JSONFactory
from mash.object_parser.oas import OAS, path_create
from mash.shell import ShellWithFileSystem

from examples.discoverable import Organization

if __name__ == '__main__':
    shell = ShellWithFileSystem(data={'repository': Organization},
                                get_value_method=observe)
    obj = shell.repository
    result = obj.ll()
    obj.init_home(['repository'])

    path = []
    result = 'departments'

    # for i in range(7):
    for i in range(7):
        k = result.split('\n')[-1]
        path.append(k)
        result = obj.ll(*path)

    json = JSONFactory(Organization).build(obj['repository'])
    oas = OAS()
    oas.extend(json)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    print(dumps(oas))
