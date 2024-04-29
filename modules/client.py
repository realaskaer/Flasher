import asyncio
import random

from asyncio import sleep
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from web3.exceptions import TransactionNotFound, TimeExhausted

from modules import Logger
from utils.networks import Network
from config import ERC20_ABI, TOKENS_PER_CHAIN, CHAIN_IDS, TOKENS_PER_CHAIN2
from web3 import AsyncHTTPProvider, AsyncWeb3
from config import RHINO_CHAIN_INFO, ORBITER_CHAINS_INFO, LAYERSWAP_CHAIN_NAME
from settings import (
    UNLIMITED_APPROVE,
    ORBITER_CHAIN_ID_TO,
    ORBITER_DEPOSIT_AMOUNT,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_DEPOSIT_AMOUNT,
    RHINO_CHAIN_ID_TO,
    RHINO_DEPOSIT_AMOUNT,
    ACROSS_CHAIN_ID_TO,
    ACROSS_DEPOSIT_AMOUNT, GAS_PRICE_MULTIPLIER,
)


class Client(Logger):
    def __init__(self, account_name: str, private_key: str, network: Network, proxy: None | str = None):
        super().__init__()
        self.network = network
        self.eip1559_support = network.eip1559_support
        self.token = network.token
        self.explorer = network.explorer
        self.chain_id = network.chain_id

        self.proxy_init = proxy
        self.session = ClientSession(connector=ProxyConnector.from_url(f"http://{proxy}") if proxy else None)
        self.request_kwargs = {"proxy": f"http://{proxy}"} if proxy else {}
        self.w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(network.rpc), request_kwargs=self.request_kwargs))
        self.account_name = account_name
        self.private_key = private_key
        self.address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)
        self.acc_info = account_name, self.address

    @staticmethod
    def round_amount(min_amount: float, max_amount:float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals)

    @staticmethod
    def get_normalize_error(error):
        if 'message' in error.args[0]:
            error = error.args[0]['message']
        return error

    async def get_decimals(self, token_name:str):
        contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])
        return await contract.functions.decimals().call()

    async def get_normalize_amount(self, token_name, amount_in_wei):
        decimals = await self.get_decimals(token_name)
        return float(amount_in_wei / 10 ** decimals)

    async def get_smart_amount(self, settings):
        if isinstance(settings[0], str):
            _, amount, _ = await self.get_token_balance()
            percent = round(random.uniform(float(settings[0]), float(settings[1])), 6) / 100
            amount = round(amount * percent, 6)
        else:
            amount = self.round_amount(*settings)
        return amount

    async def get_bridge_data(self, chain_from_id:int, module_name:str):
        bridge_info = {
            'Rhino': (RHINO_CHAIN_INFO, RHINO_CHAIN_ID_TO, RHINO_DEPOSIT_AMOUNT),
            'LayerSwap': (LAYERSWAP_CHAIN_NAME, LAYERSWAP_CHAIN_ID_TO, LAYERSWAP_DEPOSIT_AMOUNT),
            'Orbiter': (ORBITER_CHAINS_INFO, ORBITER_CHAIN_ID_TO, ORBITER_DEPOSIT_AMOUNT),
            'Across': (CHAIN_IDS, ACROSS_CHAIN_ID_TO, ACROSS_DEPOSIT_AMOUNT)
        }[module_name]

        deposit_info = bridge_info[2]
        src_chain_id = chain_from_id
        source_chain = bridge_info[0][src_chain_id]
        dst_chains = random.choice(bridge_info[1])
        destination_chain = bridge_info[0][dst_chains]

        amount = await self.get_smart_amount(deposit_info)
        return source_chain, destination_chain, amount, dst_chains


    def to_wei(self, number: int | float | str, decimals: int = 18) -> int:

        unit_name = {
            18: 'ether',
            6: 'mwei'
        }[decimals]

        return self.w3.to_wei(number=number, unit=unit_name)
    async def new_client(self, chain_id):
        from functions import get_network_by_chain_id
        new_client = Client(self.account_name, self.private_key,
                            get_network_by_chain_id(chain_id), self.proxy_init)
        return new_client

    async def wait_for_receiving(self, chain_id:int, old_balance:int = 0, token_name:str = 'ETH', sleep_time:int = 60,
                                 timeout: int = 1200, check_balance_on_dst:bool = False):
        client = await self.new_client(chain_id)

        try:
            if check_balance_on_dst:
                old_balance, _, _ = await client.get_token_balance(token_name)
                return old_balance

            self.logger_msg(*self.acc_info, msg=f'Waiting {token_name} to receive')

            t = 0
            new_eth_balance = 0
            while t < timeout:
                try:
                    new_eth_balance, _, _ = await client.get_token_balance(token_name)
                except:
                    pass

                if new_eth_balance > old_balance:
                    dicimals = await client.get_decimals(token_name) if token_name != client.network.token else 18
                    amount = round((new_eth_balance - old_balance) / 10 ** dicimals, 6)
                    self.logger_msg(*self.acc_info, msg=f'{amount} {token_name} was received', type_msg='success')
                    return True
                else:
                    self.logger_msg(*self.acc_info, msg=f'Still waiting {token_name} to receive...', type_msg='warning')
                    await asyncio.sleep(sleep_time)
                    t += sleep_time
                if t > timeout:
                    raise RuntimeError(f'{token_name} has not been received within {timeout} seconds')
        except Exception as error:
            raise RuntimeError(f'Error in <WAIT FOR RECEIVING> function. Error: {error}')
        finally:
            await client.session.close()

    async def get_token_balance(self, token_name: str = 'ETH', check_symbol: bool = True,
                                omnicheck:bool = False) -> [float, int, str]:
        if token_name != self.network.token:
            if omnicheck:
                contract = self.get_contract(TOKENS_PER_CHAIN2[self.network.name][token_name])
            else:
                contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])

            amount_in_wei = await contract.functions.balanceOf(self.address).call()
            decimals = await contract.functions.decimals().call()

            if check_symbol:
                symbol = await contract.functions.symbol().call()
                return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
            return amount_in_wei, amount_in_wei / 10 ** decimals, ''

        amount_in_wei = await self.w3.eth.get_balance(self.address)
        return amount_in_wei, amount_in_wei / 10 ** 18, 'ETH'

    def get_contract(self, contract_address: str, abi=ERC20_ABI):
        return self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi
        )

    async def get_allowance(self, token_address: str, spender_address: str) -> int:
        contract = self.get_contract(token_address)
        return await contract.functions.allowance(
            self.address,
            spender_address
        ).call()

    async def get_priotiry_fee(self):
        fee_history = await self.w3.eth.fee_history(25, 'latest', [20.0])
        non_empty_block_priority_fees = [fee[0] for fee in fee_history["reward"] if fee[0] != 0]

        divisor_priority = max(len(non_empty_block_priority_fees), 1)

        priority_fee = int(round(sum(non_empty_block_priority_fees) / divisor_priority))

        return priority_fee

    async def prepare_transaction(self, value: int = 0):
        try:
            tx_params = {
                'from': self.w3.to_checksum_address(self.address),
                'nonce': await self.w3.eth.get_transaction_count(self.address),
                'value': value,
                'chainId': self.network.chain_id
            }

            if self.network.eip1559_support:

                base_fee = await self.w3.eth.gas_price
                max_priority_fee_per_gas = await self.get_priotiry_fee()
                max_fee_per_gas = base_fee + max_priority_fee_per_gas

                tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                tx_params['maxFeePerGas'] = int(max_fee_per_gas * GAS_PRICE_MULTIPLIER)
                tx_params['type'] = '0x2'
            else:
                tx_params['gasPrice'] = int(await self.w3.eth.gas_price * GAS_PRICE_MULTIPLIER * 5)

            return tx_params
        except TimeoutError or ValueError as error:
            raise error(f'Bad connection or rate limit error | Error: {self.get_normalize_error(error)}')
        except Exception as error:
            raise RuntimeError(f'Prepare transaction | Error: {self.get_normalize_error(error)}')

    async def make_approve(self, token_address: str, spender_address: str, amount_in_wei: int = 1):
        transaction = await self.get_contract(token_address).functions.approve(
            spender_address,
            amount=2 ** 256 - 1
        ).build_transaction(await self.prepare_transaction())

        return await self.send_transaction(transaction)

    async def check_for_approved(
            self, token_address: str, spender_address: str, amount_in_wei: int = 2 * 256 - 1,
            without_bal_check: bool = False,
    ) -> bool:
        try:
            contract = self.get_contract(token_address)

            balance_in_wei = await contract.functions.balanceOf(self.address).call()
            symbol = await contract.functions.symbol().call()

            self.logger_msg(*self.acc_info, msg=f'Check for approval {symbol}')

            if not without_bal_check and balance_in_wei <= 0:
                raise RuntimeError(f'Zero {symbol} balance')

            approved_amount_in_wei = await self.get_allowance(
                token_address=token_address,
                spender_address=spender_address
            )

            if amount_in_wei <= approved_amount_in_wei:
                self.logger_msg(*self.acc_info, msg=f'Already approved')
                return False

            return await self.make_approve(token_address, spender_address, amount_in_wei)
        except Exception as error:
            raise RuntimeError(f'Check for approve | {self.get_normalize_error(error)}')

    async def send_transaction(self, transaction, need_hash:bool = False, without_gas:bool = False,
                               poll_latency:int = 10, timeout:int = 360):
        try:
            if not without_gas:
                transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * 1.5)
        except Exception as error:
            raise RuntimeError(f'Gas calculating | {self.get_normalize_error(error)}')

        try:
            singed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = await self.w3.eth.send_raw_transaction(singed_tx.rawTransaction)
        except Exception as error:
            if self.get_normalize_error(error) == 'already known':
                self.logger_msg(*self.acc_info, msg='RPC got error, but tx was send', type_msg='warning')
                return True
            else:
                raise RuntimeError(f'Send transaction | {self.get_normalize_error(error)}')

        try:

            total_time = 0
            while True:
                try:
                    receipts = await self.w3.eth.get_transaction_receipt(tx_hash)
                    status = receipts.get("status")
                    if status == 1:
                        message = f'Transaction was successful: {self.explorer}tx/{tx_hash.hex()}'
                        self.logger_msg(*self.acc_info, msg=message, type_msg='success')
                        if need_hash:
                            return tx_hash
                        return True
                    elif status is None:
                        await asyncio.sleep(poll_latency)
                    else:
                        raise RuntimeError(f'Transaction failed: {self.explorer}tx/{tx_hash}')
                except TransactionNotFound:
                    if total_time > timeout:
                        raise TimeExhausted(f"Transaction {tx_hash !r} is not in the chain after {timeout} seconds")

                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)

        except Exception as error:
            raise RuntimeError(f'Verify transaction | {self.get_normalize_error(error)}')

