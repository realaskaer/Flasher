import json
import random
import asyncio

from modules import Logger
from utils.networks import EthereumRPC
from web3 import AsyncWeb3, AsyncHTTPProvider
from functions import get_network_by_chain_id
from utils.tools import clean_gwei_file
from utils.route_generator import AVAILABLE_MODULES_INFO, get_func_by_name
from config import ACCOUNT_NAMES, PRIVATE_KEYS_EVM, PRIVATE_KEYS, PROXIES
from settings import (USE_PROXY, WALLETS_TO_WORK, GLOBAL_NETWORK,
                      ACCOUNTS_IN_STREAM, SLEEP_TIME_STREAM, SLEEP_TIME, SLEEP_MODE)

BRIDGE_NAMES = ['bridge_rhino', 'bridge_layerswap', 'bridge_orbiter', 'bridge_across',
                'bridge_native', 'withdraw_native_bridge']


class Runner(Logger):
    @staticmethod
    def get_wallets_batch(account_list: tuple = None):
        range_count = range(account_list[0], account_list[1])
        account_names = [ACCOUNT_NAMES[i - 1] for i in range_count]
        accounts = [PRIVATE_KEYS[i - 1] for i in range_count]
        return zip(account_names, accounts)

    @staticmethod
    def get_wallets():
        if WALLETS_TO_WORK == 0:
            accounts_data = zip(ACCOUNT_NAMES, PRIVATE_KEYS)

        elif isinstance(WALLETS_TO_WORK, int):
            accounts_data = zip([ACCOUNT_NAMES[WALLETS_TO_WORK - 1]], [PRIVATE_KEYS[WALLETS_TO_WORK - 1]])

        elif isinstance(WALLETS_TO_WORK, tuple):
            account_names = [ACCOUNT_NAMES[i - 1] for i in WALLETS_TO_WORK]
            accounts = [PRIVATE_KEYS[i - 1] for i in WALLETS_TO_WORK]
            accounts_data = zip(account_names, accounts)

        elif isinstance(WALLETS_TO_WORK, list):
            range_count = range(WALLETS_TO_WORK[0], WALLETS_TO_WORK[1] + 1)
            account_names = [ACCOUNT_NAMES[i - 1] for i in range_count]
            accounts = [PRIVATE_KEYS[i - 1] for i in range_count]
            accounts_data = zip(account_names, accounts)
        else:
            accounts_data = []

        return list(accounts_data)

    @staticmethod
    def load_routes():
        with open('./data/services/wallets_progress.json', 'r') as f:
            return json.load(f)

    async def smart_sleep(self, account_name, account_number, accounts_delay=False):
        if SLEEP_MODE:
            if accounts_delay:
                duration = random.randint(*tuple(x * account_number for x in SLEEP_TIME_STREAM))
            else:
                duration = random.randint(*SLEEP_TIME)
            self.logger_msg(account_name, None, f"💤 Sleeping for {duration} seconds\n")
            await asyncio.sleep(duration)

    def update_step(self, account_name, step):
        wallets = self.load_routes()
        wallets[str(account_name)]["current_step"] = step
        with open('./data/services/wallets_progress.json', 'w') as f:
            json.dump(wallets, f, indent=4)

    async def check_proxies_status(self):
        tasks = []
        for proxy in PROXIES:
            tasks.append(self.check_proxy_status(None, proxy=proxy))
        await asyncio.gather(*tasks)

    async def check_proxy_status(self, account_name: str = None, proxy: str = None, silence: bool = False):
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(EthereumRPC.rpc),
                                             request_kwargs={"proxy": f"http://{proxy}"}))
            if await w3.is_connected():
                if not silence:
                    info = f'Proxy {proxy[proxy.find("@"):]} successfully connected to Ethereum RPC'
                    self.logger_msg(account_name, None, info, 'success')
                return True
            self.logger_msg(account_name, None, f"Proxy: {proxy} can`t connect to Ethereum RPC", 'error')
            return False
        except Exception as error:
            self.logger_msg(account_name, None, f"Bad proxy: {proxy} | Error: {error}", 'error')
            return False

    def get_proxy_for_account(self, account_name):
        if USE_PROXY:
            try:
                account_number = ACCOUNT_NAMES.index(account_name) + 1
                num_proxies = len(PROXIES)
                return PROXIES[account_number % num_proxies]
            except Exception as error:
                self.logger_msg(account_name, None, f"Bad data in proxy, but you want proxy! Error: {error}", 'error')
                raise RuntimeError("Proxy error")

    async def run_account_modules(self, account_name, private_key, network, proxy, batch_mode:bool = False,
                                  index:int = 1):
        try:
            if batch_mode:
                route = self.load_routes().get('Main 1', {}).get('route')

            else:
                route = self.load_routes().get(str(account_name), {}).get('route')
            if not route:
                raise RuntimeError(f"No route available")

            route = [[i, 0] for i in route]
            current_step = 0
            module_info = AVAILABLE_MODULES_INFO

            await self.smart_sleep(account_name, index, accounts_delay=True)

            while current_step < len(route):
                module_name = route[current_step][0]
                module_func = get_func_by_name(module_name)
                self.logger_msg(account_name, None, f"🚀 Launch module: {module_info[module_func][2]}")

                module_input_data = [account_name, private_key, network, proxy]
                if route[current_step][0] in BRIDGE_NAMES:
                    module_input_data.append({"stark_key": private_key,
                                              "evm_key": PRIVATE_KEYS_EVM[PRIVATE_KEYS.index(private_key)]
                                              if GLOBAL_NETWORK == 9 else private_key})

                try:
                    result = await module_func(*module_input_data)
                except Exception as error:
                    info = f"Module name: {module_info[module_func][2]} | Error {error}"
                    self.logger_msg(
                        account_name, None, f"Module crashed during the route: {info}", type_msg='error')
                    result = False

                if result:
                    self.update_step(account_name, current_step + 1)
                    current_step += 1
                else:
                    break

                await self.smart_sleep(account_name, account_number=1)

            self.logger_msg(account_name, None, f"Wait for other wallets in stream!\n", 'info')

        except Exception as error:
            self.logger_msg(account_name, None, f"Error during the route! Error: {error}\n", 'error')

    async def run_parallel(self):
        selected_wallets = list(self.get_wallets())
        num_accounts = len(selected_wallets)
        accounts_per_stream = ACCOUNTS_IN_STREAM
        num_streams, remainder = divmod(num_accounts, accounts_per_stream)

        for stream_index in range(num_streams + (remainder > 0)):
            start_index = stream_index * accounts_per_stream
            end_index = (stream_index + 1) * accounts_per_stream if stream_index < num_streams else num_accounts

            accounts = selected_wallets[start_index:end_index]

            tasks = []

            for index, data in enumerate(accounts, 1):
                account_name, private_key = data
                tasks.append(asyncio.create_task(
                    self.run_account_modules(
                        account_name, private_key, get_network_by_chain_id(GLOBAL_NETWORK),
                        self.get_proxy_for_account(account_name), index=index)))

            await asyncio.gather(*tasks)

            self.logger_msg(None, None, f"Wallets in stream completed their tasks, launching next stream\n", 'success')

        self.logger_msg(None, None, f"All wallets completed their tasks!\n", 'success')

    async def run_accounts(self):
        clean_gwei_file()
        await self.run_parallel()
