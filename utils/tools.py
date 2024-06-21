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
from aiohttp import ClientSession, ClientProxyConnectionError, ClientHttpProxyError, ClientResponseError
from python_socks import ProxyError
from termcolor import cprint
from datetime import datetime, timedelta
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import ContractLogicError

from settings import SLEEP_TIME_RETRY, MAXIMUM_RETRY, EXCEL_PASSWORD, EXCEL_PAGE_NAME, SLEEP_TIME_MODULES, GAS_CONTROL, \
    SLEEP_TIME_GAS, MAXIMUM_GWEI


async def sleep(self, min_time=None, max_time=None):
    if not min_time:
        min_time, max_time = SLEEP_TIME_MODULES
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
            proxy = row["Proxy"]
            cex_address = row['CEX address']
            accounts_data[int(index) + 1] = {
                "account_name": account_name,
                "private_key": private_key,
                "proxy": proxy,
                "cex_wallet": cex_address,
            }

        acc_name, priv_key_evm, priv_key, proxy, cex_wallet = [], [], [], [], []
        for k, v in accounts_data.items():
            if isinstance(v['account_name'], str):
                acc_name.append(v['account_name'])
                priv_key.append(v['private_key'])
            proxy.append(v['proxy'] if isinstance(v['proxy'], str) else None)
            cex_wallet.append(v['cex_wallet'] if isinstance(v['cex_wallet'], str) else None)

        proxy = [item for item in proxy if item is not None]
        cex_wallet = [item for item in cex_wallet if item is not None]

        return acc_name, priv_key, proxy, cex_wallet


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


def create_cex_withdrawal_list():
    from config import ACCOUNT_NAMES, OKX_WALLETS
    okx_data = {}

    if ACCOUNT_NAMES and OKX_WALLETS:
        with open('./data/services/cex_withdraw_list.json', 'w') as file:
            for account_name, okx_wallet in zip(ACCOUNT_NAMES, OKX_WALLETS):
                okx_data[account_name] = okx_wallet
            json.dump(okx_data, file, indent=4)
        cprint('✅ Successfully added and saved CEX wallets data', 'light_blue')
        cprint('⚠️ Check all CEX deposit wallets by yourself to avoid problems', 'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def get_wallet_for_deposit(self):
    try:
        with open('./data/services/cex_withdraw_list.json') as file:
            from json import load
            cex_withdraw_list = load(file)
            cex_wallet = cex_withdraw_list[self.client.account_name]
        return cex_wallet
    except json.JSONDecodeError:
        raise RuntimeError(f"Bad data in cex_wallet_list.json")
    except Exception as error:
        raise RuntimeError(f'There is no wallet listed for deposit to CEX: {error}')


def helper(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        from modules.interfaces import (
            PriceImpactException, BlockchainException, SoftwareException, SoftwareExceptionWithoutRetry,
            BlockchainExceptionWithoutRetry, CriticalException, SoftwareExceptionHandled
        )

        attempts = 0
        stop_flag = False
        infinity_flag = False
        no_sleep_flag = False
        try:
            while attempts <= MAXIMUM_RETRY and not infinity_flag:
                try:
                    return await func(self, *args, **kwargs)
                except (
                        PriceImpactException, BlockchainException, SoftwareException, SoftwareExceptionWithoutRetry,
                        SoftwareExceptionHandled, BlockchainExceptionWithoutRetry, ValueError, ContractLogicError,
                        ClientProxyConnectionError, TimeoutError, ClientHttpProxyError, ProxyError,
                        ClientResponseError, CriticalException, KeyError
                ) as err:
                    error = err
                    attempts += 1
                    traceback.print_exc()
                    msg = f'{error} | Try[{attempts}/{MAXIMUM_RETRY + 1}]'

                    if isinstance(error, KeyError):
                        stop_flag = True
                        msg = f"Setting '{error}' for this module is not exist in software!"

                    elif isinstance(error, SoftwareExceptionHandled):
                        self.logger_msg(
                            *self.client.acc_info, msg=f"Insufficient balances in all networks!", type_msg='warning'
                        )
                        return True

                    elif 'StatusCode.UNAVAILABLE' in str(error):
                        msg = f'Rate limit exceeded. Will try again in 1 min...'
                        await asyncio.sleep(60)
                        no_sleep_flag = True

                    elif 'rate limit' in str(error) or '429' in str(error):
                        msg = f'Rate limit exceeded. Will try again in 5 min...'
                        await asyncio.sleep(300)
                        no_sleep_flag = True

                    elif 'StatusCode.UNAVAILABLE' in str(error):
                        msg = f'RPC got autism response, will try again in 10 second...'
                        await asyncio.sleep(10)
                        no_sleep_flag = True

                    elif isinstance(error, (
                            ClientProxyConnectionError, TimeoutError, ClientHttpProxyError, ProxyError,
                            ClientResponseError
                    )):
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Connection to RPC is not stable. Will try again in 1 min...",
                            type_msg='warning'
                        )
                        await self.client.change_rpc()
                        await asyncio.sleep(60)
                        attempts -= 1
                        no_sleep_flag = True

                    elif isinstance(error, CriticalException):
                        raise error

                    elif isinstance(error, (SoftwareExceptionWithoutRetry, BlockchainExceptionWithoutRetry)):
                        stop_flag = True
                        msg = f'{error}'

                    elif isinstance(error, BlockchainException):
                        if 'insufficient funds' not in str(error):
                            self.logger_msg(
                                self.client.account_name,
                                None, msg=f'Maybe problem with node: {self.client.rpc}', type_msg='warning')
                            await self.client.change_rpc()

                    self.logger_msg(self.client.account_name, None, msg=msg, type_msg='error')

                    if stop_flag:
                        break

                    if attempts > MAXIMUM_RETRY and not infinity_flag:
                        self.logger_msg(
                            self.client.account_name, None,
                            msg=f"Tries are over, software will stop module\n", type_msg='error'
                        )
                    else:
                        if not no_sleep_flag:
                            await sleep(self, *SLEEP_TIME_RETRY)

                except Exception as error:
                    attempts += 1
                    msg = f'Unknown Error. Description: {error} | Try[{attempts}/{MAXIMUM_RETRY + 1}]'
                    self.logger_msg(self.client.account_name, None, msg=msg, type_msg='error')
                    traceback.print_exc()

                    if attempts > MAXIMUM_RETRY and not infinity_flag:
                        self.logger_msg(
                            self.client.account_name, None,
                            msg=f"Tries are over, software will stop module\n", type_msg='error'
                        )
        finally:
            await self.client.session.close()
        return False
    return wrapper


def get_max_gwei_setting():
    file_path = './data/services/maximum_gwei.json'
    data = {}

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data['maximum_gwei'] = MAXIMUM_GWEI

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return data['maximum_gwei']


def gas_checker(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if GAS_CONTROL:
            await asyncio.sleep(1)
            print()
            counter = 0

            self.logger_msg(self.client.account_name, None, f"Checking for gas price")

            w3 = AsyncWeb3(AsyncHTTPProvider(
                random.choice(self.client.network.rpc), request_kwargs=self.client.request_kwargs
            ))

            while True:
                try:
                    gas = round(AsyncWeb3.from_wei(await w3.eth.gas_price, 'gwei'), 3)

                    if gas < get_max_gwei_setting():

                        self.logger_msg(
                            self.client.account_name, None, f"{gas} Gwei | Gas price is good", type_msg='success')
                        return await func(self, *args, **kwargs)

                    else:
                        counter += 1
                        self.logger_msg(
                            self.client.account_name, None,
                            f"{gas} Gwei | Gas is too high. Next check in {SLEEP_TIME_GAS} second", type_msg='warning')

                        await asyncio.sleep(SLEEP_TIME_GAS)
                except (
                        ClientProxyConnectionError, TimeoutError, ClientHttpProxyError, ProxyError, ClientResponseError
                ):
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Connection to RPC is not stable. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
        return await func(self, *args, **kwargs)

    return wrapper


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
