import asyncio
import copy
import json
import random
import traceback

import aiohttp
import python_socks
from eth_account.messages import encode_structured_data

from config import TAIKO_ABI, ERC20_ABI, ZK_ABI, CLAIM_ABI, CEX_WRAPPED_ID, \
    OKX_NETWORKS_NAME, OMNICHAIN_WRAPED_NETWORKS, COINGECKO_TOKEN_API_NAMES, CHAIN_NAME, TOKENS_PER_CHAIN
from modules import Logger, Aggregator, Client
from modules.interfaces import CriticalException, SoftwareException, SoftwareExceptionWithoutRetry, \
    SoftwareExceptionHandled
from settings import TWO_CAPTCHA_API_KEY, ZRO_DST_CHAIN, OKX_DEPOSIT_DATA, OKX_WITHDRAW_DATA, ACROSS_CHAIN_ID_FROM, \
    ACROSS_TOKEN_NAME, ACROSS_AMOUNT_LIMITER, BUNGEE_CHAIN_ID_FROM, BUNGEE_TOKEN_NAME, BUNGEE_AMOUNT_LIMITER, \
    LAYERSWAP_CHAIN_ID_FROM, LAYERSWAP_TOKEN_NAME, LAYERSWAP_AMOUNT_LIMITER, NITRO_TOKEN_NAME, NITRO_AMOUNT_LIMITER, \
    NITRO_CHAIN_ID_FROM, ORBITER_CHAIN_ID_FROM, ORBITER_TOKEN_NAME, ORBITER_AMOUNT_LIMITER, OWLTO_CHAIN_ID_FROM, \
    OWLTO_TOKEN_NAME, OWLTO_AMOUNT_LIMITER, RHINO_CHAIN_ID_FROM, RELAY_CHAIN_ID_FROM, NATIVE_CHAIN_ID_FROM, \
    RELAY_TOKEN_NAME, RELAY_AMOUNT_LIMITER, RHINO_TOKEN_NAME, RHINO_AMOUNT_LIMITER, NATIVE_TOKEN_NAME, \
    NATIVE_AMOUNT_LIMITER, BRIDGE_SWITCH_CONTROL
from eth_abi import encode
from utils.tools import helper, get_wallet_for_deposit, sleep, gas_checker


class Custom(Logger, Aggregator):
    def __init__(self, client: Client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.stop_flag = False
        self.signed_tx = None

    async def swap(self):
        pass

    # async def buy_node_util(self, contract_address, price, index, approve_mode, tx_params=None):
    #
    #     node_contract = self.client.get_contract(contract_address, AETHIR_ABI)
    #
    #     if not isinstance(NODE_COUNT, int):
    #         raise RuntimeError('NODE_COUNT should ne a digit! (NODE_COUNT = 10)')
    #
    #     if not approve_mode:
    #         self.logger_msg(*self.client.acc_info, msg=f"Trying to buy Carv Node Tier #{index}")
    #     else:
    #         self.logger_msg(*self.client.acc_info, msg=f"Approve for buying Carv Node Tier #{index}")
    #
    #     total_price = int(price * NODE_COUNT * 10 ** 18)
    #     total_count = int(NODE_COUNT * 10 ** 18)
    #     ref_flag = False
    #
    #     weth_address = TOKENS_PER_CHAIN['Arbitrum']['WETH']
    #
    #     if approve_mode:
    #         result = await self.client.check_for_approved(weth_address, node_contract.address, without_bal_check=True)
    #         await asyncio.sleep(1)
    #         return result
    #
    #     try:
    #         transaction = await node_contract.functions.whitelistedPurchaseWithCode(
    #             total_price,
    #             [],
    #             total_price,
    #             'crypto_earn_important',
    #         ).build_transaction(tx_params)
    #         ref_flag = True
    #     except Exception as error:
    #         try:
    #             self.logger_msg(*self.client.acc_info, msg=f"Method#1. {error}", type_msg='error')
    #             transaction = await node_contract.functions.whitelistedPurchaseWithCode(
    #                 total_price,
    #                 [],
    #                 total_count,
    #                 'crypto_earn_important',
    #             ).build_transaction(tx_params)
    #             ref_flag = True
    #         except Exception as error:
    #             if NODE_TRYING_WITHOUT_REF:
    #                 try:
    #                     self.logger_msg(*self.client.acc_info, msg=f"Method#2. {error}", type_msg='error')
    #                     transaction = await node_contract.functions.whitelistedPurchase(
    #                         total_price,
    #                         [],
    #                         total_count,
    #                     ).build_transaction(tx_params)
    #                 except Exception as error:
    #                     try:
    #                         self.logger_msg(*self.client.acc_info, msg=f"Method#3. {error}", type_msg='error')
    #                         transaction = await node_contract.functions.whitelistedPurchase(
    #                             total_price,
    #                             [],
    #                             total_price,
    #                         ).build_transaction(tx_params)
    #                     except Exception as error:
    #                         self.logger_msg(*self.client.acc_info, msg=f"Method#4. {error}", type_msg='error')
    #                         return False
    #             else:
    #                 self.logger_msg(*self.client.acc_info, msg=f"Method#2. {error}", type_msg='error')
    #                 return False
    #
    #     tx = await self.client.send_transaction(transaction)
    #
    #     if tx:
    #         if ref_flag:
    #             self.logger_msg(
    #                 *self.client.acc_info, msg=f"Tier #{index} was bought with 10% discount", type_msg='success'
    #             )
    #         else:
    #             self.logger_msg(
    #                 *self.client.acc_info, msg=f"Tier #{index} was bought", type_msg='success'
    #             )
    #         return True
    #     return False
    #
    # @helper
    # async def buy_node(self, approve_mode: bool = False):
    #     nodes_data = {
    #         1: ("0x80adA4D9F18996c19df7d07aCfE78f9460BBC151", 0.1316),
    #         2: ("0x82720570AC1847FD161b5A01Fe6440c316e5742c", 0.1580),
    #         3: ("0x3F3C6DE3Bbe1F2fdFb4B43a49e599885B7Fb1a27", 0.1817),
    #         4: ("0xc674BEB2f5Cd94A748589A9Dadd838b9E09AABD4", 0.2071),
    #         5: ("0xF8a8A71d90f1AE2F17Aa4eE9319820B5F394f629", 0.2340),
    #         6: ("0x125711d6f0AAc9DFFEd75AD2B8C51bDaF5FAEd71", 0.2633),
    #         7: ("0x3371b74beC1dE3E115A4148956F94f55bEA8cD00", 0.2962),
    #         8: ("0xa1D3632C9Dc73e8EcEBAe99a8Ea00F50F226A8B9", 0.3332),
    #         9: ("0xD7C3E0C20Ab22f1e9A59e764B1b562E1dD7438B0", 0.3749)
    #     }
    #
    #     if NODE_TIER_BUY != 0:
    #         new_nodes_data = copy.deepcopy(nodes_data[NODE_TIER_BUY])
    #     else:
    #         new_nodes_data = copy.deepcopy(nodes_data)
    #
    #     if approve_mode:
    #         for index in range(1, 10):
    #             contract_address, price = nodes_data[index]
    #             await self.buy_node_util(
    #                 contract_address=contract_address, price=price, index=index, approve_mode=approve_mode
    #             )
    #         return True
    #
    #     tx_params = await self.client.prepare_transaction()
    #
    #     if isinstance(new_nodes_data, tuple):
    #         contract_address, price = new_nodes_data
    #         while True:
    #             result = await self.buy_node_util(
    #                 contract_address=contract_address, price=price, index=NODE_TIER_BUY, approve_mode=False,
    #                 tx_params=tx_params
    #             )
    #             if result:
    #                 break
    #     else:
    #         result = False
    #         while True:
    #             for index in range(1, NODE_TIER_MAX + 1):
    #                 contract_address, price = new_nodes_data[index]
    #                 result = await self.buy_node_util(
    #                     contract_address=contract_address, price=price, index=index, approve_mode=False,
    #                     tx_params=tx_params
    #                 )
    #
    #                 if not result:
    #                     self.logger_msg(
    #                         *self.client.acc_info, msg=f"Can`t buy Carv Node Tier #{index}", type_msg='warning'
    #                     )
    #                 else:
    #                     break
    #
    #             if result:
    #                 break
    #
    #     return True

    async def balance_searcher(
            self, chains, tokens=None, omni_check: bool = True, native_check: bool = False, silent_mode: bool = False,
            balancer_mode: bool = False, random_mode: bool = False, wrapped_tokens: bool = False,
            need_token_name: bool = False, raise_handle: bool = False, without_error: bool = False
    ):
        index = 0
        clients = []

        while True:
            try:

                clients = [
                    await self.client.new_client(OMNICHAIN_WRAPED_NETWORKS[chain] if omni_check else chain)
                    for chain in chains
                ]

                if native_check:
                    tokens = [client.token for client in clients]
                elif wrapped_tokens:
                    tokens = [f'W{client.token}' for client in clients]

                balances = [
                    await client.get_token_balance(omnicheck=omni_check, token_name=token, without_error=without_error)
                    for client, token in zip(clients, tokens)
                ]

                flag = all(balance_in_wei == 0 for balance_in_wei, _, _ in balances)

                if raise_handle and flag:
                    raise SoftwareExceptionHandled('Insufficient balances in all networks!')

                if flag and not balancer_mode:
                    raise SoftwareException('Insufficient balances in all networks!')

                balances_in_usd = []
                token_prices = {}
                for balance_in_wei, balance, token_name in balances:
                    token_price = 1
                    if 'USD' not in token_name:
                        if token_name not in token_prices:
                            if token_name != '':
                                token_price = await self.client.get_token_price(COINGECKO_TOKEN_API_NAMES[token_name])
                            else:
                                token_price = 0
                            token_prices[token_name] = token_price
                        else:
                            token_price = token_prices[token_name]
                    balance_in_usd = balance * token_price

                    if need_token_name:
                        balances_in_usd.append([balance_in_usd, token_price, token_name])
                    else:
                        balances_in_usd.append([balance_in_usd, token_price])

                if not random_mode:
                    index = balances_in_usd.index(max(balances_in_usd, key=lambda x: x[0]))
                else:
                    try:
                        index = balances_in_usd.index(random.choice(
                            [balance for balance in balances_in_usd if balance[0] > 0.2]
                        ))
                    except Exception as error:
                        if 'list index out of range' in str(error):
                            raise SoftwareExceptionWithoutRetry('All networks have lower 0.2$ of native')

                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()

                if not silent_mode:
                    clients[index].logger_msg(
                        *clients[index].acc_info,
                        msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
                        type_msg='success'
                    )

                return clients[index], index, balances[index][1], balances[index][0], balances_in_usd[index]

            except (aiohttp.client_exceptions.ClientProxyConnectionError, asyncio.exceptions.TimeoutError,
                    aiohttp.client_exceptions.ClientHttpProxyError, python_socks.ProxyError):
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Connection to RPC is not stable. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)
            except SoftwareException as error:
                raise error
            except SoftwareExceptionHandled as error:
                raise error
            except Exception as error:
                if 'list index out of range' in str(error):
                    traceback.print_exc()
                    raise error
                elif 'StatusCode.NOT_FOUND' in str(error):
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Your need to activate your account first! Withdraw some native tokens for it",
                        type_msg='warning'
                    )
                traceback.print_exc()
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Bad response from RPC. Will try again in 1 min... Error: {error}", type_msg='warning'
                )
                await asyncio.sleep(60)
            finally:
                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()

    @helper
    async def claim_taiko(self):
        claim_addresses = '0x30a0ee3f0f2c76ad9f0731a4c1c89d9e2cb10930'

        url = f"https://qa.trailblazer.taiko.xyz/api/claim?address={self.client.address}"

        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"123\", \"Chromium\";v=\"123\", \"Not.A/Brand\";v=\"23\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "referrer": "https://claim.taiko.xyz/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": "null",
            "method": "GET",
            "mode": "cors",
            "credentials": "omit"
        }

        response = await self.make_request(url=url, headers=headers)

        if response['address']:

            amount = self.client.to_wei(float(response['value']))
            proof = json.loads(response['proof'])

            self.logger_msg(*self.client.acc_info, msg=f'Claim {amount / 10 ** 18:.2f} TAIKO')
            claim_contract = self.client.get_contract(claim_addresses, TAIKO_ABI)

            transaction = await claim_contract.functions.claim(
                self.client.address,
                amount,
                proof
            ).build_transaction(await self.client.prepare_transaction())

            return await self.client.send_transaction(transaction)

        raise RuntimeError('You are not eligible to claim Taiko')

    async def transfer_taiko(self):

        taiko_contract = self.client.get_contract('0xA9d23408b9bA935c230493c40C73824Df71A0975', ERC20_ABI)

        dep_address = get_wallet_for_deposit(self)

        _, balance, _ = await self.client.get_token_balance('TAIKO', omnicheck=True)
        balance_in_wei = self.client.to_wei(balance)

        self.logger_msg(*self.client.acc_info, msg=f'Transfer {balance:.2f} TAIKO to {dep_address[:10]}...')

        transfer_tx = await taiko_contract.functions.transfer(
            self.client.w3.to_checksum_address(dep_address),
            balance_in_wei
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transfer_tx)

    async def get_zk_drop_info(self):
        url = f"https://api.zknation.io/eligibility?id={self.client.address}"
        
        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "content-type": "application/json",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"123\", \"Microsoft Edge\";v=\"123\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-api-key": "46001d8f026d4a5bb85b33530120cd38",
            "referrer": "https://claim.zknation.io/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "body": "null",
            "method": "GET",
            "mode": "cors",
            "credentials": "omit"
        }

        response = await self.make_request(url=url, headers=headers)

        if response['allocations']:
            merkle_index = int(response['allocations'][0]['merkleIndex'])
            amount_in_wei = int(response['allocations'][0]['tokenAmount'])
            merkle_proof = response['allocations'][0]['merkleProof']
            airdrop_id = response['allocations'][0]['airdrop']['id']
            contract_address = response['allocations'][0]['airdrop']['contractAddress']

            return amount_in_wei, merkle_index, merkle_proof, airdrop_id, contract_address

        raise RuntimeError('You are not eligible to claim ZK')

    async def get_delegate_zk_signature(self, timestamp):
         typed_data = {
            "types": {
                "EIP712Domain": [
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "version",
                        "type": "string"
                    },
                    {
                        "name": "chainId",
                        "type": "uint256"
                    },
                    {
                        "name": "verifyingContract",
                        "type": "address"
                    }
                ],
                "Delegation": [
                    {
                        "name": "owner",
                        "type": "address"
                    },
                    {
                        "name": "delegatee",
                        "type": "address"
                    },
                    {
                        "name": "nonce",
                        "type": "uint256"
                    },
                    {
                        "name": "expiry",
                        "type": "uint256"
                    }
                ]
            },
            "primaryType": "Delegation",
            "domain": {
                "name": "ZKsync",
                "version": "1",
                "chainId": 324,
                "verifyingContract": "0x5a7d6b2f92c77fad6ccabd7ee0624e64907eaf3e"
            },
            "message": {
                "owner": f"{self.client.address}",
                "delegatee": f"{self.client.address}",
                "nonce": 0,
                "expiry": timestamp
            }
         }

         text_encoded = encode_structured_data(typed_data)
         signature = self.client.w3.eth.account.sign_message(text_encoded, self.client.private_key).signature

         return self.client.w3.to_hex(signature)

    async def get_claim_zk_signature(self, amount_in_wei, merkle_index, contract_address, timestamp):
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "version",
                        "type": "string"
                    },
                    {
                        "name": "chainId",
                        "type": "uint256"
                    },
                    {
                        "name": "verifyingContract",
                        "type": "address"
                    }
                ],
                "ClaimAndDelegate": [
                    {
                        "name": "index",
                        "type": "uint256"
                    },
                    {
                        "name": "claimant",
                        "type": "address"
                    },
                    {
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "name": "delegatee",
                        "type": "address"
                    },
                    {
                        "name": "expiry",
                        "type": "uint256"
                    },
                    {
                        "name": "nonce",
                        "type": "uint256"
                    }
                ]
            },
            "primaryType": "ClaimAndDelegate",
            "domain": {
                "name": "ZkMerkleDistributor",
                "version": "1",
                "chainId": 324,
                "verifyingContract": contract_address
            },
            "message": {
                "index": merkle_index,
                "claimant": f"{self.client.address}",
                "amount": amount_in_wei,
                "delegatee": f"{self.client.address}",
                "nonce": 0,
                "expiry": timestamp
            }
        }

        text_encoded = encode_structured_data(typed_data)
        signature = self.client.w3.eth.account.sign_message(text_encoded, self.client.private_key).signature

        return self.client.w3.to_hex(signature)

    async def create_task_for_captcha(self):
        url = 'https://api.2captcha.com/createTask'

        payload = {
            "clientKey": TWO_CAPTCHA_API_KEY,
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "https://claim.zknation.io/",
                "websiteKey": "6LdvoMYpAAAAAFiId2WM4VHeOw10GpsvP2e15hSg",
            }
        }

        response = await self.make_request(method="POST", url=url, json=payload)

        if not response['errorId']:
            return response['taskId']
        raise RuntimeError('Bad request to 2Captcha(Create Task)')

    async def get_captcha_key(self, task_id):
        url = 'https://api.2captcha.com/getTaskResult'

        payload = {
            "clientKey": TWO_CAPTCHA_API_KEY,
            "taskId": task_id
        }

        total_time = 0
        timeout = 360
        while True:
            response = await self.make_request(method="POST", url=url, json=payload)

            if response['status'] == 'ready':
                return response['solution']['gRecaptchaResponse']

            total_time += 5
            await asyncio.sleep(5)

            if total_time > timeout:
                raise RuntimeError('Can`t get captcha solve in 360 second')

    async def get_recaptcha_token(self):
        task_id = await self.create_task_for_captcha()
        captcha_key = await self.get_captcha_key(task_id)
        return captcha_key

    @helper
    async def full_claim_zk(self):
        claim_addresses = "0x66Fd4FC8FA52c9bec2AbA368047A0b27e24ecfe4"

        amount_in_wei, merkle_index, merkle_proof, airdrop_id, contract_address = await self.get_zk_drop_info()

        self.logger_msg(*self.client.acc_info, msg=f'Claim {amount_in_wei / 10 ** 18:.2f} ZK')

        claim_contract = self.client.get_contract(claim_addresses, ZK_ABI)

        transaction = await claim_contract.functions.claim(
            merkle_index,
            amount_in_wei,
            merkle_proof
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)

    async def full_claim_zro(self, claim_chain_id):
        url = f"https://www.layerzero.foundation/api/proof/{self.client.address}"

        claim_addresses = {
            1: "0xB09F16F625B363875e39ADa56C03682088471523",
            2: "0xf19ccb20726Eab44754A59eFC4Ad331e3bF4F248",
            3: "0x3Ef4abDb646976c096DF532377EFdfE0E6391ac3",
            4: "0x9c26831a80Ef7Fb60cA940EB9AA22023476B3468",
        }[claim_chain_id]

        response = await self.make_request(url=url, zro_claim=True)

        if response:
            amount_to_claim = int(response['amount'])
            merkle_proof = response['proof'].split('|')
            ext_data = '0x'

            self.logger_msg(
                *self.client.acc_info, msg=f'Claim {amount_to_claim / 10 ** 18:.2f} ZRO'
            )

            claim_contract = self.client.get_contract(claim_addresses, CLAIM_ABI)
            quoter_addresses = self.client.get_contract('0xd6b6a6701303B5Ea36fa0eDf7389b562d8F894DB', CLAIM_ABI)

            claim_result = await quoter_addresses.functions.zroClaimed(
                self.client.address
            ).call()

            if claim_result > 0:
                self.logger_msg(*self.client.acc_info, msg=f'Already claimed ZRO', type_msg='warning')
                return True

            if claim_chain_id != 1:
                from functions import OptimismRPC, BaseRPC, BSC_RPC

                client_rpc, rpc_id, eid, withdraw_network = {
                    2: (BaseRPC, 3, 30184, 6),
                    3: (OptimismRPC, 7, 30111, 3),
                    4: (BSC_RPC, 15, 30102, 8),
                }[claim_chain_id]

                donate_amount = (await quoter_addresses.functions.requiredDonation(amount_to_claim).call())[-1]

                new_client: Client = await self.client.new_client(rpc_id)

                claim_bridge_fee = int((await quoter_addresses.functions.quoteClaimCallback(
                    eid,
                    amount_to_claim,
                ).call())[0] * 1.2)

                ext_data = '0x000301002101' + encode(['uint256'], [claim_bridge_fee]).hex()

                claim_contract = new_client.get_contract(claim_addresses, CLAIM_ABI)

                scr_chain_fee_claimer = await claim_contract.functions.claimContract().call()

                scr_chain_fee_contract = new_client.get_contract(scr_chain_fee_claimer, CLAIM_ABI)

                scr_chain_claim_fee = int((await scr_chain_fee_contract.functions.quoteClaim(
                    self.client.address,
                    amount_to_claim,
                    ext_data
                ).call())[0] * 1.2)

                value = donate_amount + claim_bridge_fee + scr_chain_claim_fee

            else:
                new_client = self.client
                withdraw_network = 2
                donate_amount = (await quoter_addresses.functions.requiredDonation(amount_to_claim).call())[-1]
                value = donate_amount

            balance_in_wei, _, _ = await new_client.get_token_balance()

            if balance_in_wei < (value * 1.2):
                self.logger_msg(*self.client.acc_info, msg=f'Not enough {new_client.token} for claim, start withdraw')

                from functions import okx_withdraw_util

                await okx_withdraw_util(
                    new_client, withdraw_data=(withdraw_network, (value / 10 ** 18, (value / 10 ** 18) * 1.1))
                )

            transaction = await claim_contract.functions.donateAndClaim(
                2,
                donate_amount,
                amount_to_claim,
                merkle_proof,
                new_client.address,
                ext_data
            ).build_transaction(await new_client.prepare_transaction(value=value))

            tx_hash = await new_client.send_transaction(transaction, need_hash=True)

            await self.client.wait_for_l0_received(tx_hash=tx_hash)

            await new_client.session.close()
            await self.client.session.close()

        else:
            self.logger_msg(*self.client.acc_info, msg=f'You are not eligible to claim ZRO', type_msg='warning')
            await self.client.session.close()

        return True

    @helper
    async def transfer_zk(self):

        zk_contract = self.client.get_contract('0x5A7d6b2F92C77FAD6CCaBd7EE0624E64907Eaf3E', ERC20_ABI)

        dep_address = get_wallet_for_deposit(self)

        _, balance, _ = await self.client.get_token_balance('ZK', omnicheck=True)
        balance_in_wei = self.client.to_wei(balance)

        self.logger_msg(*self.client.acc_info, msg=f'Transfer {balance:.2f} ZK to {dep_address[:10]}...')

        transfer_tx = await zk_contract.functions.transfer(
            self.client.w3.to_checksum_address(dep_address),
            balance_in_wei
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transfer_tx)

    async def transfer_zro(self):

        zro_contract = self.client.get_contract('0x6985884C4392D348587B19cb9eAAf157F13271cd', ERC20_ABI)

        dep_address = get_wallet_for_deposit(self)

        balance_in_wei, balance, _ = await self.client.get_token_balance('ZRO', omnicheck=True)
        result = True

        if balance > 0:

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Transfer {balance:.2f} ZRO from {self.client.network.name} to {dep_address[:10]}...'
            )

            transfer_tx = await zro_contract.functions.transfer(
                self.client.w3.to_checksum_address(dep_address),
                balance_in_wei
            ).build_transaction(await self.client.prepare_transaction())

            result = await self.client.send_transaction(transfer_tx)
        else:
            self.logger_msg(*self.client.acc_info, msg=f'Zero ZRO amount!', type_msg='warning')

        return result

    @helper
    async def swap_zk(self):
        from functions import swap_syncswap

        _, balance, _ = await self.client.get_token_balance('ZK', omnicheck=True)
        balance_in_wei = self.client.to_wei(balance)

        swap_data = 'ZK', 'USDC', balance, balance_in_wei

        return await swap_syncswap(self.client, swap_data=swap_data)

    @helper
    async def smart_claim_zro(self):
        from functions import claim_zro

        search_chain = copy.deepcopy(ZRO_DST_CHAIN)

        converted_chains = {
            1: 1,
            2: 7,
            3: 31,
            4: 6
        }

        new_chains = []
        for chain in search_chain:
            new_chains.append(converted_chains[chain])

        client, chain_index, balance, _, balance_data = await self.balance_searcher(
            chains=new_chains, native_check=True
        )

        claim_chain_id = {
            'Arbitrum': 1,
            'Base': 2,
            'Optimism': 3,
            'BNB Chain': 4,
        }[client.network.name]

        result = await claim_zro(
            client.account_name, client.private_key, client.network, client.proxy_init, claim_chain_id=claim_chain_id
        )

        await client.session.close()

        return result

    @helper
    async def smart_transfer_zro(self):
        from functions import transfer_zro

        search_chain = copy.deepcopy(ZRO_DST_CHAIN)

        converted_chains = {
            1: 1,
            2: 7,
            3: 31,
            4: 6
        }

        new_chains = []
        tokens = []
        for chain in search_chain:
            new_chains.append(converted_chains[chain])
            tokens.append('ZRO')

        result = False
        try:
            client, chain_index, balance, _, balance_data = await self.balance_searcher(
                chains=new_chains, tokens=tokens, raise_handle=True
            )

            result = await transfer_zro(client.account_name, client.private_key, client.network, client.proxy_init)

            await client.session.close()
        except SoftwareExceptionHandled:
            self.logger_msg(
                *self.client.acc_info, msg=f'Zero ZRO amount in all networks!'
            )

        return result

    async def claim_and_transfer_imx(self):
        claim_contract = '0x3f04d7a7297d5535595eE0a30071008B54E62A03'

        self.logger_msg(
            *self.client.acc_info, msg=f'Claim 3 daily gems on IMX.Community'
        )

        claim_tx = await self.client.prepare_transaction() | {
            'to': claim_contract,
            'data': '0xae56842b'
        }

        claim_result = await self.client.send_transaction(claim_tx)
        dep_address = get_wallet_for_deposit(self)

        imx_balance_in_wei, imx_balance, _ = await self.client.get_token_balance('IMX')
        imx_balance -= 0.001
        imx_balance_in_wei = self.client.to_wei(imx_balance)

        self.logger_msg(
            *self.client.acc_info, msg=f'Send {imx_balance} IMX to {dep_address}'
        )

        send_tx = await self.client.prepare_transaction(value=imx_balance_in_wei) | {
            'to': dep_address
        }

        dep_result = await self.client.send_transaction(send_tx)

        return all([claim_result, dep_result])

    @helper
    async def smart_cex_withdraw(self, dapp_id: int, custom_withdraw_data: list = None):
        while True:
            try:
                from functions import (
                    okx_withdraw_util, get_network_by_chain_id
                )

                func, withdraw_data = {
                    1: (okx_withdraw_util, OKX_WITHDRAW_DATA),
                }[dapp_id]

                if custom_withdraw_data:
                    withdraw_data = custom_withdraw_data

                withdraw_data_copy = copy.deepcopy(withdraw_data)

                random.shuffle(withdraw_data_copy)
                result_list = []

                for index, data in enumerate(withdraw_data_copy, 1):
                    current_data = data
                    if isinstance(data[0], list):
                        current_data = random.choice(data)
                        if not current_data:
                            continue

                    network, amount = current_data

                    current_client = self.client
                    try:
                        if isinstance(amount[0], str):
                            amount = f"{self.client.custom_round(random.uniform(float(amount[0]), float(amount[1])), 6) / 100}"

                        result_list.append(await func(current_client, withdraw_data=(network, amount)))

                        if index != len(withdraw_data_copy):
                            await sleep(self)
                    finally:
                        if current_client:
                            await current_client.session.close()

                return all(result_list)
            except CriticalException as error:
                raise error
            except Exception as error:
                self.logger_msg(self.client.account_name, None, msg=f'{error}', type_msg='error')
                msg = f"Software cannot continue, awaiting operator's action. Will try again in 1 min..."
                self.logger_msg(self.client.account_name, None, msg=msg, type_msg='warning')
                await asyncio.sleep(60)

    @helper
    @gas_checker
    async def smart_cex_deposit(self, dapp_id: int):
        from functions import cex_deposit_util

        class_id, deposit_data, cex_config = {
            1: (1, OKX_DEPOSIT_DATA, OKX_NETWORKS_NAME),
        }[dapp_id]

        deposit_data_copy = copy.deepcopy(deposit_data)

        client = None
        result_list = []
        for data in deposit_data_copy:
            while True:
                try:
                    current_data = data
                    if isinstance(data[0], list):
                        current_data = random.choice(data)
                        if not current_data:
                            continue

                    networks, amount, limit_amount, wanted_to_hold_amount = current_data
                    if (not isinstance(networks, (int, tuple)) or not isinstance(amount, tuple)
                            or not isinstance(limit_amount, int) or not isinstance(wanted_to_hold_amount, tuple)):
                        raise CriticalException(
                            'Software only support [1, (1, 1), 0, (1, 1)] deposit format. See CEX CONTROL'
                        )

                    if isinstance(networks, tuple):
                        dapp_tokens = [f"{cex_config[network].split('-')[0]}{'.e' if network in [29, 30] else ''}"
                                       for network in networks]
                        dapp_chains = [CEX_WRAPPED_ID[chain] for chain in networks]
                    else:
                        dapp_tokens = [f"{cex_config[networks].split('-')[0]}{'.e' if networks in [29, 30] else ''}"]
                        dapp_chains = [CEX_WRAPPED_ID[networks]]

                    try:
                        client, chain_index, balance, _, balance_data = await self.balance_searcher(
                            chains=dapp_chains, tokens=dapp_tokens, omni_check=False
                        )
                    except Exception as error:
                        if 'Insufficient balances in all networks!' in str(error):
                            break
                        else:
                            raise error

                    balance_in_usd, token_price = balance_data

                    if balance_in_usd == 0:
                        self.logger_msg(*self.client.acc_info, msg=f'Can`t deposit ZERO amount', type_msg='warning')
                        break

                    dep_token = dapp_tokens[chain_index]
                    omnicheck = True if dep_token in ['USDV', 'STG', 'MAV', 'CORE'] else False

                    dep_network = networks if isinstance(networks, int) else networks[chain_index]
                    min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)

                    if balance_in_usd >= limit_amount:

                        dep_amount = await client.get_smart_amount(amount, token_name=dep_token, omnicheck=omnicheck)
                        deposit_fee = int(await client.simulate_transfer(token_name=dep_token, omnicheck=omnicheck) * 2)
                        min_hold_balance = random.uniform(min_wanted_amount, max_wanted_amount) / token_price

                        if dep_token == client.token and balance < dep_amount + deposit_fee:
                            dep_amount = dep_amount - deposit_fee

                        if balance - dep_amount < 0:
                            raise SoftwareException('Account balance - deposit fee < 0')

                        if balance - dep_amount < min_hold_balance:
                            need_to_freeze_amount = min_hold_balance - (balance - dep_amount)
                            dep_amount = dep_amount - need_to_freeze_amount

                        if dep_amount < 0:
                            raise CriticalException(
                                f'Set CEX_DEPOSIT_LIMITER[2 value] lower than {wanted_to_hold_amount}. '
                                f'Current amount = {dep_amount:.4f} {dep_token}')

                        dep_amount_in_usd = dep_amount * token_price * 0.99

                        if balance_in_usd >= dep_amount_in_usd:

                            deposit_data = dep_network, self.client.custom_round(dep_amount, 6)

                            if len(deposit_data_copy) == 1:
                                return await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                            else:
                                result_list.append(
                                    await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                                )
                                break

                        info = f"{balance_in_usd:.2f}$ < {dep_amount_in_usd:.2f}$"
                        raise CriticalException(f'Account {dep_token} balance < wanted deposit amount: {info}')

                    info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
                    self.logger_msg(
                        *self.client.acc_info, msg=f'Account {dep_token} balance < wanted limit amount: {info}',
                        type_msg='warning'
                    )
                    break

                except CriticalException as error:
                    raise error
                except Exception as error:
                    raise error
                finally:
                    if client:
                        await client.session.close()

        return all(result_list)

    @helper
    @gas_checker
    async def smart_bridge(self, dapp_id: int = None):
        client = None
        fee_client = None
        while True:
            try:
                from functions import bridge_utils

                dapp_chains, dapp_tokens, limiter = {
                    1: (ACROSS_CHAIN_ID_FROM, ACROSS_TOKEN_NAME, ACROSS_AMOUNT_LIMITER),
                    2: (BUNGEE_CHAIN_ID_FROM, BUNGEE_TOKEN_NAME, BUNGEE_AMOUNT_LIMITER),
                    3: (LAYERSWAP_CHAIN_ID_FROM, LAYERSWAP_TOKEN_NAME, LAYERSWAP_AMOUNT_LIMITER),
                    4: (NITRO_CHAIN_ID_FROM, NITRO_TOKEN_NAME, NITRO_AMOUNT_LIMITER),
                    5: (ORBITER_CHAIN_ID_FROM, ORBITER_TOKEN_NAME, ORBITER_AMOUNT_LIMITER),
                    6: (OWLTO_CHAIN_ID_FROM, OWLTO_TOKEN_NAME, OWLTO_AMOUNT_LIMITER),
                    7: (RELAY_CHAIN_ID_FROM, RELAY_TOKEN_NAME, RELAY_AMOUNT_LIMITER),
                    8: (RHINO_CHAIN_ID_FROM, RHINO_TOKEN_NAME, RHINO_AMOUNT_LIMITER),
                    9: (NATIVE_CHAIN_ID_FROM, NATIVE_TOKEN_NAME, NATIVE_AMOUNT_LIMITER),
                }[dapp_id]

                if len(dapp_tokens) == 2:
                    from_token_name, to_token_name = dapp_tokens
                else:
                    from_token_name, to_token_name = dapp_tokens, dapp_tokens

                dapp_tokens = [from_token_name for _ in dapp_chains]

                client, chain_index, balance, _, balance_data = await self.balance_searcher(
                    chains=dapp_chains, tokens=dapp_tokens, omni_check=False
                )

                fee_client = await client.new_client(dapp_chains[chain_index])
                chain_from_id, token_name = dapp_chains[chain_index], from_token_name

                switch_id = BRIDGE_SWITCH_CONTROL.get(dapp_id, dapp_id)

                source_chain_name, destination_chain, amount, dst_chain_id = await client.get_bridge_data(
                    chain_from_id=chain_from_id, dapp_id=switch_id, settings_id=dapp_id
                )

                from_chain_name = client.network.name
                to_chain_name = CHAIN_NAME[dst_chain_id]
                from_token_addr = TOKENS_PER_CHAIN[from_chain_name][from_token_name]

                if to_token_name == 'USDC':
                    to_token_addr = TOKENS_PER_CHAIN[to_chain_name].get('USDC.e')
                    if not to_token_addr:
                        to_token_addr = TOKENS_PER_CHAIN[to_chain_name]['USDC']
                else:
                    to_token_addr = TOKENS_PER_CHAIN[to_chain_name][to_token_name]

                balance_in_usd, token_price = balance_data
                limit_amount, wanted_to_hold_amount = limiter
                min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)
                fee_bridge_data = (source_chain_name, destination_chain, amount, dst_chain_id,
                                   from_token_name, to_token_name, from_token_addr, to_token_addr)

                if balance_in_usd >= limit_amount:
                    bridge_fee = await bridge_utils(
                        fee_client, switch_id, chain_from_id, fee_bridge_data, need_fee=True)
                    min_hold_balance = random.uniform(min_wanted_amount, max_wanted_amount) / token_price
                    if balance - bridge_fee - min_hold_balance > 0:
                        if balance < amount + bridge_fee and from_token_name == client.token:
                            bridge_amount = self.client.custom_round(amount - bridge_fee, 6)
                        else:
                            bridge_amount = amount
                        if balance - bridge_amount < min_hold_balance:
                            need_to_freeze_amount = min_hold_balance - (balance - bridge_amount)
                            bridge_amount = self.client.custom_round(bridge_amount - need_to_freeze_amount, 6)

                        if bridge_amount < 0:
                            raise CriticalException(
                                f'Set BRIDGE_AMOUNT_LIMITER[2 value] lower than {wanted_to_hold_amount}. '
                                f'Current amount = {bridge_amount} {from_token_name}')

                        bridge_amount_in_usd = bridge_amount * token_price

                        bridge_data = (source_chain_name, destination_chain, bridge_amount, dst_chain_id,
                                       from_token_name, to_token_name, from_token_addr, to_token_addr)

                        if balance_in_usd >= bridge_amount_in_usd:
                            return await bridge_utils(client, switch_id, chain_from_id, bridge_data)

                        info = f"{balance_in_usd:.2f}$ < {bridge_amount_in_usd:.2f}$"
                        raise CriticalException(f'Account {token_name} balance < wanted bridge amount: {info}')

                    full_need_amount = self.client.custom_round(bridge_fee + min_hold_balance, 6)
                    info = f"{balance:.2f} {token_name} < {full_need_amount:.2f} {token_name}"
                    raise CriticalException(f'Account {token_name} balance < bridge fee + hold amount: {info}')

                info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
                raise CriticalException(f'Account {token_name} balance < wanted limit amount: {info}')

            except CriticalException as error:
                raise error
            except Exception as error:
                raise error
            finally:
                if client:
                    await client.session.close()
                if fee_client:
                    await fee_client.session.close()

