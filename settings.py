"""
--------------------------------------------------OKX CONTROL-----------------------------------------------------------
    Выберите сети/суммы для вывода и ввода с OKX. Не забудьте вставить API ключи снизу.

    1 - ETH-ERC20                  13 - METIS-Metis         25 - USDC-Arbitrum One
    2 - ETH-Arbitrum One           14 - CORE-CORE           26 - USDC-Avalanche C-Chain
    3 - ETH-Optimism               15 - CFX-CFX_EVM         27 - USDC-Optimism
    4 - ETH-zkSync Era             16 - KLAY-Klaytn         28 - USDC-Polygon
    5 - ETH-Linea                  17 - FTM-Fantom          29 - USDC-Optimism (Bridged)
    6 - ETH-Base                   18 - MATIC-Polygon       30 - USDC-Polygon (Bridged)
    7 - AVAX-Avalanche C-Chain     19 - USDT-Arbitrum One   31 - USDC-BSC
    8 - BNB-BSC                    20 - USDT-Avalanche      32 - USDC-ERC20

    Сумма в количестве  - (0.01, 0.02)
    Сумма в процентах   - ("10", "20") ⚠️ Значения в кавычках.

    OKX_WITHDRAW_DATA | Каждый список - один модуль для вывода из биржи. Примеры работы указаны ниже:
                        Для каждого вывода указывайте [сеть вывода, (мин и макс сумма)]

    OKX_DEPOSIT_DATA | Каждый список - один модуль для депозита на биржу. Примеры работы указаны ниже:
                       Для каждого вывода указывайте [сеть депозита, (мин и макс сумма), лимитерX, лимитерY]

                       Настройка лимитного вывода на биржу. Указывать в $USD
                       лимитерX - это минимальный баланс на аккаунте, чтобы софт начал процесс вывода
                       лимитерY - это мин. и макс. сумма, которая должна остаться на балансе после вывода.
                       Если сумма депозита будет оставлять баланс на аккаунте больше 2-го значения, софт не будет
                       пытать сделать сумму депозита больше или меньше указанной в DEPOSIT_DATA

    Примеры рандомизации вывода с биржи:

    [[17, (1, 1.011)], None] | Пример установки None, для случайного выбора (выполнение действия или его пропуск)
    [[2, (0.48, 0.5)], [3, (0.48, 0.5)]] | Пример установки двух сетей, софт выберет одну случайную.

    Дополнительно к верхним примерам, для депозита на биржу поддерживается режим поиска баланса:
        [(2, 3, 4), (0.001, 0.002), 0, (0, 0)] | Пример указания нескольких сетей, cофт выберет сеть с наибольшим
                                                 балансом.

"""

WAIT_FOR_RECEIPT_CEX = True  # Если True, будет ждать получения средств во входящей сети после депозита/вывода
COLLECT_FROM_SUB_CEX = True  # Если True, будет собирать средства до/после депозита/вывода с субов на мейн аккаунт

'----------------------------------------------------------OKX---------------------------------------------------------'

OKX_WITHDRAW_DATA = [
    [2, (0.0019, 0.002)],
]

OKX_DEPOSIT_DATA = [
    [2, ('100', '100'), 0, (0.4, 0.5)],
]


"""
-----------------------------------------------------BRIDGE CONTROL-----------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Не забудьте вставить API ключ для LayerSwap снизу. Для каждого моста поддерживается уникальная настройка
       
        Arbitrum = 1                    zkSync Era = 11     X Layer = 56     
        Arbitrum Nova = 2               Zora = 12 
        Base = 3                        Ethereum = 13
        Linea = 4                       Avalanche = 14
        Manta = 5                       BNB Chain = 15
        Polygon = 6                     Metis = 26        
        Optimism = 7                    OpBNB = 28
        Scroll = 8                      Mantle = 29
        Starknet = 9                    ZKFair = 45
        Polygon zkEVM = 10              Blast = 49
                                           
    Сумма в количестве  - (0.01, 0.02)
    Сумма в процентах   - ("10", "20") ⚠️ Значения в кавычках
    
    ACROSS_TOKEN_NAME | Укажите токен для бриджа. Поддерживаются: ETH, BNB, MATIC, USDC, USDC.e (Bridged), USDT. 
                        Если у бриджа указано 2 токена в скобках см. BUNGEE_TOKEN_NAME, то бридж сможет делать бриджи
                        между разными токенами. Справа от параметра, для каждого бриджа указаны доступные токены.
                        
    ACROSS_AMOUNT_LIMITER | Настройка лимитных бриджей. Указывать в $USD
                            1 значение - это минимальный баланс на аккаунте, чтобы софт начал процесс бриджа
                            2 значение - это мин. и макс. сумма, которая должна остаться на балансе после бриджа
                            Если сумма для бриджа будет оставлять баланс на аккаунте больше второго значения,
                            софт не будет пытать сделать сумму бриджа больше или меньше указанной
                    
    BUNGEE_ROUTE_TYPE | Установка своего роута для совершения транзакции, по умолчанию (0) - самый лучший. 
                        1-Across   3-Celer     5-Stargate   7-Synapse      9-Hop
                        2-CCTP     4-Connext   6-Socket     8-Symbiosis    10-Hyphen   
    
    BRIDGE_SWITCH_CONTROL | Позволяет использовать один и тот же бридж два раза. По умолчанию каждая цифра закреплена за
                            за своим бриджем (см. значения снизу), чтобы поменять эту настройку
                            ориентируйтесь зависимостями снизу и указывайте для каждого моста свое значение настройки,
                            по которой он будет работать.
                            
                            1-ACROSS     3-LAYERSWAP    5-ORBITER     7-RELAY
                            2-BUNGEE     4-NITRO        6-OWLTO       8-RHINO
                               
"""

WAIT_FOR_RECEIPT_BRIDGE = True  # Если True, будет ждать получения средств во входящей сети после бриджа

'-----------------------------------------------------Native Bridge----------------------------------------------------'

NATIVE_CHAIN_ID_FROM = [3]                 # Исходящая сеть
NATIVE_CHAIN_ID_TO = [13]                  # Входящая сеть
NATIVE_BRIDGE_AMOUNT = (0.001, 0.001)      # (минимум, максимум) (% или кол-во)
NATIVE_TOKEN_NAME = 'ETH'
NATIVE_AMOUNT_LIMITER = 0, (0, 0)

'--------------------------------------------------------Across--------------------------------------------------------'

ACROSS_CHAIN_ID_FROM = [7, 1]                # Исходящая сеть
ACROSS_CHAIN_ID_TO = [4]                   # Входящая сеть
ACROSS_BRIDGE_AMOUNT = ("100", "100")      # (минимум, максимум) (% или кол-во)
ACROSS_TOKEN_NAME = 'ETH'
ACROSS_AMOUNT_LIMITER = 0, (0, 0)

'--------------------------------------------------------Bungee--------------------------------------------------------'

BUNGEE_CHAIN_ID_FROM = [10]                  # Исходящая сеть
BUNGEE_CHAIN_ID_TO = [11]                    # Входящая сеть
BUNGEE_BRIDGE_AMOUNT = (0.001, 0.003)       # (минимум, максимум) (% или кол-во)
BUNGEE_TOKEN_NAME = ('ETH', 'USDC')          # ETH, BNB, MATIC, USDC, USDC.e, USDT
BUNGEE_ROUTE_TYPE = 0                       # см. BUNGEE_ROUTE_TYPE
BUNGEE_AMOUNT_LIMITER = 0, (0, 0)

'-------------------------------------------------------LayerSwap------------------------------------------------------'

LAYERSWAP_CHAIN_ID_FROM = [11]               # Исходящая сеть
LAYERSWAP_CHAIN_ID_TO = [3]                  # Входящая сеть
LAYERSWAP_BRIDGE_AMOUNT = ('95', '97')     # (минимум, максимум) (% или кол-во)
LAYERSWAP_TOKEN_NAME = ('ETH', 'ETH')     # ETH, USDC, USDC.e
LAYERSWAP_AMOUNT_LIMITER = 0, (0, 0)


'--------------------------------------------------------Nitro---------------------------------------------------------'

NITRO_CHAIN_ID_FROM = [1]                   # Исходящая сеть
NITRO_CHAIN_ID_TO = [11]                    # Входящая сеть
NITRO_BRIDGE_AMOUNT = (0.001, 0.001)        # (минимум, максимум) (% или кол-во)
NITRO_TOKEN_NAME = ('ETH', 'USDC')          # ETH, USDC, USDT
NITRO_AMOUNT_LIMITER = 0, (0, 0)

'-------------------------------------------------------Orbiter--------------------------------------------------------'

ORBITER_CHAIN_ID_FROM = [7, 3, 5]           # Исходящая сеть
ORBITER_CHAIN_ID_TO = [6]                   # Входящая сеть
ORBITER_BRIDGE_AMOUNT = (8, 9)              # (минимум, максимум) (% или кол-во)
ORBITER_TOKEN_NAME = 'USDC'
ORBITER_AMOUNT_LIMITER = 0, (0, 0)

'--------------------------------------------------------Owlto---------------------------------------------------------'

OWLTO_CHAIN_ID_FROM = [1]                 # Исходящая сеть
OWLTO_CHAIN_ID_TO = [56]                    # Входящая сеть
OWLTO_BRIDGE_AMOUNT = (0.001, 0.001)       # (минимум, максимум) (% или кол-во)
OWLTO_TOKEN_NAME = 'ETH'
OWLTO_AMOUNT_LIMITER = 0, (1, 2)

'--------------------------------------------------------Relay---------------------------------------------------------'

RELAY_CHAIN_ID_FROM = [11]                # Исходящая сеть
RELAY_CHAIN_ID_TO = [7]                   # Входящая сеть
RELAY_BRIDGE_AMOUNT = (0.001, 0.001)      # (минимум, максимум) (% или кол-во)
RELAY_TOKEN_NAME = 'ETH'
RELAY_AMOUNT_LIMITER = 0, (0, 0)

'--------------------------------------------------------Rhino---------------------------------------------------------'

RHINO_CHAIN_ID_FROM = [7]                # Исходящая сеть
RHINO_CHAIN_ID_TO = [11]                 # Входящая сеть
RHINO_BRIDGE_AMOUNT = (1, 1.8)           # (минимум, максимум) (% или кол-во)
RHINO_TOKEN_NAME = ('USDC', 'ETH')       # ETH, BNB, MATIC, USDC, USDT
RHINO_AMOUNT_LIMITER = 0, (0, 0)

BRIDGE_SWITCH_CONTROL = {
    1: 1,  # ACROSS
    2: 2,  # BUNGEE
    3: 3,  # LAYERSWAP
    4: 4,  # NITRO
    5: 5,  # ORBITER
    6: 6,  # OWLTO
    7: 7,  # RELAY
    8: 8,  # RHINO
}

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------
    WALLETS_TO_WORK = 0 | Софт будет брать кошельки из таблице по правилам, описанным снизу
    0       = все кошельки подряд
    3       = только кошелек №3
    4, 20   = кошелек №4 и №20
    [5, 25] = кошельки с №5 по №25

    ACCOUNTS_IN_STREAM      | Количество кошельков в потоке на выполнение. Если всего 100 кошельков, а указать 10,
                                то софт сделает 10 подходов по 10 кошельков
    CONTROL_TIMES_FOR_SLEEP | Количество проверок, после которого для всех аккаунтов будет включен рандомный сон в
                                моменте, когда газ опуститься до MAXIMUM_GWEI и аккаунты продолжат работать

    EXCEL_PASSWORD          | Включает запрос пароля при входе в софт. Сначала установите пароль в таблице
    EXCEL_PAGE_NAME         | Название листа в таблице. Пример: 'EVM'
    GOOGLE_SHEET_URL        | Ссылка на вашу Google таблицу с прогрессом аккаунтов
    GOOGLE_SHEET_PAGE_NAME  | Аналогично EXCEL_PAGE_NAME
    MAIN_PROXY              | Прокси для обращения к API бирж. Формат - log:pass@ip:port. По умолчанию - localhost
"""
SOFTWARE_MODE = 0               # 0 - последовательный запуск / 1 - параллельный запуск
ACCOUNTS_IN_STREAM = 10          # Только для SOFTWARE_MODE = 1 (параллельный запуск)
WALLETS_TO_WORK = 0             # 0 / 3 / 3, 20 / [3, 20]
SAVE_PROGRESS = True            # Включает сохранение прогресса аккаунта для Classic-routes

'-----------------------------------------------------GAS CONTROL------------------------------------------------------'
GAS_CONTROL = False             # Включает контроль газа
MAXIMUM_GWEI = 40               # Максимальный GWEI для работы софта, изменять во время работы софта в maximum_gwei.json
SLEEP_TIME_GAS = 100            # Время очередной проверки газа
CONTROL_TIMES_FOR_SLEEP = 5     # Количество проверок
GAS_LIMIT_MULTIPLIER = 1.5      # Множитель газ лимита для транзакций. Поможет сэкономить на транзакциях
GAS_PRICE_MULTIPLIER = 1.5      # Множитель цены газа для транзакций. Ускоряет выполнение или уменьшает цену транзакции

'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 5              # Количество повторений при ошибках
SLEEP_TIME_RETRY = (5, 10)      # (минимум, максимум) секунд | Время сна после очередного повторения

'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False
SLEEP_TIME_ACCOUNTS = (5, 10)             # (минимум, максимум) секунд
SLEEP_TIME_MODULES = (5, 10)      # (минимум, максимум) секунд

'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = True               # True или False | Включает использование прокси
MOBILE_PROXY = False             # Включает использование мобильных прокси. USE_PROXY должен быть True
MOBILE_PROXY_URL_CHANGER = [
    '',
]  # ['link1', 'link2'..] | Ссылки для смены IP. Софт пройдется по всем ссылкам

'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE = 5                  # 0.54321 = 0.54321%, 1 = 1% | Slippage, на сколько % вы готовы получить меньше

'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = True       # True или False Включает безлимитный Approve для контракта

'------------------------------------------------SECURE DATA-----------------------------------------------------------'
# BITGET API KEYS https://www.okx.com/ru/account/my-api
BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""

# EXCEL AND GOOGLE INFO
EXCEL_PASSWORD = False
EXCEL_PAGE_NAME = "EVM"

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""

# https://2captcha.com/enterpage
TWO_CAPTCHA_API_KEY = ""

"""
--------------------------------------------------OTHER SETTINGS--------------------------------------------------------
    ZRO_DST_CHAIN = Сеть, где софт будет пытаться клеймить ZRO. Можно поставить ZRO_DST_CHAIN = [1, 2, 3], тогда софт
                    склеймит в разных сетях (Arbitrum - 1, Base - 2, Optimism - 3) 
    WAIT_FOR_RECEIPT_L0 = Если = True, софт будет ожидать получения токенов после бриджа в сеть клейма.
"""

WAIT_FOR_RECEIPT_L0 = True
ZRO_DST_CHAIN = [1, 2, 3]

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

---------------------------------------------------HELPERS--------------------------------------------------------------        

    
    okx_withdraw                  # смотри OKX CONTROL
    bridge_across                 # смотри BRIDGE CONTROL
    bridge_rhino                  # смотри BRIDGE CONTROL
    bridge_layerswap              # смотри BRIDGE CONTROL
    bridge_orbiter                # смотри BRIDGE CONTROL
    okx_deposit                   # ввод средств на биржу
    okx_collect_from_sub          # сбор средств на субАккаунтов на основной счет
    
----------------------------------------------------CUSTOM--------------------------------------------------------------        
    
    smart_claim_zro                     # claim ZRO c поиском баланса. см. ZRO_DST_CHAIN
    smart_transfer_zro                  # transfer ZRO (c поиском баланса) на адрес в таблице из колонки CEX_ADDRESS
    
------------------------------------------------------------------------------------------------------------------------        

    
    Выберите необходимые модули для взаимодействия
    Вы можете создать любой маршрут, софт отработает строго по нему. Для каждого списка будет выбран один модуль в
    маршрут, если софт выберет None, то он пропустит данный список модулей. 
    Список модулей сверху.
    
    CLASSIC_ROUTES_MODULES_USING = [
        ['smart_claim_zro'],
        ['smart_transfer_zro'],
        ...
    ]
"""

CLASSIC_ROUTES_MODULES_USING = [
     #['okx_withdraw'],
     ['smart_claim_zro'],
     ['smart_transfer_zro'],
]
