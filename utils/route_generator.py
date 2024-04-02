import json

from utils.tools import clean_progress_file
from functions import *
from web3 import AsyncWeb3
from config import ACCOUNT_NAMES
from modules import Logger
from settings import CLASSIC_ROUTES_MODULES_USING


AVAILABLE_MODULES_INFO = {
    # module_name                       : (module name, priority, tg info, can be help module, supported network)
    okx_withdraw                        : (okx_withdraw, -3, 'OKX Withdraw', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_rhino                        : (bridge_rhino, 1, 'Rhino Bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_layerswap                    : (bridge_layerswap, 1, 'LayerSwap Bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_orbiter                      : (bridge_orbiter, 1, 'Orbiter Bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_across                       : (bridge_across, 1, 'Across Bridge', 0, [2, 3, 11, 12]),
    check_pool_jediswap                 : (check_pool_jediswap, 2, 'Check MemCoin Pool on JediSwap', 0, [9]),
    # mint_token_jediswap                 : (mint_token_jediswap, 3, 'Looooot a new one shit coin =)', 0, [0]),
    # mint_token_jediswap_batch           : (mint_token_jediswap_batch, 3, 'Looooot a new one shit coin =)', 0, [0]),
    sell_shitcoin_jediswap              : (sell_shitcoin_jediswap, 3, 'Sell a new one shit coin =)', 0, [0]),
    buy_memcoin_thruster                : (buy_memcoin_thruster, 3, 'Looooot a new one shit coin =)', 0, [0]),
    sell_memcoin_thruster               : (sell_memcoin_thruster, 3, 'Sell a new one shit coin =)', 0, [0]),
    buy_cyberv                          : (buy_cyberv, 3, 'Buy CyberV NFT', 0, [0]),
    stress_test                         : (stress_test, 3, 'Stress test', 0, [0]),
    okx_deposit                         : (okx_deposit, 4, 'OKX Deposit', 0, [2, 3, 4, 8, 9, 11, 12]),
    okx_collect_from_sub                : (okx_collect_from_sub, 5, 'OKX Collect money', 0, [2, 3, 4, 8, 9, 11, 12])
}


def get_func_by_name(module_name, help_message:bool = False):
    for k, v in AVAILABLE_MODULES_INFO.items():
        if k.__name__ == module_name:
            if help_message:
                return v[2]
            return v[0]


class RouteGenerator(Logger):
    def __init__(self):
        super().__init__()
        self.w3 = AsyncWeb3()

    @staticmethod
    def classic_generate_route():
        route = []
        for i in CLASSIC_ROUTES_MODULES_USING:
            module_name = random.choice(i)
            if module_name is None:
                continue
            module = get_func_by_name(module_name)
            route.append(module.__name__)
        return route

    def classic_routes_json_save(self):
        clean_progress_file()
        with open('./data/services/wallets_progress.json', 'w') as file:
            accounts_data = {}
            for account_name in ACCOUNT_NAMES:
                if isinstance(account_name, str):
                    classic_route = self.classic_generate_route()
                    account_data = {
                        "current_step": 0,
                        "route": classic_route
                    }
                    accounts_data[str(account_name)] = account_data
            json.dump(accounts_data, file, indent=4)
        self.logger_msg(
            None, None,
            f'Successfully generated {len(accounts_data)} classic routes in data/services/wallets_progress.json\n',
            'success')
