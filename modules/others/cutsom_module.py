import asyncio
import copy
import json
import time

from eth_account.messages import encode_structured_data

from config import AETHIR_ABI, CYBERV_ABI, TOKENS_PER_CHAIN, TAIKO_ABI, ERC20_ABI, ZK_ABI
from modules import Logger, Aggregator, Client
from settings import MEMCOIN_AMOUNT, CYBERV_NFT_COUNT, NODE_COUNT, NODE_TIER_MAX, NODE_TIER_BUY, \
    NODE_TRYING_WITHOUT_REF, TWO_CAPTCHA_API_KEY
from utils.tools import helper, get_wallet_for_deposit


class Custom(Logger, Aggregator):
    def __init__(self, client: Client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.stop_flag = False
        self.signed_tx = None

    async def swap(self):
        pass

    @helper
    async def buy_memecoin_thruster(self):
        from functions import swap_thruster

        amount = MEMCOIN_AMOUNT
        amount_in_wei = self.client.to_wei(amount, 18)
        data = 'ETH', 'MEMCOIN', f"{amount:.2f}", amount_in_wei

        return await swap_thruster(self.client, swapdata=data)

    @helper
    async def sell_memecoin_thruster(self):
        from functions import swap_thruster

        await self.client.initialize_account()

        amount_in_wei, amount, _ = await self.client.get_token_balance('MEMCOIN', check_symbol=False)
        data = 'MEMCOIN', 'ETH', f"{amount:.2f}", amount_in_wei

        return await swap_thruster(self.client, swapdata=data)

    async def buy_node_util(self, contract_address, price, index, approve_mode, tx_params=None):

        node_contract = self.client.get_contract(contract_address, AETHIR_ABI)

        if not isinstance(NODE_COUNT, int):
            raise RuntimeError('NODE_COUNT should ne a digit! (NODE_COUNT = 10)')

        if not approve_mode:
            self.logger_msg(*self.client.acc_info, msg=f"Trying to buy Carv Node Tier #{index}")
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Approve for buying Carv Node Tier #{index}")

        total_price = int(price * NODE_COUNT * 10 ** 18)
        total_count = int(NODE_COUNT * 10 ** 18)
        ref_flag = False

        weth_address = TOKENS_PER_CHAIN['Arbitrum']['WETH']

        if approve_mode:
            result = await self.client.check_for_approved(weth_address, node_contract.address, without_bal_check=True)
            await asyncio.sleep(1)
            return result

        try:
            transaction = await node_contract.functions.whitelistedPurchaseWithCode(
                total_price,
                [],
                total_price,
                'crypto_earn_important',
            ).build_transaction(tx_params)
            ref_flag = True
        except Exception as error:
            try:
                self.logger_msg(*self.client.acc_info, msg=f"Method#1. {error}", type_msg='error')
                transaction = await node_contract.functions.whitelistedPurchaseWithCode(
                    total_price,
                    [],
                    total_count,
                    'crypto_earn_important',
                ).build_transaction(tx_params)
                ref_flag = True
            except Exception as error:
                if NODE_TRYING_WITHOUT_REF:
                    try:
                        self.logger_msg(*self.client.acc_info, msg=f"Method#2. {error}", type_msg='error')
                        transaction = await node_contract.functions.whitelistedPurchase(
                            total_price,
                            [],
                            total_count,
                        ).build_transaction(tx_params)
                    except Exception as error:
                        try:
                            self.logger_msg(*self.client.acc_info, msg=f"Method#3. {error}", type_msg='error')
                            transaction = await node_contract.functions.whitelistedPurchase(
                                total_price,
                                [],
                                total_price,
                            ).build_transaction(tx_params)
                        except Exception as error:
                            self.logger_msg(*self.client.acc_info, msg=f"Method#4. {error}", type_msg='error')
                            return False
                else:
                    self.logger_msg(*self.client.acc_info, msg=f"Method#2. {error}", type_msg='error')
                    return False

        tx = await self.client.send_transaction(transaction)

        if tx:
            if ref_flag:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Tier #{index} was bought with 10% discount", type_msg='success'
                )
            else:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Tier #{index} was bought", type_msg='success'
                )
            return True
        return False

    @helper
    async def buy_node(self, approve_mode: bool = False):
        nodes_data = {
            1: ("0x80adA4D9F18996c19df7d07aCfE78f9460BBC151", 0.1316),
            2: ("0x82720570AC1847FD161b5A01Fe6440c316e5742c", 0.1580),
            3: ("0x3F3C6DE3Bbe1F2fdFb4B43a49e599885B7Fb1a27", 0.1817),
            4: ("0xc674BEB2f5Cd94A748589A9Dadd838b9E09AABD4", 0.2071),
            5: ("0xF8a8A71d90f1AE2F17Aa4eE9319820B5F394f629", 0.2340),
            6: ("0x125711d6f0AAc9DFFEd75AD2B8C51bDaF5FAEd71", 0.2633),
            7: ("0x3371b74beC1dE3E115A4148956F94f55bEA8cD00", 0.2962),
            8: ("0xa1D3632C9Dc73e8EcEBAe99a8Ea00F50F226A8B9", 0.3332),
            9: ("0xD7C3E0C20Ab22f1e9A59e764B1b562E1dD7438B0", 0.3749)
        }

        if NODE_TIER_BUY != 0:
            new_nodes_data = copy.deepcopy(nodes_data[NODE_TIER_BUY])
        else:
            new_nodes_data = copy.deepcopy(nodes_data)

        if approve_mode:
            for index in range(1, 10):
                contract_address, price = nodes_data[index]
                await self.buy_node_util(
                    contract_address=contract_address, price=price, index=index, approve_mode=approve_mode
                )
            return True

        tx_params = await self.client.prepare_transaction()

        if isinstance(new_nodes_data, tuple):
            contract_address, price = new_nodes_data
            while True:
                result = await self.buy_node_util(
                    contract_address=contract_address, price=price, index=NODE_TIER_BUY, approve_mode=False,
                    tx_params=tx_params
                )
                if result:
                    break
        else:
            result = False
            while True:
                for index in range(1, NODE_TIER_MAX + 1):
                    contract_address, price = new_nodes_data[index]
                    result = await self.buy_node_util(
                        contract_address=contract_address, price=price, index=index, approve_mode=False,
                        tx_params=tx_params
                    )

                    if not result:
                        self.logger_msg(
                            *self.client.acc_info, msg=f"Can`t buy Carv Node Tier #{index}", type_msg='warning'
                        )
                    else:
                        break

                if result:
                    break

        return True

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

    @helper
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

        # {
        #     "allocations": [
        #         {
        #             "userId": "0xAC50E5a0a6616EBEC91072aF86F6fd33A8D6a637",
        #             "tokenAmount": "945000000000000000000",
        #             "criteria": [
        #                 {
        #                     "criteriaId": "contract_interactions",
        #                     "description": "Interacted with 10 smart contracts",
        #                     "criteriaType": "zksync"
        #                 },
        #                 {
        #                     "criteriaId": "defi_liquidity_provider",
        #                     "description": "Deposited liquidity into DeFi protocols",
        #                     "criteriaType": "zksync"
        #                 },
        #                 {
        #                     "criteriaId": "heavy_token_trader",
        #                     "description": "Traded 10 different ERC20 tokens",
        #                     "criteriaType": "zksync"
        #                 }
        #             ],
        #             "airdrop": {
        #                 "id": "f66d93c9-2681-4428-9500-e19fe193b973",
        #                 "contractAddress": "0x66Fd4FC8FA52c9bec2AbA368047A0b27e24ecfe4",
        #                 "associationStopsAt": "2024-06-14T13:00:00.000Z",
        #                 "claimStartsAt": "2024-06-17T07:00:00.000Z",
        #                 "finalized": true
        #             },
        #             "associatedAddress": null,
        #             "merkleIndex": "468722",
        #             "merkleProof": [
        #                 "0x43a1f0e0c84448470f285cd3e6ba7a68c2b6d8d9db99e8dd4a4677984162c1e1",
        #                 "0x17c5998b583302ec58a056dcd416c5f5298f7acd4c90b983ccff1953ec552b4a",
        #                 "0xaec13cb70b2afe6cb0b0b767f5dbcacf991103b0ede5d7b5623cbd4a998cf142",
        #                 "0xa2fec5a692564c40a3fd487372f46f233f48652ac3bef7658d19b8334a6accc4",
        #                 "0x9fff98e1ada049b3f490ea27ed4ec3995f1a8e6fd8f05939e0dccf371757e462",
        #                 "0x549e93d921c0f7c9f3092b593fadb322033b17abc5611227dac3b16d64fa18da",
        #                 "0xa1b952c3f3fdcb6a7d75efebac216bb2cf5c6bf98e0a7fe196d66f74dad79b96",
        #                 "0x5c7762f2435cd3bb06fe7d530f2a547ced8c1326dda38b8e57d24984cb0237eb",
        #                 "0x4ea5afcbea0f748ee92a0d87c2089ebc47424fb11b4dcef05b261bd92dfc82ae",
        #                 "0x15dd718f8624ba23c6820f428b62ec135e5c74c7a1d31526cbe475ad176f6200",
        #                 "0xfb8e8a62ac33c88fa8966e092833cbade11a056fea88dcc9ce35ac85e3240ebc",
        #                 "0x779b3207f116bf76bdee16a7cbefba22d9890306572dee7fd0cbe18c713f0c60",
        #                 "0xd659653a36c487cef5a2ca207d32f38387a620b51f1f328a021b88f89aed6a0a",
        #                 "0xa0bbd120ecb966236fe728f18afe3fecb5b51fa2b6f978328d6d3f2b43a69dfa",
        #                 "0x809a284b695378d6529e82239964c26c234448b8e7b175a9bcbba1e3eb081ae7",
        #                 "0x18a83c79bb6ecee8d684e79d1d16f47f4f260d380a90999907b110404c9a502c",
        #                 "0xd057d9bc8ed343edacad6541328d283cf0af83546c35f058a47e43495c3cf8c6",
        #                 "0x640009ff94289cc311064e17d2b4b8132ee8d866e4e8067c4b0fbf14b3226342",
        #                 "0x991068aad433c8990d4d8b9564af8e849a9285e2db7d9d3f20773673b4494d83",
        #                 "0x74e8aa65670c322311dbc3a190daeba1b30b221ec0a2731cda27785942070bd9"
        #             ],
        #             "claimStatus": {
        #                 "status": "queued",
        #                 "estimatedExecutionAt": "2024-06-17T08:05:23.039Z"
        #             }
        #         }
        #     ]
        # }

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
                "owner": {self.client.address},
                "delegatee": {self.client.address},
                "nonce": 0,
                "expiry": timestamp
            }
         }

         text_encoded = encode_structured_data(typed_data)
         signature = self.client.w3.eth.account.sign_message(text_encoded, self.client.private_key).signature

         return self.client.w3.to_hex(signature)

    async def get_claim_zk_signature(self, amount_in_wei, contract_address, timestamp):
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
                "index": "468722",
                "claimant": {self.client.address},
                "amount": amount_in_wei,
                "delegatee": {self.client.address},
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
                return response['solution']['token']

            total_time += 5
            await asyncio.sleep(5)

            if total_time > timeout:
                raise RuntimeError('Can`t get captcha solve in 360 second')

    async def get_recaptcha_token(self):
        task_id = await self.create_task_for_captcha()
        captcha_key = await self.get_captcha_key(task_id)
        return captcha_key

    async def full_claim_zk(self):
        url = "https://api.zknation.io/claim"

        amount_in_wei, merkle_index, merkle_proof, airdrop_id, contract_address = await self.get_zk_drop_info()

        self.logger_msg(*self.client.acc_info, msg=f'Claim {amount_in_wei / 10 ** 18:.2f} ZK')

        timestamp = int(time.time()) + 604800

        claim_signature = await self.get_claim_zk_signature(amount_in_wei, contract_address, timestamp)
        delegate_signature = await self.get_delegate_zk_signature(timestamp)
        recaptcha_token = await self.get_recaptcha_token()

        headers = {
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "content-type": "application/json",
            "priority": "u=1, i",
            "recaptcha": recaptcha_token,
            "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"123\", \"Microsoft Edge\";v=\"123\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-api-key": "46001d8f026d4a5bb85b33530120cd38",
            "referrer": "https://claim.zknation.io/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "method": "POST",
            "mode": "cors",
            "credentials": "omit"
        }

        payload = {
            "airdropId": airdrop_id,
            "claimant": f"{self.client.address}",
            "claimSignature": f"{claim_signature}",
            "claimSignatureExpiry": timestamp,
            "nonce": "0",
            "delegateSignature": f"{delegate_signature}",
            "delegateSignatureExpiry": timestamp,
            "delegatee": f"{self.client.address}",
            "delegateNonce": "0"
        }

        response = await self.make_request('POST', url=url, json=payload, headers=headers)

        if response['success']:
            self.logger_msg(
                *self.client.acc_info, msg=f'Successfully claimed ZK on zkNation', type_msg='success'
            )
            return True

        self.logger_msg(
            *self.client.acc_info, msg=f'Can`t claim ZK on zkNation: {response}', type_msg='warning'
        )
        return False

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

    @helper
    async def swap_zk(self):
        from functions import swap_syncswap

        _, balance, _ = await self.client.get_token_balance('ZK', omnicheck=True)
        balance_in_wei = self.client.to_wei(balance)

        swap_data = 'ZK', 'USDC', balance, balance_in_wei

        return await swap_syncswap(self.client, swap_data=swap_data)

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




