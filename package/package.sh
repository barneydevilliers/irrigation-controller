#!/bin/bash

set -e

GIT_REVISION_COUNT=$(git rev-list HEAD --count)
GIT_COMMIT_HASH=$(git rev-parse --short HEAD)
BASE_FOLDER=$(pwd)
FULL_NAME="irrigation-controller_1.0-"$GIT_REVISION_COUNT"."$GIT_COMMIT_HASH

#make sure the target package folder is removed
rm -rf $FULL_NAME

#create folder structure and enter folder
mkdir $FULL_NAME
cd $FULL_NAME

#create executables
mkdir -p ./usr/bin/
cp $BASE_FOLDER/../src/irrigator.py ./usr/bin/

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
