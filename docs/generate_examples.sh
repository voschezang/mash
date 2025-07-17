#!/bin/bash
set -e

out='docs/source/generated/mash_examples.md'
github='https://github.com/voschezang/mash/blob/main/'

(
cd ..

echo -e '# Examples\n' > ${out}

# generate links for each file

for file in src/examples/[a-z][a-z_]*.py; do
  echo "- [$file](${github}${file})" >> ${out}
done

)
