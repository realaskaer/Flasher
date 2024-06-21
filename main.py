import asyncio
import sys

from config import TITLE
from termcolor import cprint
from questionary import Choice, select
from utils.modules_runner import Runner
from utils.route_generator import RouteGenerator
from utils.tools import create_cex_withdrawal_list


def main():
    cprint(TITLE, 'light_green')
    cprint(f"\n☢️ It's time to warm up your nodes, baby.☢️\n", 'light_cyan', attrs=["blink"])

    runner = Runner()

    create_cex_withdrawal_list()
    print()
    #cprint('Start checking all proxies...', 'light_cyan')
    #print()

    while True:
        answer = select(
            'What do you want to do?',
            choices=[
                Choice("🚀 Start running all account with route progress", 'classic_routes_run'),
                Choice("📄 Generate classic-route for each wallet", 'classic_routes_gen'),
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
        elif answer == 'classic_routes_gen':
            generator = RouteGenerator()
            generator.classic_routes_json_save()
        else:
            print()
            answer()
            print()


if __name__ == "__main__":
    main()
