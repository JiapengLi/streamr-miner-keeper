import concurrent
import fire

from streamrlib import *
from streamrdb import *

from collections import OrderedDict

from playhouse.shortcuts import model_to_dict, dict_to_model

from pycoingecko import CoinGeckoAPI

from polygonapi import PolygonApi
from evmtoken import EVMTOKENS

def host(action, name, address="", user="", port=22, sshkey=""):
    h = {
        "name": name,
        "address": address,
        "user": user,
        "port": port,
        "sshkey": sshkey,
    }

    if str.lower(action) == 'add':
        host("del", name)
        try:
            default_sshkey = Conf.get(Conf.key == 'sshkey').value
            if h['sshkey'] == '':
                h['sshkey'] = default_sshkey
            Host.create(**h)
        except Exception as e:
            print(f"error: {e}")

        print(h)
    elif str.lower(action) == 'del':
        try:
            try:
                h = Host.get(Host.name == h['name'])
            except:
                h = None
            if h:
                h.delete_instance()
        except Exception as e:
            print(f"error: {e}")
    else:
        print(f"Unknown action {action}, use `add` or `del`")

def miner(action, pubkey, name="", host="", container="", command="auto"):
    m = {
        'pubkey': pubkey,
        'name': name,
        'host': host,
        'container': container,
        'command': command
    }
    if str.lower(action) == 'add':
        miner("del", pubkey, host=host)
        try:
            Miner.create(**m)
        except Exception as e:
            print(f"miner add error: {e}")
        print(f"{m}")
    elif str.lower(action) == 'del':
        try:
            try:
                m = Miner.get(Miner.pubkey == pubkey)
            except:
                m = None
            if m:
                m.delete_instance()
        except Exception as e:
            print(f"miner del error: {e}")
    else:
        print(f"Unknown action {action}, use `add` or `del`")

def cfg2db(conffile):
    create_tables()

    conf = load_json_file(conffile)

    try:
        Conf.create(key='sshkey', value=conf['sshkey'])
        Conf.create(key='dingtalkkey', value=conf['dingtalkkey'])
        Conf.create(key='notifyts', value=f"{int(time.time()) - 40 * 60}")
    except:
        pass

    for obj in conf["hosts"]:
        if obj == {}:
            continue
        host('add', **obj)

    for obj in conf["miners"]:
        if obj == {}:
            continue
        miner('add', **obj)

def db2cfg(conffile):
    conf = {}
    save_json_file(conf, conffile)

def fetch_miners_info(max_workers = 10):
    sapi = StreamrApi()
    params = [m.pubkey for m in Miner.select()]
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(sapi.miner, a): (a) for a in params}
        for future in concurrent.futures.as_completed(futures):
            pubkey = futures[future]
            res = future.result()
            results[pubkey] = {
                "data": 0,
                "secondsSinceLastClaim": 0,
                "lastClaimTime": "unknown",
                "receivedRewards": 0,
            }
            if res['DATA']:
                results[pubkey]['data'] = res['DATA']
                results[pubkey]['receivedRewards'] = res['STATS']['receivedRewards']
                results[pubkey]['secondsSinceLastClaim'] = res['STATS']['secondsSinceLastClaim']
                results[pubkey]['lastClaimTime'] = res['STATS']['lastClaimTime']
    print(json.dumps(results, indent=4))

    return results

def keeper():
    force_notify = False
    total_rewards = 0
    received_rewards = 0
    message = ""

    cg = CoinGeckoAPI()
    ret = cg.get_price(ids='streamr,matic-network,helium,bitcoin,dimo,', vs_currencies='usd')
    print(ret)
    DATA_Price = ret['streamr']['usd']
    MATIC_Price = ret['matic-network']['usd']
    HNT_Price = ret['helium']['usd']
    BTC_Price = ret['bitcoin']['usd']
    DIMO_Price = ret['dimo']['usd']

    papi = PolygonApi()
    token = "DATA"
    papi.set_contract(token=EVMTOKENS[token]['address'], abi=EVMTOKENS[token]['abi'])

    results = fetch_miners_info()

    totalBalanceMATIC = 0
    totalBalanceDATA = 0.0
    message_dict = OrderedDict()
    for m in Miner.select():
        if results.get(m.pubkey, '') == '':
            continue

        r = results[m.pubkey]
        sta = "OK"

        matic = papi.balance(m.pubkey)
        balance = papi.token_balance(m.pubkey)
        totalBalanceMATIC += matic
        totalBalanceDATA += balance

        seconds_since_last_fix = 0
        if m.fixtime != 0:
            seconds_since_last_fix = int(time.time() - m.fixtime)

        if r['secondsSinceLastClaim'] > 2 * 60 *60:
            sta = "**NG**"
            if seconds_since_last_fix == 0 or seconds_since_last_fix > 1.5 * 60 * 60:
                force_notify = True
                cmd = m.command
                if m.command == 'auto':
                    cmd = f"sudo docker restart {m.container}"
                try:
                    h = model_to_dict(Host.get(Host.name == m.host_id))
                    SSHClient(**h).exec_cmd_and_close(cmd)
                    m.fixtime = int(time.time())
                    m.save()
                except Exception as e:
                    print(f"Fail to restart streamr node {m.name}")
                    print(e)
            else:
                print(f"Skip restart device ID{m.name}")
        urewards = r['data'] - r['receivedRewards']
        msg = f"{sta}, ID{m.name}, {int(r['data']):d}, {int(r['receivedRewards']):d}, {int(urewards):d}, {r['secondsSinceLastClaim']/60/60:.1f}h, {int(seconds_since_last_fix/60/60)}h\n"
        message_dict[f'ID{m.name}'] = msg
        total_rewards += r['data']
        received_rewards += r['receivedRewards']

    for _, v in sorted(message_dict.items()):
        message += v
    # print(message_dict)

    rate = received_rewards / (totalBalanceDATA/10**18 - total_rewards)

    message = f'''
BTC Price: {BTC_Price:.0f}U
DATA Price: {DATA_Price:.6f}U
HNT Price: {HNT_Price:.2f}U
DIMO Price: {DIMO_Price:.6f}U
MATIC Price: {MATIC_Price:.6f}U
---
Miner: {len(Miner.select())}
Total: {total_rewards:.0f} DATA
Received: {received_rewards:.0f} / {totalBalanceDATA/10**18/1000:.0f}K DATA ({totalBalanceDATA / 10**18 * DATA_Price:.0f}U {rate * 100:.1f}%)
Unclaimed: {total_rewards - received_rewards:.0f} DATA
{message}'''
    print(message)

    try:
        c = Conf.get(Conf.key == 'dingtalkkey')
        n = Conf.get(Conf.key == 'notifyts')
        if c.value != "" :

            if (time.time() - int(n.value)) > 40 * 60:
                force_notify = True
            else:
                print(f"{40 * 60 - (time.time() - int(n.value)):.0f}s to notify")

            if force_notify:
                dingtalk = DingTalk(c.value)
                dingtalk.push("$STREAMR", message)
                n.value = f"{int(time.time())}"
                n.save()
    except:
        pass

def test():
    sapi = StreamrApi()
    pass

if __name__ == '__main__':
    create_tables()

    fire.Fire({
        "cfg2db": cfg2db,
        "db2cfg": db2cfg,

        "host": host,
        "miner": miner,

        "keeper": keeper,

        "test": test,
    })

    close_db()
