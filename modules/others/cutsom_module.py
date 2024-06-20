import asyncio
import copy
import json

from eth_account.messages import encode_structured_data

from config import AETHIR_ABI, TOKENS_PER_CHAIN, TAIKO_ABI, ERC20_ABI, ZK_ABI, ZRO_ABI
from modules import Logger, Aggregator, Client
from settings import MEMCOIN_AMOUNT, NODE_COUNT, NODE_TIER_MAX, NODE_TIER_BUY, \
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
        url = "https://api.zknation.io/claim"

        claim_addresses = "0x66Fd4FC8FA52c9bec2AbA368047A0b27e24ecfe4"

        amount_in_wei, merkle_index, merkle_proof, airdrop_id, contract_address = await self.get_zk_drop_info()

        self.logger_msg(*self.client.acc_info, msg=f'Claim {amount_in_wei / 10 ** 18:.2f} ZK')

        # timestamp = int(time.time()) + 604800
        #
        # claim_signature = await self.get_claim_zk_signature(amount_in_wei, merkle_index, contract_address, timestamp)
        # delegate_signature = await self.get_delegate_zk_signature(timestamp)
        # recaptcha_token = await self.get_recaptcha_token()
        #
        # headers = {
        #     "accept": "application/json",
        #     "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        #     "content-type": "application/json",
        #     "priority": "u=1, i",
        #     "Recaptcha": recaptcha_token,
        #     "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"123\", \"Microsoft Edge\";v=\"123\"",
        #     "sec-ch-ua-mobile": "?0",
        #     "sec-ch-ua-platform": "\"Windows\"",
        #     "sec-fetch-dest": "empty",
        #     "sec-fetch-mode": "cors",
        #     "sec-fetch-site": "same-site",
        #     "x-api-key": "46001d8f026d4a5bb85b33530120cd38",
        #     "referrer": "https://claim.zknation.io/",
        #     "referrerPolicy": "strict-origin-when-cross-origin",
        #     "method": "POST",
        #     "mode": "cors",
        #     "credentials": "omit"
        # }
        #
        # payload = {
        #     "airdropId": airdrop_id,
        #     "claimant": f"{self.client.address}",
        #     "claimSignature": f"{claim_signature}",
        #     "claimSignatureExpiry": timestamp,
        #     "nonce": "0",
        #     "delegateSignature": f"{delegate_signature}",
        #     "delegateSignatureExpiry": timestamp,
        #     "delegatee": f"{self.client.address}",
        #     "delegateNonce": "0"
        # }
        #
        # response = await self.make_request('POST', url=url, json=payload, headers=headers)

        claim_contract = self.client.get_contract(claim_addresses, ZK_ABI)

        transaction = await claim_contract.functions.claim(
            merkle_index,
            amount_in_wei,
            merkle_proof
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)

    @helper
    async def full_claim_zro(self):
        url = f"https://www.layerzero.foundation/api/proof/{self.client.address}"

        claim_addresses = "0xB09F16F625B363875e39ADa56C03682088471523"

        response = await self.make_request(url=url)

        if response['amount']:
            amount_to_claim = int(response['amount'])
            merkle_proof = response['proof'].split('|')

            self.logger_msg(*self.client.acc_info, msg=f'Claim {amount_to_claim / 10 ** 18:.2f} ZRO')

            claim_contract = self.client.get_contract(claim_addresses, ZRO_ABI)

            donate_amount = int((round(amount_to_claim / 10 ** 18) + 1) * 0.00004 * 10 ** 18)

            transaction = await claim_contract.functions.donateAndClaim(
                2,
                donate_amount,
                amount_to_claim,
                merkle_proof,
                self.client.address,
                '0x'
            ).build_transaction(await self.client.prepare_transaction(value=donate_amount))

            return await self.client.send_transaction(transaction)

        # timestamp = int(time.time()) + 604800
        #
        # claim_signature = await self.get_claim_zk_signature(amount_in_wei, merkle_index, contract_address, timestamp)
        # delegate_signature = await self.get_delegate_zk_signature(timestamp)
        # recaptcha_token = await self.get_recaptcha_token()
        #
        # headers = {
        #     "accept": "application/json",
        #     "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        #     "content-type": "application/json",
        #     "priority": "u=1, i",
        #     "Recaptcha": recaptcha_token,
        #     "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"123\", \"Microsoft Edge\";v=\"123\"",
        #     "sec-ch-ua-mobile": "?0",
        #     "sec-ch-ua-platform": "\"Windows\"",
        #     "sec-fetch-dest": "empty",
        #     "sec-fetch-mode": "cors",
        #     "sec-fetch-site": "same-site",
        #     "x-api-key": "46001d8f026d4a5bb85b33530120cd38",
        #     "referrer": "https://claim.zknation.io/",
        #     "referrerPolicy": "strict-origin-when-cross-origin",
        #     "method": "POST",
        #     "mode": "cors",
        #     "credentials": "omit"
        # }
        #
        # payload = {
        #     "airdropId": airdrop_id,
        #     "claimant": f"{self.client.address}",
        #     "claimSignature": f"{claim_signature}",
        #     "claimSignatureExpiry": timestamp,
        #     "nonce": "0",
        #     "delegateSignature": f"{delegate_signature}",
        #     "delegateSignatureExpiry": timestamp,
        #     "delegatee": f"{self.client.address}",
        #     "delegateNonce": "0"
        # }
        #
        # response = await self.make_request('POST', url=url, json=payload, headers=headers)

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
    async def transfer_zro(self):

        zro_contract = self.client.get_contract('0x6985884C4392D348587B19cb9eAAf157F13271cd', ERC20_ABI)

        dep_address = get_wallet_for_deposit(self)

        _, balance, _ = await self.client.get_token_balance('ZRO', omnicheck=True)
        balance_in_wei = self.client.to_wei(balance)

        self.logger_msg(*self.client.acc_info, msg=f'Transfer {balance:.2f} ZRO to {dep_address[:10]}...')

        transfer_tx = await zro_contract.functions.transfer(
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




