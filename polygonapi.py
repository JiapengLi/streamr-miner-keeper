from web3 import Web3, HTTPProvider

class PolygonApi:
    def __init__(self, rpc=None, unit = 'ether'):
        if rpc is None:
            rpc = 'https://polygon-rpc.com/'
        self.w3 = Web3(HTTPProvider(rpc))
        self.unit = unit

        if self.w3.isConnected():
            print(f"Polygon RPC connected, chainid: {self.w3.eth.chainId}, blocknumber {self.w3.eth.blockNumber}, gas {self.w3.eth.gas_price}")
        else:
            print(f"Check network")

        if self.w3.eth.max_priority_fee > 100*1000000000:
            print(f"Gas price too high")
        else:
            print(f"Gas price {self.w3.eth.max_priority_fee}")

        # self.w3.eth.set_gas_price_strategy(medium_gas_price_strategy)

        # print(self.w3.eth.generate_gas_price())

        self.contract = None

    def key2addr(self, prikey):
        private_key = bytes.fromhex(prikey)
        account = self.w3.eth.account.from_key(private_key=private_key)
        return account.address

    def balance(self, pubkey):
        return self.w3.eth.get_balance(pubkey)

    def pay(self, prikey, pubkey, amount):
        payer_pubkey = self.key2addr(prikey)
        payer_prikey = bytes.fromhex(prikey)
        payee_pubkey = pubkey

        print(f"{payer_pubkey} -> {payee_pubkey}, {amount}")

        nonce = self.w3.eth.getTransactionCount(payer_pubkey)
        txn = {
            'chainId': self.w3.eth.chainId,
            'nonce': nonce,
            'to': payee_pubkey,
            'value': amount,
            'gas': 100000,
            'gasPrice': self.w3.eth.gasPrice
        }

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=payer_prikey)
        transaction = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        ret = self.w3.eth.wait_for_transaction_receipt(transaction.hex())
        print(ret)

    def set_contract(self, token, abi):
        self.contract = self.w3.eth.contract(address=token, abi=abi)

    def token_balance(self, pubkey):
        balance = self.contract.functions.balanceOf(pubkey).call()
        # balance = self.w3.fromWei(balance, 'ether')
        return balance

    def transfer(self, prikey, pubkey, amount):
        payer_pubkey = self.key2addr(prikey)
        payer_prikey = bytes.fromhex(prikey)
        payee_pubkey = pubkey


        payer_b = self.token_balance(payer_pubkey)
        payee_b = self.token_balance(payee_pubkey)
        print(f"{payer_b}, {payee_b}")

        print(f"{payer_pubkey} -> {payee_pubkey}, {amount}")

        nonce = self.w3.eth.get_transaction_count(payer_pubkey)

        txn = self.contract.functions.transfer(payee_pubkey, amount).build_transaction({
            'chainId': self.w3.eth.chainId,
            'gas': 100000,
            'maxFeePerGas': self.w3.eth.gas_price + 100,
            'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            'nonce': nonce,
        })
        print(txn, type(txn))

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=payer_prikey)
        transaction = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        ret = self.w3.eth.wait_for_transaction_receipt(transaction.hex())
        print(ret)

'''
def test():
    from web3 import Web3,  HTTPProvider
    from tokenDATAAbi import DATAToken, DATAAbi

    unit = 'ether' # 10**8
    provider_uri = 'https://polygon-rpc.com/'
    address_from = '0x64e75c70683d798f61B7fE7f91d552a345dA28CD'
    address_to = '0x64e75c70683d798f61B7fE7f91d552a345dA28CD'

    private_key_str = '6b2bcfbdba7d68f25f5c4a457726b6f86e34b21e7a0f0151368a2d5af7726609'
    private_key = bytes.fromhex(private_key_str)
    print(private_key)

    w3 = Web3(HTTPProvider(provider_uri))
    contract = w3.eth.contract(address=DATAToken, abi=DATAAbi)

    # chain info
    print(w3.isConnected())
    print(f"chainid: {w3.eth.chainId}, blocknumber {w3.eth.blockNumber}")

    # wallet balance
    ret = w3.eth.get_balance(address_from)
    matic = w3.fromWei(ret, unit)
    print(f"{ret}, {matic:.6f}matic")

    # ERC-20 contract info
    totalSupply = contract.functions.totalSupply().call()
    totalSupply = w3.fromWei(totalSupply, unit)

    name  = contract.functions.name().call()

    symbol = contract.functions.symbol().call()

    print(f'Name: {name}, Symbol: {symbol}, Token: {DATAToken}, Total Supply: {totalSupply:.6f}')

    balance = contract.functions.balanceOf(address_from).call()
    balance = w3.fromWei(balance, 'ether')
    print(f"{address_from}, {balance}")

    account = w3.eth.account.from_key(private_key=private_key)
    print(f"Account {account.address}, {type(account)}")

    # signed_txn = w3.eth.account.signTransaction()
    # contract.functions.transfer(address_to, 10).call()
    # contract.functions.transfer('0xafC2F2bBD4173311BE60A7f5d4103b098D2703e8', 0x10).buildTransaction({'chainId': 4, 'gas':70000, 'nonce': w3.eth.getTransactionCount('0x5b580eB23Fca4f0936127335a92f722905286738')})

    #key sss-13 '6b2bcfbdba7d68f25f5c4a457726b6f86e34b21e7a0f0151368a2d5af7726609'


# When running locally, execute the statements found in the file linked below to load the EIP20_ABI variable.
# See: https://github.com/carver/ethtoken.py/blob/v0.0.1-alpha.4/ethtoken/abi.py

>>> from web3.auto import w3

>>> unicorns = w3.eth.contract(address="0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359", abi=EIP20_ABI)

>>> nonce = w3.eth.get_transaction_count('0x5ce9454909639D2D17A3F753ce7d93fa0b9aB12E')

# Build a transaction that invokes this contract's function, called transfer
>>> unicorn_txn = unicorns.functions.transfer(
...     '0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359',
...     1,
... ).build_transaction({
...     'chainId': 1,
...     'gas': 70000,
...     'maxFeePerGas': w3.toWei('2', 'gwei'),
...     'maxPriorityFeePerGas': w3.toWei('1', 'gwei'),
...     'nonce': nonce,
... })

>>> unicorn_txn
{'value': 0,
 'chainId': 1,
 'gas': 70000,
 'maxFeePerGas': 2000000000,
 'maxPriorityFeePerGas': 1000000000,
 'nonce': 0,
 'to': '0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359',
 'data': '0xa9059cbb000000000000000000000000fb6916095ca1df60bb79ce92ce3ea74c37c5d3590000000000000000000000000000000000000000000000000000000000000001'}

>>> private_key = b"\xb2\\}\xb3\x1f\xee\xd9\x12''\xbf\t9\xdcv\x9a\x96VK-\xe4\xc4rm\x03[6\xec\xf1\xe5\xb3d"
>>> signed_txn = w3.eth.account.sign_transaction(unicorn_txn, private_key=private_key)
>>> signed_txn.hash
HexBytes('0x748db062639a45e519dba934fce09c367c92043867409160c9989673439dc817')
>>> signed_txn.rawTransaction
HexBytes('0x02f8b00180843b9aca0084773594008301117094fb6916095ca1df60bb79ce92ce3ea74c37c5d35980b844a9059cbb000000000000000000000000fb6916095ca1df60bb79ce92ce3ea74c37c5d3590000000000000000000000000000000000000000000000000000000000000001c001a0cec4150e52898cf1295cc4020ac0316cbf186071e7cdc5ec44eeb7cdda05afa2a06b0b3a09c7fb0112123c0bef1fd6334853a9dcf3cb5bab3ccd1f5baae926d449')
>>> signed_txn.r
93522894155654168208483453926995743737629589441154283159505514235904280342434
>>> signed_txn.s
48417310681110102814014302147799665717176259465062324746227758019974374282313
>>> signed_txn.v
1

>>> w3.eth.send_raw_transaction(signed_txn.rawTransaction)

# When you run send_raw_transaction, you get the same result as the hash of the transaction:
>>> w3.toHex(w3.keccak(signed_txn.rawTransaction))
'0x748db062639a45e519dba934fce09c367c92043867409160c9989673439dc817'
'''