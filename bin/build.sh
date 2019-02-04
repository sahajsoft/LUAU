#!/bin/bash
if [ -d "build" ]; then
    rm -rf build
fi 
find . | grep -E "(.pytest_cache|__pycache__|\.pyc|\.pyo)" | xargs rm -rf

virtualenv venv
source venv/bin/activate

pip install -r requirements.txt

python3 -m pytest --cov=tagger --cov=util --cov=low_use 

if [ $? ==  1 ]; then
    rm -rf venv
    exit 1
fi

PYTHON_SITE_PACKAGE_DIR=$(python -c "import os; print(os.path.dirname(os.__file__) + '/site-packages')")
deactivate

mkdir build
find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
cp -r tagger build
cp -r util build
cp -r low_use build

#PYTHON_SITE_PACKAGE_DIR=$(python -c "import os; print(os.path.dirname(os.__file__) + '/site-packages')")
echo $PYTHON_SITE_PACKAGE_DIR
find $PYTHON_SITE_PACKAGE_DIR | grep -E "(moto|mock|pytest|pytest_cov|coverage)" | xargs rm -rf
cp -r $PYTHON_SITE_PACKAGE_DIR/* build/

cd build 
zip -r LUAUTagger.zip .
cd ..
mv build/LUAUTagger.zip ./LUAUTagger.zip

rm -rf venv
rm -rf build
find . | grep -E "(.pytest_cache|__pycache__|\.pyc|\.pyo)" | xargs rm -rf