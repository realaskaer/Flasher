import io
import json
import os
import random
import asyncio
import functools
import traceback

import msoffcrypto
import pandas as pd

from getpass import getpass
from aiohttp import ClientSession
from termcolor import cprint
from datetime import datetime, timedelta
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from settings import (
    GLOBAL_NETWORK,
    SLEEP_TIME_RETRY,
    MAXIMUM_RETRY,
    EXCEL_PASSWORD,
    EXCEL_PAGE_NAME
)


async def sleep(self, min_time, max_time):
    duration = random.randint(min_time, max_time)
    print()
    self.logger_msg(*self.client.acc_info, msg=f"💤 Sleeping for {duration} seconds")
    await asyncio.sleep(duration)


def get_accounts_data(page_name:str = None):
    decrypted_data = io.BytesIO()
    sheet_page_name = page_name if page_name else EXCEL_PAGE_NAME
    with open('./data/accounts_data.xlsx', 'rb') as file:
        if EXCEL_PASSWORD:
            cprint('⚔️ Enter the password degen', color='light_blue')
            password = getpass()
            office_file = msoffcrypto.OfficeFile(file)

            try:
                office_file.load_key(password=password)
            except msoffcrypto.exceptions.DecryptionError:
                cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️\n', color='light_red', attrs=["blink"])
                raise DecryptionError('Incorrect password')

            try:
                office_file.decrypt(decrypted_data)
            except msoffcrypto.exceptions.InvalidKeyError:
                cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️\n', color='light_red', attrs=["blink"])
                raise InvalidKeyError('Incorrect password')

            except msoffcrypto.exceptions.DecryptionError:
                cprint('\n⚠️ Set password on your Excel file first! ⚠️\n', color='light_red', attrs=["blink"])
                raise DecryptionError('Excel without password')

            office_file.decrypt(decrypted_data)

            try:
                wb = pd.read_excel(decrypted_data, sheet_name=sheet_page_name)
            except ValueError as error:
                cprint('\n⚠️ Wrong page name! ⚠️\n', color='light_red', attrs=["blink"])
                raise ValueError(f"{error}")
        else:
            try:
                wb = pd.read_excel(file, sheet_name=sheet_page_name)
            except ValueError as error:
                cprint('\n⚠️ Wrong page name! ⚠️\n', color='light_red', attrs=["blink"])
                raise ValueError(f"{error}")

        accounts_data = {}
        for index, row in wb.iterrows():
            account_name = row["Name"]
            private_key = row["Private Key"]
            private_key_evm = row["Private Key EVM"] if GLOBAL_NETWORK == 9 else 0x123
            proxy = row["Proxy"]
            cex_address = row['CEX address']
            accounts_data[int(index) + 1] = {
                "account_name": account_name,
                "private_key_evm": private_key_evm,
                "private_key": private_key,
                "proxy": proxy,
                "cex_wallet": cex_address,
            }

        acc_name, priv_key_evm, priv_key, proxy, cex_wallet = [], [], [], [], []
        for k, v in accounts_data.items():
            if isinstance(v['account_name'], str):
                acc_name.append(v['account_name'])
                priv_key_evm.append(v['private_key_evm'])
                priv_key.append(v['private_key'])
            proxy.append(v['proxy'] if isinstance(v['proxy'], str) else None)
            cex_wallet.append(v['cex_wallet'] if isinstance(v['cex_wallet'], str) else None)

        proxy = [item for item in proxy if item is not None]
        cex_wallet = [item for item in cex_wallet if item is not None]

        return acc_name, priv_key_evm, priv_key, proxy, cex_wallet


def clean_stark_file():
    with open('./data/services/stark_data.json', 'w') as file:
        file.truncate(0)


def clean_progress_file():
    with open('./data/services/wallets_progress.json', 'w') as file:
        file.truncate(0)


def clean_gwei_file():
    with open('./data/services/maximum_gwei.json', 'w') as file:
        file.truncate(0)


def clean_action_file():
    with open('./data/services/action_flag.json', 'w') as file:
        file.truncate(0)


def check_progress_file():
    file_path = './data/services/wallets_progress.json'

    if os.path.getsize(file_path) > 0:
        return True
    else:
        return False


def save_buy_tx(account_name, amount):
    file_path = './data/services/memcoin_buys.json'
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError:
        data = {}

    data[account_name] = {
        "amount": amount
    }

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def drop_date():
    current_date = datetime.now()
    random_months = random.randint(1, 4)

    future_date = current_date + timedelta(days=random_months * 30)

    return future_date.strftime("%Y.%m.%d")


def create_okx_withdrawal_list():
    from config import ACCOUNT_NAMES, OKX_WALLETS
    okx_data = {}

    if ACCOUNT_NAMES and OKX_WALLETS:
        with open('./data/services/okx_withdraw_list.json', 'w') as file:
            for account_name, okx_wallet in zip(ACCOUNT_NAMES, OKX_WALLETS):
                okx_data[account_name] = okx_wallet
            json.dump(okx_data, file, indent=4)
        cprint('✅ Successfully added and saved OKX wallets data', 'light_blue')
        cprint('⚠️ Check all OKX deposit wallets by yourself to avoid problems', 'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def helper(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        attempts = 0
        try:
            while True:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as error:
                    self.logger_msg(
                        self.client.account_name,
                        None, msg=f"{error} | Try[{attempts + 1}/{MAXIMUM_RETRY + 1}]", type_msg='error'
                    )
                    attempts += 1
                    if attempts > MAXIMUM_RETRY:
                        break
                    await sleep(self, *SLEEP_TIME_RETRY)
        finally:
            await self.client.session.close()
        self.logger_msg(self.client.account_name,
                        None, msg=f"Tries are over, launching next module.\n", type_msg='error')
        return False
    return wrapper


async def prepare_wallets():
    from config import ACCOUNT_NAMES, PRIVATE_KEYS
    # from modules.stark_client import StarknetClient
    # from utils.networks import StarknetRPC
    #
    # clean_stark_file()
    #
    # async def prepare_wallet(account_name, private_key):
    #
    #     if await StarknetClient.check_stark_data_file(account_name):
    #         return
    #
    #     try:
    #         key_pair = KeyPair.from_private_key(private_key)
    #         w3 = FullNodeClient(node_url=random.choice(StarknetRPC.rpc))
    #
    #         possible_addresses = [(StarknetClient.get_argent_address(key_pair, 1), 0, 1),
    #                               (StarknetClient.get_braavos_address(key_pair), 1, 0),
    #                               (StarknetClient.get_argent_address(key_pair, 0), 0, 0)]
    #
    #         for address, wallet_type, cairo_version in possible_addresses:
    #             account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)
    #             try:
    #                 result = await account.client.get_class_hash_at(address)
    #
    #                 if result:
    #                     await StarknetClient.save_stark_data_file(account_name, address, wallet_type, cairo_version)
    #             except ClientError:
    #                 pass
    #     except Exception as error:
    #         raise RuntimeError(f'Wallet is not deployed! Error: {error}')
    #
    # tasks = []
    # for account_name, private_key in zip(ACCOUNT_NAMES, PRIVATE_KEYS):
    #     tasks.append(asyncio.create_task(prepare_wallet(account_name, private_key)))
    # await asyncio.gather(*tasks)


async def get_eth_price():
    url = 'https://api.coingecko.com/api/v3/simple/price'

    params = {
        'ids': 'ethereum',
        'vs_currencies': 'usd'
    }

    async with ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            data = await response.json()
            if response.status == 200:
                return data['ethereum']['usd']
