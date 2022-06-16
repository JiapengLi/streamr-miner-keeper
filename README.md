# Streamr Miner Keeper

Run **Streamr Miner Keeper** periodically to keep your streamr miner node healthy. **STOP MISSING REWARD CLAIM!**  

After involved in streamr project, I found that the miner node sometimes stops working after days or weeks running, and a restart can always fix the issue. So it comes to the idea, that you can monitor the node stats, when it stops claiming rewards, trigger docker container  restart command automatically.

## Features

- Fetch last claim time through streamr API (10 threads at the same time)
- Auto login host machine through SSH and trigger fix command if the nodes stops claim rewards (docker restart $container_name)
- Push result to DingTalk (leave `dingtalkkey` an empty string to disable it)

## Configuration

Before installation create your own configuration file.

```
{
    "sshkey": "/ed25519/key/file/path",
    "hosts":[
        { "name": "xx", "address": "xx.domain.name", "user": "username", "port": 22 },
        {}
    ],
    "miners":[
        { "id": "000", "pubkey": "0xa123......", "host": "hostname_in_host_list", "container": "streamr", "command": "auto" },
        {}
    ],
    "dingtalkkey": ""
}
```

- `sshkey` : SSH key file path, use absolute path (only ed25519 format key file is supported)
- `hosts`: host list
  - `name`: host name, must be list unique
  - `address`: ip or domain name
  - `user`: ssh user name
  - `port`: ssh port
  - `sshkey`: (optional) omit to use the common `sshkey`
- `miners`: miner list
  - `id`: miner name
  - `pubkey`: miner public key
  - `host`: host name in host list, the same as the name in hosts list
  - `container`: docker container name, use to auto generate miner restart command 
  - `command`: set `auto` to generate `sudo docker restart $container` command

## Installation

First, install python3 dependencies.

```
sudo pip3 install fire paramiko
```

Specify configure file and run `install.sh` to deploy.

```
sudo ./install.sh $conf_file
```

- `/opt/streamr-miner-keeper`: workspace
- `/lib/systemd/system/streamr-miner-keeper.service`: systemd service
- `/lib/systemd/system/streamr-miner-keeper.timer`: systemd timer, trigger once in every 2 hours

Workspace structure:

```
.
├── conf.json
├── id_ed25519
├── streamrlib.py
└── streamr.py
```

## Tips

- You'll have to put wallet private key on vps to make streamr miner node working, it is very important to make sure your machine is secure.
- To use `streamr-miner-keeper` you'll have to put vps private key on the host machine, this is also not good. **Please use it on you own risk.** (it is better to use a computer in LAN network to run the scripts)

## Acknowledgement

- https://brubeckscan.app/
- https://streamr.network/docs/streamr-network/mining

