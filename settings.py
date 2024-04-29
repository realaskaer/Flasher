"""
--------------------------------------------------OKX CONTROL-----------------------------------------------------------
    Выберите сети/суммы для вывода и ввода с OKX. Не забудьте вставить API ключи снизу.

    1 - ETH-ERC20              9  - CELO-Celo           17 - KLAY-Klaytn        25 - USDT-Avalanche
    2 - ETH-Arbitrum One       10 - ONE-Harmony         18 - FTM-Fantom         26 - USDT-Arbitrum One
    3 - ETH-zkSync Lite        11 - GLMR-Moonbeam       19 - AVAX-Avalanche     27 - USDC-ERC20   
    4 - ETH-Optimism           12 - MOVR-Moonriver      20 - ASTR-Astar         28 - USDC-Optimism
    5 - ETH-Starknet           13 - METIS-Metis         21 - BNB-BSC            29 - USDC-Avalanche
    6 - ETH-zkSync Era         14 - CORE-CORE           22 - USDT-ERC20         30 - USDC-Arbitrum One
    7 - ETH-Linea              15 - CFX-Conflux         23 - USDT-Polygon       31 - USDT-Polygon
    8 - ETH-Base               16 - ZEN-Horizen         24 - USDT-Optimism      32 - USDC-Optimist (Bridged)

------------------------------------------------------------------------------------------------------------------------
"""
OKX_WITHDRAW_NETWORK = 32                 # Сеть вывода из OKX
OKX_WITHDRAW_AMOUNT = (10, 10)   # (минимальная, максимальная) сумма для вывода из OKX

OKX_DEPOSIT_NETWORK = 5                  # Сеть из которой планируется пополнение OKX
OKX_DEPOSIT_AMOUNT = (0.0001, 0.0001)    # (минимальная, максимальная) сумма для пополнения OKX

OKX_BALANCE_WANTED = 0.005               # Необходимый баланс на аккаунтах для уравнителя (make_balance_to_average)

"""
------------------------------------------------BRIDGE CONTROL----------------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Софт работает только с нативным токеном(ETH). Не забудьте вставить API ключ для LayerSwap снизу.
    Для каждого моста поддерживается уникальная настройка
    
    Можно указать минимальную/максимальную сумму или минимальный/максимальный % от баланса
    
    Количество - (0.01, 0.02)
    Процент    - ("10", "20") ⚠️ Значения в скобках
       
     (A)Arbitrum = 1                    Polygon ZKEVM = 10 
        Arbitrum Nova = 2            (A)zkSync Era = 11     
     (A)Base = 3                       *Zora = 12 
        Linea = 4                       Ethereum = 13
        Manta = 5                      *Avalanche = 14
       *Polygon = 6                     BNB Chain = 15
     (A)Optimism = 7                 (O)Metis = 26        
        Scroll = 8                     *OpBNB = 28
        Starknet = 9                   *Mantle = 29
                                        ZKFair = 45   
    
    * - не поддерживается в Rhino.fi
    (A) - сети, поддерживаемые Across мостом
    (0) - поддерживается только для Orbiter моста
    ORBITER_CHAIN_ID_FROM(TO) = [2, 4, 16] | Одна из сетей будет выбрана
"""
ORBITER_CHAIN_ID_FROM = [7]                # Исходящая сеть
ORBITER_CHAIN_ID_TO = [45]                  # Входящая сеть
ORBITER_DEPOSIT_AMOUNT = (8.5, 8.5)    # (минимум, максимум) ETH или %
ORBITER_TOKEN_NAME = 'USDC'

LAYERSWAP_CHAIN_ID_FROM = [9]                # Исходящая сеть
LAYERSWAP_CHAIN_ID_TO = [4]                  # Входящая сеть
LAYERSWAP_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) ETH или %

RHINO_CHAIN_ID_FROM = [7]                # Исходящая сеть
RHINO_CHAIN_ID_TO = [11]                  # Входящая сеть
RHINO_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) ETH или %

ACROSS_CHAIN_ID_FROM = [9]                # Исходящая сеть
ACROSS_CHAIN_ID_TO = [4]                  # Входящая сеть
ACROSS_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) ETH или %

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------
    GLOBAL_NETWORK | Блокчейн для основного взаимодействия ⚠️
    
    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8
    Base = 3                Starknet = 9  
    Linea = 4               Polygon ZKEVM = 10   
    Manta = 5               zkSync Era = 11      
    Polygon = 6             Zora = 12
                            Blast = 46
    
    WALLETS_TO_WORK = 0 | Софт будет брать кошельки из таблице по правилам, описаным снизу
    0       = все кошельки подряд
    3       = только кошелек №3 
    4, 20   = кошелек №4 и №20
    [5, 25] = кошельки с №5 по №25
    
    ACCOUNTS_IN_STREAM      | Количество кошельков в потоке на выполнение. Если всего 100 кошельков, а указать 10,
                                то софт сделает 10 подходов по 10 кошельков
                                
    EXCEL_PASSWORD          | Включает запрос пароля при входе в софт. Сначала установите пароль в таблице
    EXCEL_PAGE_NAME         | Название листа в таблице. Пример: 'Starknet' 
"""
GLOBAL_NETWORK = 11
ACCOUNTS_IN_STREAM = 1
WALLETS_TO_WORK = 0            # 0 / 3 / 3, 20 / [3, 20]
NUMBER_OF_STREAM = 1

'-------------------------------------------------GAS CONTROL----------------------------------------------------------'

GAS_LIMIT_MULTIPLIER = 1.5      # Множитель газ лимита для транзакций. Поможет сэкономить на транзакциях
GAS_PRICE_MULTIPLIER = 1.0      # Множитель цены газа для транзакций. Ускоряет выполнение или уменьшает цену транзакции

'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 10000              # Количество повторений при ошибках
SLEEP_TIME_RETRY = (0, 0)      # (минимум, максимум) секунд | Время сна после очередного повторения

'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False
SLEEP_TIME = (5, 10)             # (минимум, максимум) секунд
SLEEP_TIME_STREAM = (5, 10)      # (минимум, максимум) секунд

'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = False               # True или False | Включает использование прокси

'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE = 50                  # 0.54321 = 0.54321%, 1 = 1% | Slippage, на сколько % вы готовы получить меньше

'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = True       # True или False Включает безлимитный Approve для контракта

'------------------------------------------------SECURE DATA-----------------------------------------------------------'
# OKX API KEYS https://www.okx.com/ru/account/my-api
OKX_API_KEY = ""
OKX_API_SECRET = ""
OKX_API_PASSPHRAS = ""

# EXCEL AND GOOGLE INFO
EXCEL_PASSWORD = False
EXCEL_PAGE_NAME = "EVM"

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""


"""
--------------------------------------------------OTHER SETTINGS--------------------------------------------------------
    NEW_WALLET_TYPE | Определяет какой кошелек будет задеплоен, если вы решили создать новый. 0 - ArgentX | 1 - Braavos
    MEMCOIN_AMOUNT | Сумма, на которую будет куплен щиток
    MEMCOIN_MINT_ADDRESS | Адреса кошельков, на которые придут токены. Будет сделана 1 транзакция, в которой будет
        реализован мультикол, чтобы лутануть хороший объем.
     
    MEMCOIN_MODE_CODE | 1 - отдаем ETH и получаем токены, ровно на 0.01 ETH
                        0 - получаем 1% токенов от суплая и отдаем необходимое количество ETH за 1% токенов
"""

# в софте всего 10 тиров нод
NODE_COUNT = 10     # кол-во нод к покупке за 1 транзакцию
NODE_TIER_BUY = 1   # тир ноды к покупке, если поставить 0, то софт будет пытаться взять по очереди все тиры до NODE_TIER_MAX
NODE_TIER_MAX = 5   # максимальный тир, при NODE_TIER_BUY = 0

CYBERV_NFT_COUNT = 0

ZKFAIR_GAS_PRICE = 21000
ZKFAIR_GAS_LIMIT = 25000
ZKFAIR_CLAIM_REFUND_PHASES = [1, 2, 3, 4]

MEMCOIN_AMOUNT = 0.004  # сумма в ETH для MEMCOIN_MODE_CODE = 1

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

---------------------------------------------------HELPERS--------------------------------------------------------------        

    
    okx_withdraw                  # смотри OKX CONTROL
    upgrade_stark_wallet          # обновляет кошелек, во время маршрута
    deploy_stark_wallet           # деплоит кошелек, после вывода с OKX
    bridge_across                 # смотри BRIDGE CONTROL
    bridge_rhino                  # смотри BRIDGE CONTROL
    bridge_layerswap              # смотри BRIDGE CONTROL
    bridge_orbiter                # смотри BRIDGE CONTROL
    okx_deposit                   # ввод средств на биржу
    okx_collect_from_sub          # сбор средств на субАккаунтов на основной счет
    
----------------------------------------------------CUSTOM--------------------------------------------------------------        
    
    
    buy_memcoin_thruster         # делает Swap ETH на щиток через Thruster
    sell_memcoin_thruster        # делает Swap щитка (свапает весь баланс щитка) на ETH через Thruster
    
    buy_cyberv                   # покупает CyberV NFT на сайте https://launchpad.gmnetwork.ai/CyberV
    
    stress_test
    check_pool_jediswap
    mint_token_avnu
    mint_token_jediswap           # делает Swap ETH на щиток через JediSwap
    mint_token_jediswap_batch     # делает Swap ETH на щиток через JediSwap (1 транзакция на все кошельки)
    sell_shitcoin_jediswap        # делает Swap щитка (свапает весь баланс щитка) на ETH через JediSwap
    
---------------------------------------------------STARKNET-------------------------------------------------------------        

    upgrade_stark_wallet
    deploy_stark_wallet
    
------------------------------------------------------------------------------------------------------------------------        

    
    Выберите необходимые модули для взаимодействия
    Вы можете создать любой маршрут, софт отработает строго по нему. Для каждого списка будет выбран один модуль в
    маршрут, если софт выберет None, то он пропустит данный список модулей. 
    Список модулей сверху.
    
    CLASSIC_ROUTES_MODULES_USING = [
        ['mint_token_jediswap'],
        ['sell_shitcoin'],
        ...
    ]
"""

CLASSIC_ROUTES_MODULES_USING = [
     ['approve_weth_for_buy_node'],
     ['buy_node'],
]
