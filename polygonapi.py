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
