#!/bin/bash

set -e

GIT_REVISION_COUNT=$(git rev-list HEAD --count)
GIT_COMMIT_HASH=$(git rev-parse --short HEAD)
BASE_FOLDER=$(pwd)
FULL_NAME="irrigation-controller_1.0-"$GIT_REVISION_COUNT"."$GIT_COMMIT_HASH

#Remove all previous deb packages
rm *.deb -f

#Create the control file from the template
cp control-template control
echo "Version: 1.0."$GIT_REVISION_COUNT >> control

#make sure the target package folder is removed
rm -rf $FULL_NAME

#create folder structure and enter folder
mkdir $FULL_NAME
cd $FULL_NAME

#create executables
mkdir -p ./usr/bin/
cp $BASE_FOLDER/../src/irrigator.py ./usr/bin/
cp $BASE_FOLDER/../src/valves.py ./usr/bin/

#create the init script
mkdir -p ./etc/init.d/
cp $BASE_FOLDER/../init.d/irrigator ./etc/init.d/

#create config files
mkdir -p ./etc/
cp $BASE_FOLDER/../config/irrigation-controller.yaml ./etc/

#create deb config file
mkdir -p ./DEBIAN/
cp $BASE_FOLDER/control ./DEBIAN/


#create the package
cd $BASE_FOLDER
dpkg-deb --build $FULL_NAME

#clean up the target folder 
rm -rf $FULL_NAME
