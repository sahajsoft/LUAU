#! /bin/bash

pip install sphinx sphinx_rtd_theme
cd docs
sphinx-apidoc -F -P -o . ../low_use
sphinx-apidoc -F -P -o . ../tagger
sphinx-apidoc -F -P -o . ../util
make html