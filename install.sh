#!/bin/bash

sudo git clone https://github.com/winardiaris/pabrikon.git /opt/pabrikon
sudo ln -s /opt/pabrikon/bin/pabrikon.py /usr/local/bin/pabrikon
echo "[info] instalation complete"
echo "type 'pabrikon -h' for help the pabrikon "
