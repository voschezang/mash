"""Generate a OAS/Swagger component
See: [OAS](https://swagger.io/specification/)
"""
from typing import _GenericAlias

from mash.object_parser.spec import Spec
from mash.util import is_enum


# OAS basic types, excluding containers  (e.g. dict, list)
basic_value_type = {
    bool: 'boolean',
    complex: 'string',
    float: 'number',
    int: 'integer',
    str: 'string',
}


class K:
    """OAS keys
    """
    components = 'components'
    schemas = 'schemas'
    props = 'properties'
    doc = 'description'


class V:
    """OAS values
    """
    @staticmethod
    def ref(item=''):
        return f'#/components/schemas/{item}'


template = {
    'openapi': '3.0.1',
    'info': {
        'title': 'My API',
        'version': '1.0.0',
        K.doc: ''
    },
    'servers': [{'url': 'https://example.com/v1'}],
    'paths': {},
    K.components: {K.schemas: {}}
}


def path_create(item_type: str, verb='POST', ):
    verb = verb.lower()
    return {verb:
            {'operationId': verb + item_type,
             'requestBody': {'content': {'application/json':
                                         {'schema': oas_ref(item_type)}},
                             'required': True},
             'responses': {405: {'description': 'Invalid input'}}}}


class OAS(dict):
    """A key-value map that represents an OAS.
    It that can be converted to JSON or YAML and viewed in:
    https://editor.swagger.io/
    """

    def __init__(self, *args, **kwds):
        super().__init__(template.copy())

    @property
    def components(self):
        return self[K.components][K.schemas]

    def extend(self, obj: object):
        """Generate OAS/Swagger components from a class
        See: [OAS](https://swagger.io/specification/)
        E.g.
        ```yml
        components:
            schemas:
                User:
                    properties:
                        id:
                            type: integer
                        name:
                            type: string
        ```
        """
        t = type(obj).__name__
        if t not in self.components:
            self.components[t] = oas_component(obj)

        if not hasattr(obj, '__annotations__'):
            return

        for k in obj.__annotations__:
            try:
                v = getattr(obj, k)
            except AttributeError as e:
                e
            v = getattr(obj, k)
            item_type = infer_oas_type(v)

            if isinstance(v, Spec):
                self.extend(v)
                self.components[t][K.props][k] = oas_ref(item_type)

            elif is_enum(type(v)):
                # use strings rather than enum.value
                item_type = infer_oas_type('')
                values = [e.name for e in type(v)]
                self.components[t][K.props][k] = {
                    'type': item_type,
                    'enum': values
                }

            elif type(v) in basic_value_type.keys():
                self.components[t][K.props][k] = {'type': item_type}

            elif isinstance(v, _GenericAlias) or isinstance(v, list):
                for child in v:
                    self.add_array(t, k, child)

            elif item_type == 'dict':
                for child in v.values():
                    self.add_array(t, k, child)
            else:
                self.extend(v)
                self.components[t][K.props][k] = oas_ref(item_type)

    def add_array(self, parent_name: str, child_name: str, child):
        item_type = infer_oas_type(child)
        if isinstance(child, Spec) or not has_known_type(child):
            self.extend(child)
            item = oas_ref(item_type)
        else:
            item = {'type': item_type}

        self.components[parent_name][K.props][child_name] = {
            'type': 'array',
                    'items': item
        }


def oas_component(obj: Spec, doc=''):
    if not doc and obj.__doc__:
        doc = obj.__doc__.strip()

    result = {K.doc: doc}
    if isinstance(obj, Spec) or hasattr(obj, '__dataclass_fields__'):
        result['type'] = 'object'
        result[K.props] = {}

    else:
        result['type'] = infer_oas_type('')

    return result


def oas_ref(item=''):
    return {'$ref': f'#/components/schemas/{item}'}


def has_known_type(obj):
    return type(obj) in basic_value_type


def infer_oas_type(obj):
    obj_type = type(obj)
    try:
        return basic_value_type[obj_type]
    except KeyError:
        return obj_type.__name__
