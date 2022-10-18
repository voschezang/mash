"""Generate a OAS/Swagger component
See: [OAS](https://swagger.io/specification/)
"""

from object_parser.object_parser import Spec, is_enum
from typing import _GenericAlias

translations = {
    int: 'integer',
    float: 'number',
    str: 'string',
    bool: 'boolean',
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
        # return f'$ref: #/components/schemas/{item}'
        return f'#/components/schemas/{item}'
        # return {'$ref': '#/components/schemas/{item}'}


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

    @ property
    def components(self):
        return self[K.components][K.schemas]

    def extend(self, obj: Spec):
        """Generate OAS/Swagger components from a Spec
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

            elif isinstance(v, _GenericAlias) or isinstance(v, list):
                child = v[0]
                item_type = infer_oas_type(child)
                if isinstance(child, Spec):
                    self.extend(child)
                    item = oas_ref(item_type)
                else:
                    item = {'type': infer_oas_type(child)}

                self.components[t][K.props][k] = {
                    'type': 'array',
                    'items': item
                }

            elif type(v) not in translations.keys():
                self.extend(v)
                self.components[t][K.props][k] = oas_ref(item_type)

            else:
                self.components[t][K.props][k] = {'type': item_type}


def oas_component(obj: Spec, doc=''):
    if not doc and obj.__doc__:
        doc = obj.__doc__.strip()

    result = {K.doc: doc}
    if isinstance(obj, Spec):
        result['type'] = 'object'
        result[K.props] = {}

    else:
        result['type'] = infer_oas_type('')

    return result


def oas_ref(item=''):
    return {'$ref': f'#/components/schemas/{item}'}


def infer_oas_type(obj):
    obj_type = type(obj)
    try:
        return translations[obj_type]
    except KeyError:
        return obj_type.__name__
