from modules import *
from utils.networks import *
from config import OKX_WRAPED_ID
from settings import (OKX_DEPOSIT_NETWORK)


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


async def swap_rango(account_number, private_key, network, proxy, **kwargs):
    worker = Rango(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)

async def okx_withdraw(account_number, private_key, network, proxy, *args, **kwargs):
    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(*args, **kwargs)


async def okx_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(OKX_WRAPED_ID[OKX_DEPOSIT_NETWORK])

    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def okx_collect_from_sub(account_number, private_key, network, proxy):
    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.collect_from_sub()


async def swap_jediswap(client, *args, **kwargs):
    worker = JediSwap(client)
    return await worker.swap(*args, **kwargs)


async def check_pool_jediswap(account_number, private_key, network, proxy, *args, **kwargs):
    worker = JediSwap(get_client(account_number, private_key, network, proxy))
    return await worker.get_min_amount_out(*args, **kwargs)


async def swap_avnu(account_number, private_key, network, proxy, **kwargs):
    worker = AVNU(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_thruster(current_client, **kwargs):
    worker = Thruster(current_client)
    return await worker.swap(**kwargs)


async def swap_10kswap(client):
    worker = TenkSwap(client)
    return await worker.swap()


async def swap_sithswap(account_number, private_key, network, proxy):
    worker = SithSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_myswap(account_number, private_key, network, proxy):
    worker = MySwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_protoss(account_number, private_key, network, proxy):
    worker = Protoss(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def buy_memcoin_thruster(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.buy_memecoin_thruster()


async def sell_memcoin_thruster(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.sell_memecoin_thruster()


async def sell_shitcoin_jediswap(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.sell_token_jediswap()


async def buy_cyberv(account_number, private_key, _, proxy):
    network = EthereumRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.buy_cyberv()


async def buy_node(account_number, private_key, _, proxy):
    network = ArbitrumRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.buy_node()


async def approve_weth_for_buy_node(account_number, private_key, _, proxy):
    network = ArbitrumRPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.buy_node(approve_mode=True)


async def claim_and_transfer_imx(account_number, private_key, _, proxy):
    network = IMX_RPC
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.claim_and_transfer_imx()


async def stress_test(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.stress_test()

