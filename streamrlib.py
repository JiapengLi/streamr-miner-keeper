import os
import json
import requests

import traceback

import time, datetime, pytz

import paramiko

def save_json_file(j, file):
    f = open(file, "w")
    print(json.dumps(j, indent=4), file=f)
    f.close()

def load_json_file(file):
    f = open(file, "r", encoding="utf-8")
    res = json.loads(f.read())
    f.close()
    return res

class StreamrApi:
    def __init__(self):
        self.url = os.environ.get('STREAMR_API_URL', "https://brubeck1.streamr.network:3013")
        self.graphurl = os.environ.get('STREAMR_API_GRAPH_URL', "https://api.thegraph.com/subgraphs/name/streamr-dev/data-on-polygon")
        self.s = requests.session()

    def request(self, path, para=None, new=False):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        if new:
            s = requests.session()
        else:
            s = self.s

        url = f'{self.url}/{path}'
        res = None
        cnt = 2
        success = False
        print(f"{url} {para} {new}")
        while cnt > 0:
            try:
                res = s.get(url, headers=headers, params=para, timeout=120)
                if res.status_code != 200:
                    try:
                        resp_content = res.json()
                    except ValueError:
                        resp_content = res.content
                    delay = 8
                    print(f"{path} (chance: {cnt}) {res.status_code} {resp_content}, retry {delay}s later")
                    time.sleep(delay)
                    res = {}
                else:
                    res = res.json()
                    success = True
                    break
            except Exception as e:
                # print(f"-----------error {traceback.format_exc()}")
                print(f"error {path} {e}")
                res = {}
            cnt -= 1
        if not success:
            print(f"{path} get data failed")
        return res

    def query(self, gql=""):
        ret = self.s.post(self.graphurl, json={"query": gql}).json()
        return ret

    def received_rewards(self, address):
        streamrAddress = "0x3979f7d6b5c5bfa4bcd441b4f35bfa0731ccfaef"
        gql = f'''{{
    erc20Transfers( where: {{from: "{str.lower(streamrAddress)}", to: "{str.lower(address)}", timestamp_gt: 1640995200 }} ){{
        value
        timestamp
    }}
}}
'''
        ret = self.query(gql)
        total_rewards = 0
        for obj in ret['data']['erc20Transfers']:
            total_rewards += float(obj['value'])

        return total_rewards

    def rewards(self, address):
        return self.request(f"datarewards/{address}")
    def stats(self, address):
        return self.request(f"stats/{address}")

    '''
    {
        "DATA": 1470.05,
        "STATS": {
            "claimCount": 1541,
            "claimPercentage": 0.587047619047619,
            "claimedRewardCodes": [
                {
                    "id": "20500ae9-f551-4eee-9bff-cb51bce496f8",
                    "claimTime": "2022-04-06T03:54:13.062Z"
                }
            ]
        }
    }
    '''
    def miner(self, address):
        rewards = self.rewards(address)
        stats = self.stats(address)
        received_rewards = self.received_rewards(address)
        rewards['STATS'] = stats
        rewards['STATS']['secondsSinceLastClaim'] = 0
        rewards['STATS']['lastClaimTime'] = ""
        rewards['STATS']['receivedRewards'] = received_rewards
        if len(rewards['STATS']['claimedRewardCodes']) > 0:
            last_claim = rewards['STATS']['claimedRewardCodes'][-1]

            utc_time = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')
            claim_time = str.replace(last_claim['claimTime'], 'Z', '+00:00')

            utc_time = datetime.datetime.fromisoformat(utc_time)
            claim_time = datetime.datetime.fromisoformat(claim_time)

            seconds_since_last_claim = int((utc_time - claim_time).total_seconds())

            rewards['STATS']['secondsSinceLastClaim'] = seconds_since_last_claim
            rewards['STATS']['lastClaimTime'] = last_claim['claimTime']

        return rewards


class SSHClient:
    def __init__(self, **host):
        self.host = host

        prikey = paramiko.Ed25519Key.from_private_key_file(host['sshkey'])

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy)
        client.connect(
            hostname=host['address'],
            username=host['user'],
            port=host['port'],
            pkey=prikey,
            timeout=10
        )

        self.client = client

    def exec_cmd_and_close(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        result = str(stdout.read(), encoding="utf-8")
        self.client.close()

        print(result)
        return result

class DingTalk:
    def __init__(self, key) -> None:
        self.lastMessageTime = 0
        self.key = key

    def post(self, title, text, isatall=False):
        webhook = f"https://oapi.dingtalk.com/robot/send?access_token={self.key}"

        # request header
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }

        atlist = []
        if isatall:
            atlist = [
                "18566238520"
            ]


        # json packet
        message ={
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": atlist,
                "atUserIds": [
                ],
                "isAtAll": isatall
            }
        }
        message_json = json.dumps(message)

        #print(message_json)

        while time.monotonic() - self.lastMessageTime < 4:
            time.sleep(1)
        self.lastMessageTime = time.monotonic()

        info = requests.post(url=webhook,data=message_json,headers=header)

        #print(info.text)


    def push(self, name, msg, send_date=True, isatall=False):
        msg = str.replace(msg, "\n", "\n\n")

        utc_time = datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))
        date = utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        title = f"{name}" + f"{date} UTC",
        text_hdr = f"**{name}** \n\n"
        if send_date:
            text_hdr += f"{date} UTC\n\n"

        MAXBYTES = 4096 + 1024
        maxbytes = MAXBYTES
        if len(msg) > (MAXBYTES):
            maxbytes = len(msg) / int((len(msg) + MAXBYTES - 1)  / MAXBYTES)

        lines = msg.splitlines()
        msg_lines = ""
        for l in lines:
            msg_lines += f"{l}\n"
            if len(msg_lines) > maxbytes:
                text = text_hdr + f"{msg_lines}"
                self.post(title, text, isatall)

                text_hdr = ""
                msg_lines = ""

        if len(msg_lines) > 0:
            text = text_hdr + f"{msg_lines}"
            self.post(title, text, isatall)
