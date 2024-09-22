from modules import *
from utils.networks import *
from settings import ZRO_DST_CHAIN


def get_client(account_number, private_key, network, proxy) -> Client:
    return Client(account_number, private_key, network, proxy)


def get_network_by_chain_id(chain_id):
    return {
        1: ArbitrumRPC,
        2: Arbitrum_novaRPC,
        3: BaseRPC,
        4: LineaRPC,
        5: MantaRPC,
        6: PolygonRPC,
        7: OptimismRPC,
        8: ScrollRPC,
        9: StarknetRPC,
        10: Polygon_ZKEVM_RPC,
        11: zkSyncEraRPC,
        12: ZoraRPC,
        13: EthereumRPC,
        14: AvalancheRPC,
        15: BSC_RPC,
        16: MoonbeamRPC,
        17: HarmonyRPC,
        18: TelosRPC,
        19: CeloRPC,
        20: GnosisRPC,
        21: CoreRPC,
        22: TomoChainRPC,
        23: ConfluxRPC,
        24: OrderlyRPC,
        25: HorizenRPC,
        26: MetisRPC,
        27: AstarRPC,
        28: OpBNB_RPC,
        29: MantleRPC,
        30: MoonriverRPC,
        31: KlaytnRPC,
        32: KavaRPC,
        33: FantomRPC,
        34: AuroraRPC,
        35: CantoRPC,
        36: DFK_RPC,
        37: FuseRPC,
        38: GoerliRPC,
        39: MeterRPC,
        40: OKX_RPC,
        41: ShimmerRPC,
        42: TenetRPC,
        43: XPLA_RPC,
        44: LootChainRPC,
        45: ZKFairRPC,
        46: BlastRPC,
        50: IMX_RPC
    }[chain_id]


def get_key_by_id_from(args, chain_from_id):
    private_keys = args[0].get('stark_key'), args[0].get('evm_key')
    current_key = private_keys[1]
    if chain_from_id == 9:
        current_key = private_keys[0]
    return current_key


async def swap_syncswap(current_client, **kwargs):
    worker = SyncSwap(current_client)
    return await worker.swap(**kwargs)


async def swap_zk(current_client, **kwargs):
    worker = Custom(current_client)
    return await worker.swap_zk(**kwargs)


async def claim_taiko(account_number, private_key, _, proxy):
    network = TaikoRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.claim_taiko()


async def transfer_taiko(account_number, private_key, _, proxy):
    network = TaikoRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_taiko()


async def claim_zk(account_number, private_key, _, proxy):
    network = zkSyncEraRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.full_claim_zk()


async def transfer_zk(account_number, private_key, _, proxy):
    network = zkSyncEraRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_zk()


async def smart_transfer_zro(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_transfer_zro()


async def smart_claim_zro(account_number, private_key, _, proxy):
    network = ArbitrumRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.full_claim_zro()


async def cex_deposit_util(current_client, dapp_id: int, deposit_data: tuple):
    class_name = {
        1: OKX,
    }[dapp_id]

    return await class_name(current_client).deposit(deposit_data=deposit_data)


async def okx_withdraw_util(current_client, **kwargs):
    worker = Binance(current_client)
    return await worker.withdraw(**kwargs)


async def okx_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=1)


async def okx_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=1)


async def transfer_zro(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_zro()


async def claim_and_transfer_imx(account_number, private_key, _, proxy):
    network = IMX_RPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.claim_and_transfer_imx()
