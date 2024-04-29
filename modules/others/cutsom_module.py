import asyncio

from config import AETHIR_ABI, CYBERV_ABI
from modules import Logger, Aggregator
from settings import MEMCOIN_AMOUNT, NODE_ID, CYBERV_NFT_COUNT
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

    @helper
    async def buy_node(self):
        nodes_data = {
            "0xc9110F53C042a61d1b0f95342e61d62714F8A2E6": 0.0813,
            "0x11B2669a07A0D17555a7Ab54C0C37f5c8655A739": 0.0915,
            "0x58078e429a99478304a25B2Ab03ABE79199bE618": 0.103,
            "0x2E89CAE8F6532687b015F4BA320F57c77920B451": 0.1158,
            "0x396Ea0670e3112BC344791Ee7931a5A55E0bDBd1": 0.1303,
            "0xB08772AA562ED5d06B34fb211c51EC92debF7b26": 0.1466,
            "0x772eDA6C5aACC61771F9b5f9423D381D311a7018": 0.1649,
            "0x4842547944832Fe833af677BFDB157dEf391e685": 0.1855,
            "0x3F0d099120Bf804606835DEFa6dA1A5E784328D6": 0.2087,
            "0xe0D06d430b0a44e6444f5f0736dC113afe5b636A": 0.2348,
            "0xE501ADF8425E1Dd5099fA607dCc2B4c91C47B986": 0.2524,
            "0x2FB5D834D274b9442DA957E98319C35938219a9E": 0.2713,
            "0xa1109b5550bec4a1118bD232BacCd07dc914CF04": 0.2917,
            "0x2e64E45faBF1f432d2B59ABd474Da738042B9393": 0.3136,
            "0x11fBF3713B44AE6D8DBCA1920A40c82AdC685eb4": 0.3371,
            "0xC7acfcAD2e3008713ee6E3FAF182Aa3a35ae233b": 0.3371,
            "0x12f8cDEfd7146a089609Be76dCeb8cCeda45eC84": 0.3624,
            "0x17889bAfcd74E49c219b7449BE60290CF44a314A": 0.3624,
            "0x7497B778f8ACfe135D7710B223F72B82ECca8F20": 0.3895,
            "0x069CEA5EfA367F8827Bb71aE2eDF4C5D7907BC79": 0.3895,
            "0x47F97110768e06984855410Fb51698F2CaB04569": 0.4188,
            "0xfE1AEb6f8ceFaF3cc6b331975B25C30a86b111ea": 0.4502,
            "0xb23f5E5A712D3EB8F28433A753666eC6A59238b9": 0.4502,
            "0xeF51418BcF608470cB02C3701E22d8885DBbFF5A": 0.4839,
            "0x5a9D1119d3dDf17112f008AE4f200A0d4d1E12F1": 0.4839,
            "0x2C8e588EC69B15731970470c8C0Eb864D9Ffb414": 0.5202,
            "0x857558578A8Dd302D56a1111835e7bAa245EA38e": 0.5592,
            "0x2BDd83B8B189013173C59a15cd9a2fb4Fba9db40": 0.6012,
            "0x569C7B5f46f33d7EABcf6347Db6e3338f924AF34": 0.6463,
            "0x37AA2dD6aA1c611958879a072C78Db8C8150eb84": 0.6947,
            "0x648afe9Dd30515329865ddF5277ae64EaE0576E4": 0.7468,
            "0xa2751F76b031189007a573cEa8FdA0d9ddbEf894": 0.8029,
            "0xb09fFbf62450608Ba304befDA6C8FA1eCF77F3f3": 0.8631,
            "0xC94e199600f09CDcBEEe0AeeB0bBf55E31585149": 0.9278,
            "0x7ec4D460a3E97fed71081ECAcd5591d1d3A1884C": 0.9974,
            "0x96Da89f233a53b97976F73D7C519C44fefD08CD5": 1.0722,
            "0x8CC671cEabb069a2F232CB6ECd4fFC7cd23E9c76": 1.1526,
            "0xc501E4aa8fA91a8cdc696F513B05883f5347C69d": 1.2391,
            "0xc1e161E12C537661E047d0BFA187EbfF5988A873": 1.332,
            "0x5Edf657342e5fD199Ff64Ff10C232F5D5f931d83": 1.4319,
            "0x08Acfe563babE2Afb28E434723bB20121FD65E0c": 1.5393,
            "0x28aA5d6BE4A4861Bf8a49ae46ab8Ce31A89A03De": 1.5393,
            "0xF5f80976ca38881ECe87b9c83Eb9273bd87AA688": 1.6547,
            "0xced90a97B34a04dc49b0b4d58336c8c74F1971a3": 1.7788,
            "0x9F2D06b84c2Ac36989286506D4431b48c970Dc92": 1.9122,
            "0x518eCD09723EF4a71952aCD9281234294dE1488a": 1.9122,
            "0x75d4E9988ed1a06FBB4b1A4D13217Fb87C82cB08": 2.0556,
        }

        # {
        #     "inputs": [
        #
        #     ],
        #     "name": "saleAmount",
        #     "outputs": [
        #         {
        #             "internalType": "uint256",
        #             "name": "",
        #             "type": "uint256"
        #         }
        #     ],
        #     "stateMutability": "view",
        #     "type": "function"
        # },
        # {
        #     "inputs": [
        #
        #     ],
        #     "name": "salePrice",
        #     "outputs": [
        #         {
        #             "internalType": "uint256",
        #             "name": "",
        #             "type": "uint256"
        #         }
        #     ],
        #     "stateMutability": "view",
        #     "type": "function"
        # },
        # {
        #     "inputs": [
        #
        #     ],
        #     "name": "startTime",
        #     "outputs": [
        #         {
        #             "internalType": "uint256",
        #             "name": "",
        #             "type": "uint256"
        #         }
        #     ],
        #     "stateMutability": "view",
        #     "type": "function"
        # },
        import datetime

        # Предположим, что у вас есть timestamp
        # Преобразование timestamp в объект datetime

        for contract_address, price in nodes_data.items():

            node_contract = self.client.get_contract(contract_address, AETHIR_ABI)

            total_price = int(price * 2)
            total_count = int(2)

            #await self.client.check_for_approved()

            start_time = await node_contract.functions.startTime().call()
            date_time = datetime.datetime.fromtimestamp(start_time)
            bytes_data = '0x'
            # Преобразование объекта datetime в строку с помощью метода strftime()
            try:
                transaction = await node_contract.functions.whitelistedPurchase(
                    total_price,
                    [],
                    total_count,
                ).build_transaction(await self.client.prepare_transaction(value=total_price))
            except Exception as error:
                try:
                    self.logger_msg(*self.client.acc_info, msg=f"Method#1. {error}", type_msg='error')
                    transaction = await node_contract.functions.whitelistedPurchase(
                        total_price,
                        []
                    ).build_transaction(await self.client.prepare_transaction(value=total_price))
                except Exception as error:
                    try:
                        self.logger_msg(*self.client.acc_info, msg=f"Method#2. {error}", type_msg='error')
                        transaction = await node_contract.functions.whitelistedPurchaseWithCode(
                            total_price,
                            [],
                            total_count,
                            'defigen',
                        ).build_transaction(await self.client.prepare_transaction(value=total_price))
                    except Exception as error:
                        self.logger_msg(*self.client.acc_info, msg=f"Method#3. {error}", type_msg='error')
                        raise error

            print(transaction)
            break
            return await self.client.send_transaction(transaction)

        # for contract_address, price in nodes_data.items():
        #
        #     node_contract = self.client.get_contract(contract_address, AETHIR_ABI)
        #
        #     #await self.client.check_for_approved()
        #
        #     start_time = await node_contract.functions.totalPaymentReceived().call()
        #     print(start_time)
        #     # date_time = datetime.datetime.fromtimestamp(start_time)
        #     #
        #     # # Преобразование объекта datetime в строку с помощью метода strftime()
        #     # formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
        #     # if formatted_date_time.split()[0][-2:] == "30":
        #     #     print(f"{contract_address}: {price}")
        #     # continue
        #     # transaction = await node_contract.functions.a(
        #     #     sale_price,
        #     #     [],
        #     #     sale_price,
        #     #     'defigen'
        #     # ).build_transaction(await self.client.prepare_transaction(value=sale_price))
        #     #
        #     # return await self.client.send_transaction(transaction)

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
