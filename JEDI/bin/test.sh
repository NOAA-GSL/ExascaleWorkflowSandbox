#!/usr/bin/bash

for r in crtm femps fv3-jedi gsw ioda oops saber soca ufo ufo-data vader; do
  sbatch ctest.sh ${WORK} $r
done
