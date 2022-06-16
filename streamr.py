import concurrent
import fire

from streamrlib import *

def streamr_get_all_miner_info(miners, max_workers = 10):
    sapi = StreamrApi()
    params = miners.keys()
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(sapi.miner, a): (a) for a in params}
        for future in concurrent.futures.as_completed(futures):
            pubkey = futures[future]
            res = future.result()
            m = miners[pubkey]
            results[pubkey] = m.copy()
            results[pubkey]['data'] = res['DATA']
            results[pubkey]['secondsSinceLastClaim'] = res['STATS']['secondsSinceLastClaim']
            results[pubkey]['lastClaimTime'] = res['STATS']['lastClaimTime']

    # print(json.dumps(results, indent=4))

    return results

def keeper(conffile):
    conf = load_json_file(conffile)

    default_sshkey = conf['sshkey']

    hosts = {}
    for obj in conf["hosts"]:
        if obj == {}:
            continue
        name = obj['name']
        hosts[name] = obj.copy()
        if hosts[name].get("sshkey", "") == "":
            hosts[name]['sshkey'] = default_sshkey
        print(hosts[name])

    miners = {}
    for obj in conf["miners"]:
        if obj == {}:
            continue
        miners[obj['pubkey']] = obj.copy()

    rewards = 0
    message = ""
    results = streamr_get_all_miner_info(miners)
    for pubkey in miners:
        r = results[pubkey]
        sta = "OK"
        if r['secondsSinceLastClaim'] > 3*60*60:
            cmd = r['command']
            if r['command'] == 'auto':
                cmd = f"sudo docker restart {r['container']}"
            try:
                SSHClient(hosts[r['host']]).exec_cmd_and_close(cmd)
            except:
                print(f"Fail to restart streamr node {r['id']}")
            sta = "**NG**"
        message += f"{sta}, ID{r['id']}, {int(r['data'])}, {r['secondsSinceLastClaim']/60/60:.1f}h\n"
        rewards += r['data']

    if conf['dingtalkkey'] != "":
        dingtalk = DingTalk(conf['dingtalkkey'])
        dingtalk.push("$STREAMR", f"Total: {rewards} DATA\n{message}")


if __name__ == '__main__':
    fire.Fire({
        "keeper": keeper,
    })


