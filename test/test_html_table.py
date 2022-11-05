from pytest import raises
import yaml

from html_table import example_yaml_data, generate, verify_table_data

expected_html = """
<table>
  <tr>
    <th>First Heading</th>
    <th>Last Heading</th>
  </tr>
  <tbody>
    <tr>
      <td rowspan="2">A value</td>
      <td>Option B</td>
    </tr>
    <tr>
      <td>Option C</td>
    </tr>
  </tbody>
  <tbody>
    <tr>
      <td rowspan="2">Another value</td>
      <td>Option D</td>
    </tr>
    <tr>
      <td>Option E</td>
    </tr>
  </tbody>
</table>
"""


def test_html_table_verify_data():
    data = yaml.load(example_yaml_data, yaml.Loader)

    verify_table_data(data)

    del data['parameters']
    with raises(AssertionError):
        verify_table_data(data)


def test_html_table_generate():
    data = yaml.load(example_yaml_data, yaml.Loader)
    doc = generate(data)
    body = str(doc.body.children[1]).strip()
    assert body == expected_html.strip()
