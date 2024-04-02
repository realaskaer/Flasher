from modules import Blockchain, Logger, Bridge
from utils.tools import helper
from starknet_py.hash.selector import get_selector_from_name
from utils.stark_signature.stark_deployer import BraavosCurveSigner
from config import (ARGENT_IMPLEMENTATION_CLASS_HASH_NEW, BRAAVOS_PROXY_CLASS_HASH,
                    BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, BRAAVOS_IMPLEMENTATION_CLASS_HASH)


class Starknet(Blockchain, Logger, Bridge):
    def __init__(self, client):
        Logger.__init__(self)
        Bridge.__init__(self, client)
        Blockchain.__init__(self, client)

    @helper
    async def deploy_wallet(self):
        await self.client.initialize_account(check_balance=True)

        if self.client.WALLET_TYPE:
            self.client.account.signer = BraavosCurveSigner(
                account_address=self.client.account.address,
                key_pair=self.client.key_pair,
                chain_id=self.client.chain_id
            )

            class_hash = BRAAVOS_PROXY_CLASS_HASH
            salt = [self.client.key_pair.public_key]
            selector = get_selector_from_name("initializer")
            constructor_calldata = [BRAAVOS_IMPLEMENTATION_CLASS_HASH, selector, len(salt), *salt]

            self.logger_msg(*self.client.acc_info, msg=f"Deploy Braavos account")
        else:

            self.logger_msg(*self.client.acc_info, msg=f"Deploy ArgentX account")

            class_hash = ARGENT_IMPLEMENTATION_CLASS_HASH_NEW
            constructor_calldata = [self.client.key_pair.public_key, 0]

        signed_tx = await self.client.account.sign_deploy_account_transaction(
            class_hash=class_hash,
            contract_address_salt=self.client.key_pair.public_key,
            constructor_calldata=constructor_calldata,
            nonce=0,
            auto_estimate=True
        )

        tx_hash = (await self.client.account.client.deploy_account(signed_tx)).transaction_hash
        return await self.client.send_transaction(check_hash=True, hash_for_check=tx_hash)

    @helper
    async def upgrade_wallet(self):
        await self.client.initialize_account()

        wallets_name = {
            1: 'Braavos',
            0: 'ArgentX'
        }

        wallet_name, wallet_type = wallets_name[self.client.WALLET_TYPE], self.client.WALLET_TYPE

        implementation_version = (await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=self.client.address,
            selector_name="get_implementation",
            calldata=[]
        )))[0] if wallet_type else await self.client.account.client.get_class_hash_at(self.client.account.address)

        braavos_hash, argent_hash = BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, ARGENT_IMPLEMENTATION_CLASS_HASH_NEW

        implement_hash = braavos_hash if wallet_type else argent_hash
        upgrade_data = [int(implement_hash)] if wallet_type else [int(implement_hash), 1, 0]

        if implementation_version != implement_hash:
            self.logger_msg(*self.client.acc_info, msg=f"Upgrade {wallet_name.capitalize()} account")

            upgrade_call = self.client.prepare_call(
                contract_address=self.client.address,
                selector_name='upgrade',
                calldata=upgrade_data
            )

            return await self.client.send_transaction(upgrade_call)
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Account already upgraded!", type_msg='warning')
