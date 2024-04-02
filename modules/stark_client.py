import asyncio
import json
import random

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.hash.address import compute_address
from starknet_py.net.client_errors import ClientError
from starknet_py.cairo.felt import decode_shortstring
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.client_models import Call

from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from modules import Logger
from utils.networks import StarknetRPC
from config import (
    TOKENS_PER_CHAIN,
    RHINO_CHAIN_INFO,
    ORBITER_CHAINS_INFO,
    LAYERSWAP_CHAIN_NAME,
    ARGENT_IMPLEMENTATION_CLASS_HASH_NEW,
    BRAAVOS_PROXY_CLASS_HASH, BRAAVOS_IMPLEMENTATION_CLASS_HASH, ARGENT_PROXY_CLASS_HASH,
    ARGENT_IMPLEMENTATION_CLASS_HASH, CHAIN_IDS
)

from settings import (
    USE_PROXY,
    UNLIMITED_APPROVE,
    ORBITER_CHAIN_ID_TO,
    ORBITER_DEPOSIT_AMOUNT,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_DEPOSIT_AMOUNT,
    RHINO_CHAIN_ID_TO,
    RHINO_DEPOSIT_AMOUNT,
    ACROSS_CHAIN_ID_TO,
    ACROSS_DEPOSIT_AMOUNT,
    NEW_WALLET_TYPE
)


class StarknetClient(Logger):
    def __init__(self, account_name: str, private_key: str, network, proxy: None | str = None, rpc=None):
        super().__init__()
        self.network = network
        self.token = network.token
        self.explorer = network.explorer
        self.chain_id = StarknetChainId.MAINNET
        self.proxy = f"http://{proxy}" if proxy else ""
        self.proxy_init = proxy
        self.account_name = account_name
        self.acc_number = int(account_name.split()[-1])
        index = self.acc_number % len(StarknetRPC.rpc) - 1

        key_pair = KeyPair.from_private_key(private_key)
        self.key_pair = key_pair
        self.session = self.get_proxy_for_account(self.proxy)
        rpc_init = network.rpc[index] if not rpc else rpc
        self.w3 = FullNodeClient(node_url=rpc_init, session=self.session)

        self.private_key = private_key
        self.acc_info = None
        self.account = None
        self.address = None
        self.WALLET_TYPE = None

    async def initialize_account(self, check_balance:bool = False):
        self.account, self.address, self.WALLET_TYPE, cairo_version = await self.get_wallet_auto(
            self.w3, self.key_pair,
            self.account_name, check_balance
        )

        self.address = int(self.address)
        self.acc_info = self.account_name, self.address
        self.account._cairo_version = cairo_version
        self.account.ESTIMATED_FEE_MULTIPLIER = 2

    async def get_wallet_auto(self, w3, key_pair, account_name, check_balance:bool = False):
        last_data = await self.check_stark_data_file(account_name)
        if last_data:
            address, wallet_type, cairo_version = (last_data['address'], last_data['wallet_type'],
                                                   last_data['cairo_version'])

            account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)

            return account, address, wallet_type, cairo_version

        possible_addresses = [(self.get_argent_address(key_pair, 1), 0, 1),
                              (self.get_braavos_address(key_pair), 1, 0),
                              (self.get_argent_address(key_pair, 0), 0, 0)]

        for address, wallet_type, cairo_version in possible_addresses:
            account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)
            try:
                if check_balance:
                    result = await account.get_balance()
                else:
                    result = await account.client.get_class_hash_at(address)

                if result:
                    await self.save_stark_data_file(account_name, address, wallet_type, cairo_version)
                    return account, address, wallet_type, cairo_version
            except ClientError:
                pass
        new_wallet = {
            0: ('ArgentX', self.get_argent_address(key_pair, 1), 0, 1),
            1: ('Braavos', self.get_braavos_address(key_pair), 1, 0)
        }[NEW_WALLET_TYPE]

        address = new_wallet[1]
        account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)
        self.logger_msg(self.account_name, None, msg=f"Account name: '{account_name}' has not deployed",
                        type_msg='warning')
        self.logger_msg(self.account_name, None, msg=f"Software will create {new_wallet[0]} account")
        return account, address, new_wallet[-2], new_wallet[-1]

    @staticmethod
    def get_proxy_for_account(proxy):
        if USE_PROXY and proxy != "":
            return ClientSession(connector=ProxyConnector.from_url(f"{proxy}", verify_ssl=False))
        return ClientSession(connector=TCPConnector(verify_ssl=False))

    @staticmethod
    async def check_stark_data_file(account_name):
        bad_progress_file_path = './data/services/stark_data.json'
        try:
            with open(bad_progress_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if account_name in data:
            return data[account_name]

    @staticmethod
    async def save_stark_data_file(account_name, address, wallet_type, cairo_version):
        bad_progress_file_path = './data/services/stark_data.json'
        try:
            with open(bad_progress_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[account_name] = {
            'address': address,
            'wallet_type': wallet_type,
            'cairo_version': cairo_version
        }

        with open(bad_progress_file_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def get_braavos_address(key_pair) -> int:
        selector = get_selector_from_name("initializer")
        call_data = [key_pair.public_key]

        return compute_address(
            class_hash=BRAAVOS_PROXY_CLASS_HASH,
            constructor_calldata=[BRAAVOS_IMPLEMENTATION_CLASS_HASH, selector, len(call_data), *call_data],
            salt=key_pair.public_key
        )

    @staticmethod
    def get_argent_address(key_pair, cairo_version) -> int:
        selector = get_selector_from_name("initialize")
        call_data = [key_pair.public_key, 0]

        if cairo_version:
            proxy_class_hash = ARGENT_IMPLEMENTATION_CLASS_HASH_NEW
            constructor_calldata = call_data
        else:
            proxy_class_hash = ARGENT_PROXY_CLASS_HASH
            constructor_calldata = [ARGENT_IMPLEMENTATION_CLASS_HASH, selector, len(call_data), *call_data]

        return compute_address(
            class_hash=proxy_class_hash,
            constructor_calldata=constructor_calldata,
            salt=key_pair.public_key
        )

    @staticmethod
    def round_amount(min_amount: float, max_amount:float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals)

    @staticmethod
    def get_normalize_error(error):
        if 'message' in error.args[0]:
            error = error.args[0]['message']
        return error

    async def initialize_evm_client(self, private_key, chain_id):
        from modules import Client
        from functions import get_network_by_chain_id
        evm_client = Client(self.account_name, private_key,
                            get_network_by_chain_id(chain_id), self.proxy_init)
        return evm_client

    async def get_decimals(self, token_name:str):
        contract = TOKENS_PER_CHAIN[self.network.name][token_name]
        return (await self.account.client.call_contract(self.prepare_call(contract, 'decimals')))[0]

    async def get_normalize_amount(self, token_name, amount_in_wei):
        decimals = await self.get_decimals(token_name)
        return float(amount_in_wei / 10 ** decimals)

    async def get_smart_amount(self, settings:tuple, token_name:str = 'ETH'):
        if isinstance(settings[0], str):
            _, amount, _ = await self.get_token_balance(token_name)
            percent = round(random.uniform(float(settings[0]), float(settings[1])), 6) / 100
            amount = round(amount * percent, 6)
        else:
            amount = self.round_amount(*settings)
        return amount

    async def get_bridge_data(self, chain_from_id: int, module_name: str):
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

    async def new_client(self, chain_id):
        from functions import get_network_by_chain_id
        from modules import Client
        if chain_id != 9:
            client = Client
        else:
            client = StarknetClient
        new_client = client(self.account_name, self.private_key,
                            get_network_by_chain_id(chain_id), self.proxy_init)
        return new_client

    async def wait_for_receiving(self, chain_id:int, old_balance:int = 0, token_name:str = 'ETH', sleep_time:int = 30,
                                 timeout: int = 1200, check_balance_on_dst:bool = False):
        client = await self.new_client(chain_id)
        try:
            if check_balance_on_dst:
                old_balance = await self.account.get_balance()
                return old_balance

            self.logger_msg(*self.acc_info, msg=f'Waiting ETH to receive')

            t = 0
            new_eth_balance = 0
            while t < timeout:
                try:
                    new_eth_balance = await self.account.get_balance()
                except:
                    pass

                if new_eth_balance > old_balance:
                    amount = round((new_eth_balance - old_balance) / 10 ** 18, 6)
                    self.logger_msg(*self.acc_info, msg=f'{amount} {token_name} was received', type_msg='success')
                    return True
                else:
                    self.logger_msg(*self.acc_info, msg=f'Still waiting {token_name} to receive...', type_msg='warning')
                    await asyncio.sleep(sleep_time)
                    t += sleep_time
        except Exception:
            raise RuntimeError(f'{token_name} has not been received within {timeout} seconds')
        finally:
            await client.session.close()

    @staticmethod
    def prepare_call(contract_address:int, selector_name:str, calldata:list = None):
        if calldata is None:
            calldata = []
        return Call(
            to_addr=contract_address,
            selector=get_selector_from_name(selector_name),
            calldata=[int(data) for data in calldata],
        )

    async def get_contract(self, contract_address: int, proxy_config: bool = False):
        return await Contract.from_address(address=contract_address, provider=self.account, proxy_config=proxy_config)

    async def get_token_balance(self, token_name: str = 'ETH', check_symbol: bool = True) -> [float, int, str]:
        contract = TOKENS_PER_CHAIN[self.network.name][token_name]
        amount_in_wei = (await self.account.client.call_contract(self.prepare_call(contract, 'balanceOf',
                                                                                   [self.address])))[0]

        decimals = (await self.account.client.call_contract(self.prepare_call(contract, 'decimals')))[0]

        if check_symbol:
            symbol = decode_shortstring((await self.account.client.call_contract(
                self.prepare_call(contract, 'symbol')))[0])

            return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
        return amount_in_wei, amount_in_wei / 10 ** decimals, ''

    def get_approve_call(self, token_address: int, spender_address: int,
                         amount_in_wei: int = None, unlim_approve: bool = UNLIMITED_APPROVE) -> Call:
        return self.prepare_call(token_address, 'approve', [
            spender_address,
            2 ** 128 - 1 if unlim_approve else amount_in_wei,
            2 ** 128 - 1 if unlim_approve else 0
        ])

    async def send_transaction(self, *calls:list, check_hash:bool = False,
                               hash_for_check:int = None, mint_shits:bool = False, max_fee:float = 0):
        try:
            tx_hash = hash_for_check
            if not check_hash:
                if not mint_shits:
                    tx_hash = (await self.account.execute(
                        calls=calls,
                        auto_estimate=True
                    )).transaction_hash
                else:
                    tx_hash = (await self.account.execute(
                        calls=calls,
                        auto_estimate=False,
                        max_fee=max_fee,
                        nonce=1,
                    )).transaction_hash

            await self.account.client.wait_for_tx(tx_hash, check_interval=5, retries=1000)
            self.logger_msg(
                *self.acc_info, msg=f'Transaction was successful: {self.explorer}tx/{hex(tx_hash)}', type_msg='success')
            return True

        except Exception as error:
            raise RuntimeError(f'Send transaction | {self.get_normalize_error(error)}')
