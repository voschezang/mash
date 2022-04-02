from src.object_parser_example import example_data, Organization
from src.oas import OAS

json = example_data

members = {'type': 'array',
           'items': {'type': 'string'}}
team_type = {'type': 'string', 'enum': ['A', 'B']}
properties = {'manager': {'type': 'string'},
              'members': members,
              'team_type': team_type,
              'active': {'type': 'boolean'}
              }


def test_oas_component():
    oas = OAS()
    org = Organization(json)
    team = org.departments[0].teams[0]
    oas.extend(team)
    components = oas.components

    assert components['Team']['description'] == team.__doc__
    assert components['Team']['type'] == 'object'
    assert components['Team']['properties']['members'] == members
    assert components['Team']['properties']['team_type'] == team_type
    assert components['Team']['properties'] == properties
    assert components == {'Team': {'description': team.__doc__,
                                   'type': 'object',
                                   'properties': properties
                                   }
                          }


def test_oas_components():
    org = Organization(json)
    oas = OAS()
    department = org.departments[0]
    team = org.departments[0].teams[0]
    oas.extend(department)

    assert oas.components['Team'] == {'description': team.__doc__,
                                      'type': 'object',
                                      'properties': properties
                                      }

    teams = {'type': 'array',
             'items': {'$ref': '#/components/schemas/Team'}}
    assert oas.components['Department']['properties']['teams'] == teams
