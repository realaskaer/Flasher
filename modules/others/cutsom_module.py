from config import AETHIR_ABI, CYBERV_ABI
from modules import Logger, Aggregator
from settings import MEMCOIN_AMOUNT, NODE_ID
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
        node_addresses = {
            1: "0xc2BF4eBEbBd692176d08faC51ba7ec3410Af18EC",
            2: "0xD19EBA0953e995806e76f5505cD6D8A820909C94",
            3: "0xF85468AaDD71d2dbC969b4A8Cc2147c1DdD4866d",
            4: "0x754C9D60d5E877bd24c47FaE05eb670875D47442",
            5: "0x2EbdcEDE80039bb745C3ee2a18C740346dd6560e",
            6: "0x213404cAB4e3FF587614daBF7bfB23FEb0354227",
            7: "0xB503f244C02B9472FE0e49d558Df3A3274E1C38c",
            8: "0x13e8c714F43C806933E0600880600002186BB924",
            9: "0x2f2735573c137a57F8cE472D55039beb564Fa489",
            10: "0x20F0E6560d3B2A3DCd3f6dCbF1182e9bB39C49D5",
            11: "0x1464F7317D6ed9A593aEc6817603032e00a66Ec9",
            12: "0x5734c72a2A7EBbC81b0f68D2B70337E641E101e4",
            13: "0x6e27373dA1ECB48361135c1606F48Ab9D0BA6d0e",
            14: "0x8464e90Ecb3E004548A3aC1f7923AF2ddd0bb74C",
            15: "0xCC72630C2193C1b3c30ceAD19Ec52F503a09ef61",
            16: "0x7127B5397f5E565BFCA3902Bc90A1B98bc774F7F",
            17: "0xC8F323ca581868b85f663F8151fBbF3eaa28D8F8",
            18: "0xABb16F825190aB86c8f1FE8d1B92fb533972aead",
            19: "0xd3d5cbd93C8bEf660c606F34FeA0dB8a61f23304",
            20: "0x07d995a0Da7aeB996468B42D2ed1746b8c534F19",
            21: "0xA52A44207083bDB3E120f17E38a34d66DD0c621A",
            22: "0xAF255dCB88a09B6DE7239A7Af02e8a5351eF47C2",
            23: "0x45526eB2D1dD87d4ED06F867132B0B34e4570619",
            24: "0x2967C63d7BabEf1111DD2B69C7E9c7eEee4B7603",
            25: "0x3Aac8b9e37DF1369b6d57A22360115FF40F657bd",
            26: "0x5b9a4f7e47Be8187e3a7cA34ADeE117980a08d6C",
            27: "0x7c3C3994A41FCf91460603bc8d347F94C1A69e08",
            28: "0x229A2aAA2BA844912dDa0EAd878a505cF91B99b8",
            29: "0xCC149f4154e42c5f9C5aA91d4b05613ebe22E962",
            30: "0x14b86CeC8e4C9924DF50F61Ba69432acFe631f83",
            31: "0x6Dd87393fe2A46B961DB5B04A33b749B6E74b77D",
            32: "0x5caB24d6be7c38451dB88e2Ee3A1F8DC05c4f369",
            33: "0x05eE164193b73A8f120A05854534e9337E7a8FfC",
            34: "0xfFF8b61AAE444BDC0573F6d5Be49A3A3E3985925",
            35: "0xB257Ed0Aa1ceAC4Cb2e206Fa417a5B1d1AE8bBB7",
            36: "0x176596142e9e4C1dAeEa21Bfb3648F6Fd40Ec6d4",
            37: "0x563A67fe35CA51d52C26A5859ac3221502D80a70",
            38: "0x8dCa0d5e28b412C602bdd8F4CDC24090f82A00e1",
            39: "0x33b7f001630260AfB071dbB77f98041452703bBd",
            40: "0xbcbBfBB1E1Bf1B905cBc9ba3F0F3ceAe2a5d25eF",
            41: "0xEF5570f2F01D9cA4A588D283998D56537F8269cC",
            42: "0x1E64551759a5D67c017182F0c338e378BD378419",
            43: "0xd05A967b0932248304889fAfFc35982C26C39999",
            44: "0x0832E9b219d81DcE30cBB3fD5bF676546b042166",
            45: "0x21d4ce496934d07e98A5E931C6a2e028d3468508",
            46: "0xad00F8853705205dDaE5763BC5f8324E5598F017",
            47: "0xe9F5c88009Dc81BDe0a0446E6736434d249597cE",
            48: "0x8FEf23dD02C16D5A2250Ace4e64411F0574288A9",
            49: "0x13D34F008974f66500C09fa52AD5a6E62242Fd60",
            50: "0xF5719b95E0e00383C5AA7035556EA3cFb042EC59",
            51: "0xb5104e2a0BA6B93Be531D0Eabba85153894B2966",
            52: "0xa82d10419b1cdA94a41e6389D7e5a8288981a5aa",
            53: "0x1B30B26c50d3926F0b69b8beaAf3B81d077EC9e7",
        }[NODE_ID]

        node_contract = self.client.get_contract(node_addresses, AETHIR_ABI)

        await self.client.check_for_approved()

        sale_price = await node_contract.functions.salePrice().call()

        transaction = await node_contract.functions.a(
            sale_price,
            [],
            sale_price,
            'defigen'
        ).build_transaction(await self.client.prepare_transaction(value=sale_price))

        return await self.client.send_transaction(transaction)

    @helper
    async def buy_cyberv(self):
        mint_addresses = '0x67CE4afa08eBf2D6d1f31737cc5D54Ff116205e9'
        sale_price = 127000000000000000

        mint_contract = self.client.get_contract(mint_addresses, CYBERV_ABI)

        transaction = await mint_contract.functions.mint(
            2,
            ''
        ).build_transaction(await self.client.prepare_transaction(value=sale_price))

        return await self.client.send_transaction(transaction)

