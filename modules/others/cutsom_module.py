import copy

from config import AETHIR_ABI, CYBERV_ABI, TOKENS_PER_CHAIN
from modules import Logger, Aggregator
from settings import MEMCOIN_AMOUNT, CYBERV_NFT_COUNT, NODE_COUNT, NODE_TIER_MAX, NODE_TIER_BUY
from utils.tools import helper


class Custom(Logger, Aggregator):
    def __init__(self, client):
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
            self.logger_msg(*self.client.acc_info, msg=f"Trying to buy Sophon Node Tier #{index}")
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Approve for buying Sophon Node Tier #{index}")

        total_price = int(price * NODE_COUNT * 10 ** 18)
        total_count = int(NODE_COUNT * 10 ** 18)
        ref_flag = False

        weth_address = TOKENS_PER_CHAIN['zkSync']['WETH']

        if approve_mode:
            return await self.client.check_for_approved(weth_address, node_contract.address, without_bal_check=True)

        try:
            transaction = await node_contract.functions.whitelistedPurchaseWithCode(
                total_price,
                [],
                total_price,
                'cryptoearn',
            ).build_transaction(tx_params)
            ref_flag = True
        except Exception as error:
            try:
                self.logger_msg(*self.client.acc_info, msg=f"Method#1. {error}", type_msg='error')
                transaction = await node_contract.functions.whitelistedPurchaseWithCode(
                    total_price,
                    [],
                    total_count,
                    'cryptoearn',
                ).build_transaction(tx_params)
                ref_flag = True
            except Exception as error:
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
            1: ("0xc9110F53C042a61d1b0f95342e61d62714F8A2E6", 0.0813),
            2: ("0x11B2669a07A0D17555a7Ab54C0C37f5c8655A739", 0.0915),
            3: ("0x58078e429a99478304a25B2Ab03ABE79199bE618", 0.103),
            4: ("0x2E89CAE8F6532687b015F4BA320F57c77920B451", 0.1158),
            5: ("0x396Ea0670e3112BC344791Ee7931a5A55E0bDBd1", 0.1303),
            6: ("0xB08772AA562ED5d06B34fb211c51EC92debF7b26", 0.1466),
            7: ("0x772eDA6C5aACC61771F9b5f9423D381D311a7018", 0.1649),
            8: ("0x4842547944832Fe833af677BFDB157dEf391e685", 0.1855),
            9: ("0x3F0d099120Bf804606835DEFa6dA1A5E784328D6", 0.2087)
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
                            *self.client.acc_info, msg=f"Can`t buy Sophon Node Tier #{index}", type_msg='warning'
                        )
                    else:
                        break

                if result:
                    break

        return True

    @helper
    async def buy_cyberv(self, public_mode:bool = False):
        mint_addresses = '0x67CE4afa08eBf2D6d1f31737cc5D54Ff116205e9'
        sale_price = int(127000000000000000 * CYBERV_NFT_COUNT)

        url = f'https://api-nft.gmnetwork.ai/nft/whitelist/?collection_name=CyberV&address={self.client.address}'

        response = await self.make_request(url=url)

        if response['success']:

            if response['result']['signature'] != '' or public_mode:
                signature = self.client.w3.to_bytes(hexstr=response['result']['signature'])

                self.logger_msg(
                    *self.client.acc_info, msg=f'Mint CyberV NFT, signature: {self.client.w3.to_hex(signature)[:10]}...'
                )

                signature = self.client.w3.to_bytes(hexstr=response['result']['signature'])
                mint_contract = self.client.get_contract(mint_addresses, CYBERV_ABI)

                transaction = await mint_contract.functions.mint(
                    CYBERV_NFT_COUNT,
                    signature if not public_mode else '0x'
                ).build_transaction(await self.client.prepare_transaction(value=sale_price))

                return await self.client.send_transaction(transaction)

            raise RuntimeError('Signature is not exist')
        raise RuntimeError('Bad request to CyberV API')
