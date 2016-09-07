#!/bin/bash

cd /tmp
wget https://github.com/winardiaris/pabrik-ikon/archive/dev-gui.zip
unzip dev-gui.zip
sudo mv pabrik-ikon-dev-gui /opt/pabrik-ikon
sudo ln -s /opt/pabrik-ikon/bin/pabrik.py /usr/local/bin/pabrik
echo "[info] instalation complete"
echo "type 'pabrik -h' for help the pabrik-ikon "
