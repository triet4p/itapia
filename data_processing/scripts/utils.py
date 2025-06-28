from datetime import datetime, timezone, time as dt_time
class FetchException(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
        
TO_FETCH_TICKERS = [
    # Tech
    'AAPL', # Apple
    'MSFT', # Microsoft
    'NVDA', # Nvidia
    'ASML', # ASML,
    'TSM', # Taiwan Semiconductor,
    'SAP', # SAP,
    'INFY', # Infosys
    "ORCL", # Oracle
    "ADBE", # Adobe
    "CRM", # Salesforce
    "AMD", # Advanced Micro Devices,
    "INTC", # Intel Corporation
    # Financials
    'JPM', # JPMorgan Chase,
    'BAC', # Bank of America,
    'GS', # Goldman Sachs,
    'HSBC', # HSBC,
    'BCS', # Barclays,
    'MUFG', # Mitsubishi UFJ Financial Group,
    'DB', # Deutsche Bank
    'V', #Visa
    'MA', # Mastercard
    'WFC', # Well Fargo
    'BRK-B', # Berkshire Hathaway
    # Healthcare
    'JNJ', # Johnson & Johnson,
    'PFE', # Pfizer,
    'MRK', # Merck,
    'NVS', # Novartis,
    'AZN', # AstraZeneca,
    'SNY', # Sanofi,
    'UNH', # UnitedHealth Group,
    'LLY', # Eli Lilly and Company
    'ABBV', # AbbVie
    'MDT', # Metronic
    # Consumer Discretionary
    'AMZN', # Amazon,
    'TSLA', # Tesla,
    'HD', # Home Depot,
    'MCD', # McDonald's,
    'SBUX', # Starbucks,
    'HMC', # Honda Motor Company,
    'BMW.DE', # BMW,
    'NKE', #Nike
    'TM', #Toyota
    'MC.PA',
    # Consumer Staples
    'PG', # Procter & Gamble,
    'KO', # Coca-Cola,
    'WMT', # Walmart,
    'UL', # Unilever,
    'NESN.SW', # Nestlé,
    'COST', # Costco,
    'BUD', # Anheuser-Busch InBev,
    'PEP', # Pepsi Co
    'MDLZ', # Mondelez International,
    'TGT', # Target Cor
    # Energy
    'XOM', # Exxon Mobil,
    'CVX', # Chevron,
    'BP', # BP,
    'ENB', # Enbridge
    'SHEL', # Shell plc
    'TTE', # Total energies
    'SLB', # Schlumberger
    # Industrials
    'BA', # Boeing,
    'CAT', # Caterpillar,
    'GE', # General Electric,
    'HON', # Honeywell,
    'LMT', # Lockheed Martin,
    'UPS', # United Parcel Service
    'AIR.PA', # Airbus
    'SIE.DE', # Siemens
    # Utilities
    'NEE', # NextEra Energy,
    'DUK', # Duke Energy,
    'BCE', # Bell Canada,
    'TEF', # Telefónica,
    'SO', # Southern COmpany
    'ENGI.PA', # Engie PA
    # Communitcation
    'GOOGL', # GOOGLE
    'VZ', # Verizon Communications,
    'T', # AT&T,
    'META', 
    'NFLX', #Netflix
    'DIS', # Disney
    'TMUS', # T-mobile US
    # Material
    'BHP', # BHP
    'RIO',
    'LIN',
    'DOW',
    # Real Estate
    'PLD', # Prologis,
    'AMT',
    'SPG',
    'EQIX'
]

TO_FETCH_TICKERS_BY_REGION = {
    "americas": [
        'AAPL', 'MSFT', 'NVDA', 'JPM', 'BAC', 'GS', 'WFC', 'V', 'MA', 'BRK-B',
        'JNJ', 'PFE', 'MRK', 'UNH', 'LLY', 'ABBV', 'MDT', 'AMZN', 'TSLA', 'HD',
        'MCD', 'SBUX', 'NKE', 'PG', 'KO', 'WMT', 'COST', 'BUD', 'PEP', 'MDLZ',
        'TGT', 'XOM', 'CVX', 'BA', 'CAT', 'GE', 'HON', 'LMT', 'UPS', 'NEE',
        'DUK', 'SO', 'GOOGL', 'VZ', 'T', 'META', 'NFLX', 'DIS', 'TMUS', 'PLD',
        'AMT', 'SPG', 'EQIX', 'LIN', 'DOW', 'SLB', 'ENB', 'BCE', 'ORCL', 'ADBE', 
        'CRM', 'AMD', 'INTC'
    ],
    "europe": [
        'SAP', 'DB', 'BMW.DE', 'SIE.DE', 'HSBC', 'BCS', 'AZN', 'UL', 'BP', 'RIO',
        'BHP', 'SHEL', 'NVS', 'NESN.SW', 'SNY', 'MC.PA', 'AIR.PA', 'ENGI.PA',
        'TTE', 'TEF', 'ASML'
    ],
    "asia_pacific": [
        'TSM', 'MUFG', 'HMC', 'TM', 'INFY'
    ]
}

DEFAULT_START_DATE = datetime(2018, 1, 1, tzinfo=timezone.utc)

REGION_TIME_ZONE = {
    'americas': "America/New_York",
    'europe': 'Europe/Berlin',
    'asia_pacific': 'Asia/Tokyo'
}

MARKET_OPEN_TIME = dt_time(8, 0, 0)
MARKET_CLOSE_TIME = dt_time(18, 0, 0)
