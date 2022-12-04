import yaml

from mash.html_table import example_yaml_data, generate
from mash.html_table_data import parse_json

expected_html = """
<table>
  <tr>
    <th><p><em>First</em> Heading</p>
</th>
    <th><p><em>Last</em> Heading</p>
</th>
  </tr>
  <tbody>
    <tr>
      <td rowspan="2"><p>A value</p>
</td>
      <td><p>Option B</p>
</td>
    </tr>
    <tr>
      <td><p>Option C</p>
</td>
    </tr>
  </tbody>
  <tbody>
    <tr>
      <td rowspan="2"><p>Another value</p>
</td>
      <td><p>Option D</p>
</td>
    </tr>
    <tr>
      <td><p>Option E</p>
</td>
    </tr>
  </tbody>
</table>
"""


def test_html_table_generate():
    json = yaml.load(example_yaml_data, yaml.Loader)
    data = parse_json(json)
    doc = generate(data)

    body = str(doc.body.children[1]).strip()
    assert body == expected_html.strip()
