#!/bin/bash

CONFFILE=$1
USER=root
TARGET_NAME=streamr-miner-keeper
WORKSPACE=/opt/streamr-miner-keeper

mkdir -p $WORKSPACE
cp streamr.py streamrlib.py $WORKSPACE
cp $CONFFILE $WORKSPACE/conf.json

PYTHON=`which python3`


cat << EOF > /lib/systemd/system/$TARGET_NAME.service
[Unit]
Description=Streamr Miner Keeper service
After=network.target

[Service]
WorkingDirectory=$WORKSPACE
ExecStart=$PYTHON streamr.py keeper conf.json
User=$USER

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /lib/systemd/system/$TARGET_NAME.timer
[Unit]
Description=Streamr Miner Keeper timer

[Timer]
OnCalendar=*-*-* 01/2:20:00
#OnCalendar=*-*-* *:0/30
Unit=$TARGET_NAME.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable "$TARGET_NAME.service"
systemctl enable "$TARGET_NAME.timer"
systemctl restart "$TARGET_NAME.timer"
