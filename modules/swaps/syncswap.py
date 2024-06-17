from time import time
from eth_abi import abi
from modules import DEX, Logger, Client
from utils.tools import helper
from eth_account.messages import encode_structured_data
from config import (
    SYNCSWAP_CONTRACTS,
    SYNCSWAP_ABI,
    ZERO_ADDRESS,
    TOKENS_PER_CHAIN
)


class SyncSwap(DEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name

        router_abi = SYNCSWAP_ABI['router']
        if self.network == 'zkSync':
            router_abi = SYNCSWAP_ABI['router2']

        self.router_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['router'],
            router_abi
        )
        self.pool_factory_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['classic_pool_factory'],
            SYNCSWAP_ABI['classic_pool_factory']
        )

    async def get_swap_permit(self, token_name:str):
        token_name_for_permit, version = {
            'USDT': ("Tether USD", 1),
            'USDC': ("USD Coin" if self.client.network.name == "Scroll" else 'USDC', 2)
        }[token_name]

        deadline = int(time()) + 11800

        permit_data = {
            "types": {
                "Permit": [
                    {
                        "name": "owner",
                        "type": "address"
                    },
                    {
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "name": "value",
                        "type": "uint256"
                    },
                    {
                        "name": "nonce",
                        "type": "uint256"
                    },
                    {
                        "name": "deadline",
                        "type": "uint256"
                    }
                ],
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
                ]
            },
            "domain": {
                "name": token_name_for_permit,
                "version": f"{version}",
                "chainId": self.client.chain_id,
                "verifyingContract": TOKENS_PER_CHAIN[self.client.network.name][token_name]
            },
            "primaryType": "Permit",
            "message": {
                "owner": self.client.address,
                "spender": self.router_contract.address,
                "value": 2 ** 256 - 1,
                "nonce": 0,
                "deadline": deadline
            }
        }

        text_encoded = encode_structured_data(permit_data)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded, self.client.private_key)

        return deadline, sing_data.v, hex(sing_data.r), hex(sing_data.s)

    async def get_min_amount_out(self, pool_address: str, from_token_address: str, amount_in_wei: int):
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_ABI['classic_pool'])
        min_amount_out = await pool_contract.functions.getAmountOut(
            from_token_address,
            amount_in_wei,
            self.client.address
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * 3))

    @helper
    async def swap(self, swap_data: list = None, help_deposit: bool = False, paymaster_mode:bool = False):
        from_token_name, to_token_name, amount, amount_in_wei = swap_data

        if paymaster_mode and from_token_name != self.client.token:
            amount = round(amount * 0.7, 3)
            amount_in_wei = int(amount_in_wei * 0.7)

        if help_deposit:
            to_token_name = 'ETH'

        self.logger_msg(*self.client.acc_info, msg=f'Swap on SyncSwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

        withdraw_mode = 1
        deadline = int(time()) + 11850
        pool_address = await self.pool_factory_contract.functions.getPool(from_token_address, to_token_address).call()
        min_amount_out = await self.get_min_amount_out(pool_address, from_token_address, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, SYNCSWAP_CONTRACTS[self.network]['router'], amount_in_wei, unlimited_approve=True
            )

        swap_data = abi.encode(['address', 'address', 'uint8'],
                               [from_token_address, self.client.address, withdraw_mode])

        steps = [
            pool_address,
            self.client.w3.to_hex(swap_data),
            ZERO_ADDRESS,
            '0x',
        ]

        if self.client.network.name == 'zkSync':
            steps.append(True)

        paths = [
            [steps],
            from_token_address if from_token_name != 'ETH' else ZERO_ADDRESS,
            amount_in_wei
        ]

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)

        if self.client.network.name == 'Scroll' and from_token_name != 'ETH':
            try:
                transaction = await self.router_contract.functions.swapWithPermit(
                    [paths],
                    min_amount_out,
                    deadline,
                    [
                        from_token_address,
                        2 ** 256 - 1,
                        *(await self.get_swap_permit(from_token_name))
                    ]
                ).build_transaction(tx_params)
            except Exception as error:
                if 'invalid signature' in str(error):
                    self.logger_msg(
                        *self.client.acc_info, msg=f'This account can`t swap via Permit, try to use common swap',
                        type_msg='warning'
                    )
                else:
                    self.logger_msg(
                        *self.client.acc_info, msg=f'Autism response from RPC, try to use common swap',
                        type_msg='warning'
                    )

                transaction = await self.router_contract.functions.swap(
                    [paths],
                    min_amount_out,
                    deadline,
                ).build_transaction(tx_params)

        else:
            transaction = await self.router_contract.functions.swap(
                [paths],
                min_amount_out,
                deadline,
            ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
