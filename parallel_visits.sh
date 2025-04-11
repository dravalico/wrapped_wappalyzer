#!/bin/bash

DOMAINSFILE=$1
OUTFILE=$2
PROCESSES=$3

if [ $# -ne 3 ]; then
    echo "usage: $0 domainsfile outfile processes"
    exit 1
fi

cat $DOMAINSFILE | parallel -j $PROCESSES --progress "docker run --rm --cpus=1 --memory=3g --platform=linux/amd64 dravalico/wrapped-wappalyzer:1.0 --url {}" > $OUTFILE