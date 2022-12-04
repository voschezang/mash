from examples.object_parser_example import SuperUser, example_data, Organization, Capacity
from mash.object_parser.oas import OAS

json = example_data

members = {'type': 'array',
           'items': {'type': 'string'}}
stakeholders = {'type': 'array',
                'items': {'$ref': '#/components/schemas/SuperUser'}}
team_type = {'type': 'string', 'enum': ['A', 'B']}
properties = {'manager': {'type': 'string'},
              'members': members,
              'stakeholders': stakeholders,
              'team_type': team_type,
              'active': {'type': 'boolean'},
              'capacity': {'$ref': '#/components/schemas/Capacity'},
              'value': {'type': 'number'},
              'secret': {'type': 'string'}
              }


def test_oas_component():
    oas = OAS()
    org = Organization(json)
    team = org.departments[0].teams[0]
    oas.extend(team)
    components = oas.components

    assert components['Team']['description'] == team.__doc__.strip()
    assert components['Team']['type'] == 'object'
    assert components['Team']['properties']['members'] == members
    assert components['Team']['properties']['team_type'] == team_type
    assert components['Team']['properties'] == properties
    assert components == {'Team': {'description': team.__doc__.strip(),
                                   'type': 'object',
                                   'properties': properties
                                   },
                          'SuperUser': {'description': SuperUser.__doc__.strip(),
                                        'type': 'string'},
                          'Capacity': {'description': Capacity.__doc__.strip(),
                                       'type': 'string'}
                          }


def test_oas_components():
    org = Organization(json)
    oas = OAS()
    department = org.departments[0]
    team = org.departments[0].teams[0]
    oas.extend(department)

    assert oas.components['Team'] == {'description': team.__doc__.strip(),
                                      'type': 'object',
                                      'properties': properties
                                      }

    teams = {'type': 'array',
             'items': {'$ref': '#/components/schemas/Team'}}
    assert oas.components['Department']['properties']['teams'] == teams
