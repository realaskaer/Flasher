import asyncio
import json
import time

from config import (TOKENS_PER_CHAIN, JEDISWAP_CONTRACT, PROXIES, MYSWAP_CONTRACT,
                    TENKSWAP_CONTRACT, SITHSWAP_CONTRACT)
from modules import Logger, Aggregator
from settings import MEMCOIN_AMOUNT, NUMBER_OF_STREAM, MEMCOIN_MINT_ADDRESS, MEMCOIN_SUPPLY, MEMCOIN_AMOUNT_BATCH, \
    MEMCOIN_DECIMALS, MEMCOIN_DAPP_CODE, MEMCOIN_MODE_CODE
from utils.tools import helper


class StarkCustom(Logger, Aggregator):
    def __init__(self, client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.stop_flag = False
        self.signed_tx = None

    async def swap(self):
        pass

    @staticmethod
    async def check_action_file():
        path = './data/services/action_flag.json'

        try:
            with open(path, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = {
                'action_flag': 0
            }

        if data['action_flag']:
            return True

    async def get_min_amount_out(self, contract_address:int, path: list):
        await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=contract_address,
            selector_name="get_amounts_out",
            calldata=[150000000000000, 0, len(path), *path]
        ))

    @staticmethod
    async def set_action_flag():
        path = './data/services/action_flag.json'

        try:
            with open(path, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = {
                'action_flag': 0
            }

        data['action_flag'] = 1

        with open(path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def get_selector():
        if MEMCOIN_DAPP_CODE == 1:
            return 1271585942111654734125606951221628240160430040413791527265389999851511344752
        if MEMCOIN_DAPP_CODE == 2:
            raise
        if MEMCOIN_DAPP_CODE == 3:
            raise
        if MEMCOIN_DAPP_CODE == 4:
            raise

    async def get_tx_calldata(self, router_contract:int = 0, amount_in_wei:int = 0, min_amount_out:int = 0,
                              path:list = None, deadline:int = 0, wallet:int = 0, pool_id:int = 9):
        one_percent_of_supply = int((MEMCOIN_SUPPLY * 10 ** MEMCOIN_DECIMALS) * 0.0099)
        want_pay_amount = int(MEMCOIN_AMOUNT_BATCH * 10 ** 18)
        if MEMCOIN_DAPP_CODE == 1:
            if MEMCOIN_MODE_CODE:
                return self.client.prepare_call(
                    contract_address=router_contract,
                    selector_name="swap_exact_tokens_for_tokens",
                    calldata=[
                        amount_in_wei, 0,
                        min_amount_out, 0,
                        len(path),
                        *path,
                        int(wallet),
                        deadline
                    ]
                )

            return self.client.prepare_call(
                contract_address=router_contract,
                selector_name="swap_tokens_for_exact_tokens",
                calldata=[
                    one_percent_of_supply, 0,
                    want_pay_amount, 0,
                    len(path),
                    *path,
                    int(wallet),
                    deadline
                ]
            )
        elif MEMCOIN_DAPP_CODE == 2:
            eth_address = TOKENS_PER_CHAIN['Starknet']['ETH']
            return self.client.prepare_call(
                contract_address=router_contract,
                selector_name="swap",
                calldata=[
                    pool_id,
                    eth_address,
                    amount_in_wei, 0,
                    min_amount_out, 0
                ]
            )
        elif MEMCOIN_DAPP_CODE in [3, 4]:
            if MEMCOIN_MODE_CODE:
                return self.client.prepare_call(
                    contract_address=router_contract,
                    selector_name="swapExactTokensForTokens",
                    calldata=[
                        amount_in_wei, 0,
                        min_amount_out, 0,
                        *path,
                        int(wallet),
                        deadline
                    ]
                )
            return self.client.prepare_call(
                contract_address=router_contract,
                selector_name="swapTokensForExactTokens",
                calldata=[
                    one_percent_of_supply, 0,
                    want_pay_amount, 0,
                    *path,
                    int(wallet),
                    deadline
                ]
            )

    @staticmethod
    async def process_transactions(block_data, selector, eth_address, memcoin_address, contract_address):
        flag = False
        try:
            count = len(block_data)
            for i in range(count - 1, -1, -1):
                tx = block_data[i]
                if (selector in tx.calldata and eth_address in tx.calldata and
                        memcoin_address in tx.calldata and contract_address in tx.calldata):
                    flag = True
                    break
            return flag
        except AttributeError:
            pass
        except IndexError:
            pass

    async def send_tx_fast(self, client, signed_tx):
        try:
            tx_hash = (await client.account._client.send_transaction(signed_tx)).transaction_hash

            self.logger_msg(
                *self.client.acc_info, msg=f'Transaction is pending in mempool')

            await client.account.client.wait_for_tx(tx_hash)

            self.logger_msg(
                *self.client.acc_info,msg=f'Transaction was successful: {self.client.explorer}tx/{hex(tx_hash)}',
                type_msg='success')
            await client.session.close()
        except Exception as error:
            self.logger_msg(*self.client.acc_info, msg=f'Error in <SEND TX> function: {error}', type_msg='error')
            await client.session.close()

    async def check_pool(self, client, contract_address, stream_number):
        eth_address = TOKENS_PER_CHAIN['Starknet']['ETH']
        memcoin_address = TOKENS_PER_CHAIN['Starknet']['MEMCOIN']
        selector = self.get_selector()
        while True:
            try:
                if await self.check_action_file():
                    break

                block_data = (await client.account.client.get_block('pending')).transactions

                flag = await self.process_transactions(block_data, selector, eth_address,
                                                       memcoin_address, contract_address)
                if flag:
                    await self.set_action_flag()
                    self.logger_msg(*client.acc_info, msg=f'Add liquidity tx in mempool', type_msg='success')
                    break
                self.logger_msg(*client.acc_info, msg=f'Pool not created', type_msg='error')
            except Exception as error:
                self.logger_msg(
                    *client.acc_info,
                    msg=f'Stream-{stream_number + 1:0>2} | Error in <CHECK POOL> function: {error}', type_msg='error')

    async def get_signed_tx(self, client, batch_mode:bool = False):
        amount_in_wei = int(MEMCOIN_AMOUNT * 10 ** 18)

        if MEMCOIN_DAPP_CODE == 1:
            router_contract = JEDISWAP_CONTRACT['router']
        elif MEMCOIN_DAPP_CODE == 2:
            router_contract = MYSWAP_CONTRACT['router']
        elif MEMCOIN_DAPP_CODE == 3:
            router_contract = TENKSWAP_CONTRACT['router']
        elif MEMCOIN_DAPP_CODE == 4:
            router_contract = SITHSWAP_CONTRACT['router']
        else:
            raise RuntimeError('DAPP CODE WILL BE IN [1, 2, 3, 4]')

        from_token_address = TOKENS_PER_CHAIN[client.network.name]['ETH']
        to_token_address = TOKENS_PER_CHAIN[client.network.name]['MEMCOIN']

        deadline = int(time.time()) + 1000000
        path = [from_token_address, to_token_address]
        fee_per_acc = int(0.002 * 10 ** 18)
        max_fee = (int(0.0005 * 10 ** 18) * len(MEMCOIN_MINT_ADDRESS)) if batch_mode else fee_per_acc
        calls = [client.get_approve_call(from_token_address, router_contract, amount_in_wei, unlim_approve=True)]
        min_amount_out = 1000

        if batch_mode:
            for wallet in MEMCOIN_MINT_ADDRESS:
                calls.append(await self.get_tx_calldata(path=path, amount_in_wei=amount_in_wei, deadline=deadline,
                                                        min_amount_out=min_amount_out, wallet=wallet,
                                                        router_contract=router_contract))
        else:
            calls.append(await self.get_tx_calldata(path=path, amount_in_wei=amount_in_wei, deadline=deadline,
                                                    min_amount_out=min_amount_out, wallet=client.address,
                                                    router_contract=router_contract))

        nonce = await client.account.get_nonce()
        signed_tx = await client.account.sign_invoke_transaction(calls, nonce=nonce, max_fee=max_fee,
                                                                 auto_estimate=False)

        return signed_tx, router_contract, path

    async def mint_token_jediswap(self, batch_mode:bool = False):
        from functions import get_client

        await self.client.initialize_account()

        signed_tx, router_contract, path = await self.get_signed_tx(self.client, batch_mode=batch_mode)

        tasks_pool = []
        clients = []

        if self.client.acc_number == 1:
            for stream_number, _ in enumerate(range(NUMBER_OF_STREAM)):
                proxy = PROXIES[stream_number % len(PROXIES)]
                rpc = self.client.network.rpc[1:][stream_number % (len(self.client.network.rpc) - 1)]
                client = get_client(self.client.account_name, self.client.private_key, self.client.network,
                                    proxy, rpc=rpc)
                await client.initialize_account()
                clients.append(client)
            for index, _ in enumerate(range(NUMBER_OF_STREAM)):
                tasks_pool.append(asyncio.create_task(self.check_pool(clients[index], router_contract, index)))
            try:

                self.logger_msg(*self.client.acc_info, msg=f'Stark check add liquidity tx')

                done, pending = await asyncio.wait(tasks_pool, return_when=asyncio.FIRST_COMPLETED)

                for task in pending:
                    task.cancel()
            except Exception as error:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'Error in <GENERATE POOL>: {error}', type_msg='error')

        else:
            while True:
                if await self.check_action_file():
                    break
                else:
                    await asyncio.sleep(0.025)

        await self.send_tx_fast(self.client, signed_tx)

        for client in clients:
            await client.session.close()

        return True

    @helper
    async def sell_token_jediswap(self):
        from functions import swap_jediswap

        await self.client.initialize_account()

        amount_in_wei, amount, _ = await self.client.get_token_balance('MEMCOIN', check_symbol=False)
        data = 'MEMCOIN', 'ETH', f"{amount:.2f}", amount_in_wei

        return await swap_jediswap(self.client, swapdata=data)

    @helper
    async def stress_test(self):
        await self.client.initialize_account()

        self.logger_msg(*self.client.acc_info, msg=f'Start testing node. All tx will be lunch together')
        tasks = []
        ranges = [50, 100, 200, 300, 400, 500, 1000, 1500, 2000, 3000, 5000]
        for limit in ranges:
            for i in range(limit):
                tasks.append(asyncio.create_task(self.client.account.get_balance()))

                await asyncio.gather(*tasks)
                self.logger_msg(*self.client.acc_info, msg=f'Test with {limit} get balance tx was success',
                                type_msg='success')
                self.logger_msg(*self.client.acc_info, msg=f'Sleep 60 seconds')
                await asyncio.sleep(61)

    @helper
    async def mint_inscribe(self):
        await self.client.initialize_account()
        calls = []

        call = self.client.prepare_call(
            contract_address=0x07341189e3c96f636a4192cfba8c18deeee33a19c5d0425a26cf96ea42388c4e,
            selector_name="inscribe",
            calldata=[
                *list("data:,{\"p\":\"stark-20\",\"op\":\"mint\",\"tick\":\"STRK\",\"amt\":\"1000\"}".encode())
            ]
        )

        for i in range(20):
            calls.append(call)

        signed_tx = await self.client.account.sign_invoke_transaction(calls, auto_estimate=True)

        return await self.send_tx_fast(self.client, signed_tx)
