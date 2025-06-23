
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

import json
import os

CONTEXT_FILE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
CONTEXT_FILE_PATH = CONTEXT_FILE_DIR + '/context.json'

def read_context():
    try:
        with open(CONTEXT_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        raise FetchException('Missing context file')

def write_context(new_context: dict):
    try:
        with open(CONTEXT_FILE_PATH, '+w') as f:
            if 'START' not in new_context.keys():
                raise FetchException('False type of context')
            
            context = {
                'START': new_context['START']
            }
            
            json.dump(context, f)
    except Exception:
        raise FetchException('Missing context')