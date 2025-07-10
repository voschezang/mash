#!/bin/bash
set -e

out='docs/source/modules'
github='https://github.com/voschezang/mash/blob/main/'

(
cd ..

echo -e '# Examples\n' > ${out}/mash_examples.md

# generate links for each file

for file in src/examples/[a-z][a-z_]*.py; do
  echo "- [$file](${github}${file})" >> ${out}/mash_examples.md
done

)
