#! /bin/bash

pip install sphinx sphinx_rtd_theme
cd doc_builder
sphinx-apidoc -F -P -o . ../low_use
sphinx-apidoc -F -P -o . ../tagger
sphinx-apidoc -F -P -o . ../util
make html
cd ../docs
mv html/*.* .
rm -rf html/