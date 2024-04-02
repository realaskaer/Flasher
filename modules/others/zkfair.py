import asyncio
import random

from datetime import datetime
from eth_account.messages import encode_defunct
from web3.exceptions import TransactionNotFound, TimeExhausted
from config import ZKFAIR_ABI
from modules import Logger, Aggregator
from settings import ZKFAIR_GAS_LIMIT, ZKFAIR_GAS_PRICE, ZKFAIR_CLAIM_REFUND_PHASES
from utils.tools import helper


class ZKFair(Logger, Aggregator):
    def __init__(self, client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)

    @helper
    async def verif_tx(self, tx_hash):
        poll_latency = 25
        total_time = 0
        timeout = 3600
        while True:
            try:
                receipts = await self.client.w3.eth.get_transaction_receipt(tx_hash)
                status = receipts.get("status")
                if status == 1:
                    message = f'Transaction was successful: {self.client.explorer}tx/{tx_hash.hex()}'
                    self.logger_msg(*self.client.acc_info, msg=message, type_msg='success')
                    return True
                elif status is None:
                    await asyncio.sleep(poll_latency)
                else:
                    raise RuntimeError(f'Transaction failed: {self.client.explorer}tx/{tx_hash}')
            except TransactionNotFound:
                if total_time > timeout:
                    raise TimeExhausted(f"Transaction {tx_hash !r} is not in the chain after {timeout} seconds")

                total_time += poll_latency
                await asyncio.sleep(poll_latency)

    async def prepare_sign_tx(self):
        digit = random.randint(1, 9)
        amount, amount_in_wei = float(f"0.0{digit}"), int(f"{digit}0000000000000000")

        tx_params = {
            'from': self.client.w3.to_checksum_address(self.client.address),
            'nonce': await self.client.w3.eth.get_transaction_count(self.client.address),
            'value': 0,
            'chainId': self.client.network.chain_id,
            'gasPrice': int(ZKFAIR_GAS_PRICE * 10 ** 9),
            'gas': ZKFAIR_GAS_LIMIT,
            "to": self.client.address,
            "data": '0x'
        }

        return (self.client.w3.eth.account.sign_transaction(tx_params, self.client.private_key)).rawTransaction

    async def send_tx_to_my_self(self, signed_tx):

        tx_hash = await self.client.w3.eth.send_raw_transaction(signed_tx)

        self.logger_msg(*self.client.acc_info, msg=f"Transfer was send", type_msg='success')

        return await self.verif_tx(tx_hash)

    @helper
    async def send_txs_to_my_sefl(self):
        try:
            signed_tx = await self.prepare_sign_tx()

        except Exception as error:
            raise RuntimeError(f'Python обосрался во время подписания транзакции. Error: {error}')
        try:
            return await self.send_tx_to_my_self(signed_tx)

        except Exception as error:
            raise RuntimeError(f'Python обосрался во время отправки транзакций. Error: {error}')

    async def claim_refund(self):
        timestamp, api_signature = self.get_authentication_data()

        url_proof = 'https://airdrop.zkfair.io/api/refund_merkle'
        url_refund = 'https://airdrop.zkfair.io/api/refundable'

        for phase in ZKFAIR_CLAIM_REFUND_PHASES:
            params_proof = {
                'address': self.client.address,
                'phase': phase,
                'API-SIGNATURE': api_signature,
                'TIMESTAMP': timestamp
            }

            params_refund = {
                'address': self.client.address,
                'API-SIGNATURE': api_signature,
                'TIMESTAMP': timestamp
            }

            try:
                proof = (await self.make_request(url=url_proof, params=params_proof))['data']['proof']
                refund_data = (await self.make_request(url=url_refund, params=params_refund))['data'][f"phase{phase}"]
                refund_index = int(refund_data['refund_index'])
                refund_in_wei = int(refund_data['account_refund'])
                refund_contract_address = refund_data['refund_contract_address']
            except:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'Available to refund in phase {phase}: 0 USDC', type_msg='warning')
                continue

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Available to refund in phase {phase}: {refund_in_wei / 10 ** 18:.3f} USDC', type_msg='success')

            refund_contract = self.client.get_contract(refund_contract_address, ZKFAIR_ABI)

            transaction = await refund_contract.functions.claim(
                refund_index,
                refund_in_wei,
                proof
            ).build_transaction(await self.client.prepare_transaction())

            await self.client.send_transaction(transaction)

        return True

    def get_authentication_data(self):
        current_time = datetime.utcnow()
        formatted_time = current_time.isoformat(timespec='milliseconds') + 'Z'

        text = f"{formatted_time}GET/api/airdrop?address={self.client.address}"

        text_hex = "0x" + text.encode('utf-8').hex()
        text_encoded = encode_defunct(hexstr=text_hex)
        signature = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key).signature

        return formatted_time, self.client.w3.to_hex(signature)

    @helper
    async def claim_drop(self):
        timestamp, api_signature = self.get_authentication_data()

        url_proof = 'https://airdrop.zkfair.io/api/airdrop_merkle'
        url_airdrop = 'https://airdrop.zkfair.io/api/airdrop'

        params_proof = {
            'address': self.client.address,
            'API-SIGNATURE': api_signature,
            'TIMESTAMP': timestamp
        }

        params_airdrop = {
            'address': self.client.address,
            'API-SIGNATURE': api_signature,
            'TIMESTAMP': timestamp
        }

        proof_data = (await self.make_request(url=url_proof, params=params_proof))
        airdrop_data = (await self.make_request(url=url_airdrop, params=params_airdrop))

        if proof_data['resultCode'] == 0 and airdrop_data['resultCode'] == 0:
            proof = proof_data['data']['proof']
            airdrop_index = int(airdrop_data['data']['index'])
            airdrop_in_wei = int(airdrop_data['data']['account_profit'])
            airdrop_contract_address = airdrop_data['data']['contract_address']

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Available to claim: {airdrop_in_wei / 10 ** 18:.3f} ZKF', type_msg='success')

            airdrop_contract = self.client.get_contract(airdrop_contract_address, ZKFAIR_ABI)

            transaction = await airdrop_contract.functions.claim(
                int(airdrop_index),
                int(airdrop_in_wei),
                proof
            ).build_transaction(await self.client.prepare_transaction())

            await self.client.send_transaction(transaction)

        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f'Not available to claim', type_msg='warning')

        return True
