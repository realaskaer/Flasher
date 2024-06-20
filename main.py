import asyncio
import sys

from config import TITLE
from termcolor import cprint
from questionary import Choice, select
from utils.modules_runner import Runner
from utils.route_generator import RouteGenerator
from utils.tools import create_cex_withdrawal_list, prepare_wallets


async def prepare_wallets_main():
    await prepare_wallets()


def main():
    cprint(TITLE, 'light_green')
    cprint(f"\n☢️ It's time to warm up your nodes, baby.☢️\n", 'light_cyan', attrs=["blink"])

    runner = Runner()

    create_cex_withdrawal_list()
    print()
    cprint('Start checking all proxies...', 'light_cyan')
    print()

    while True:
        answer = select(
            'What do you want to do?',
            choices=[
                Choice("🚀 Claim and Transfer ZRO", 'classic_routes_run'),
                Choice('❌ Exit', "exit")
            ],
            qmark='🛠️',
            pointer='👉'
        ).ask()

        if answer == 'classic_routes_run':
            print()
            asyncio.run(runner.run_accounts())
            print()
        elif answer == 'exit':
            sys.exit()
        else:
            print()
            answer()
            print()


if __name__ == "__main__":
    main()
