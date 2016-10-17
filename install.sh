#!/bin/bash

cd /tmp
wget https://github.com/winardiaris/pabrikon/archive/master.zip
unzip master.zip
sudo mv pabrikon-master /opt/pabrikon
sudo ln -s /opt/pabrikon/bin/pabrikon.py /usr/local/bin/pabrikon
echo "[info] instalation complete"
echo "type 'pabrikon -h' for help the pabrikon "
