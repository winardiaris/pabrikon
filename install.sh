#!/bin/bash
NAMA=$1
KOMENTAR=$2
pwd=$('pwd')

wget https://github.com/winardiaris/pabrik-ikon/archive/master.zip
unzip master.zip
mkdir -p $pwd/$NAMA
cp -r pabrik-ikon-master/data $pwd/$NAMA/data
cp pabrik-ikon-master/index.theme $pwd/$NAMA
cp pabrik-ikon-master/pabrik.sh $pwd/$NAMA
cd $pwd/$NAMA
mkdir -p {actions,animations,apps,categories,devices,emblems,io,mimetypes,places,status,stock}/scalable
sed "s/nama-ikon/$NAMA/g ;s/komentar/$KOMENTAR/g" index.theme > index.themes
rm -rf index.theme
mv index.themes index.theme




rm -rf  master.zip
rm -rf pabrik-ikon-master

