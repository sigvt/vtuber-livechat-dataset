import os
from os import path
import time
from functools import lru_cache
import requests

# convert currency symbol to three-letter string
CURRENCY_TO_TLS_MAP = {
    '$': 'USD',
    '£': 'GBP',
    '¥': 'JPY',
    '₩': 'KRW',
    '₪': 'ILS',
    '€': 'EUR',
    '₱': 'PHP',
    '₹': 'INR',
    'A$': 'AUD',
    'CA$': 'CAD',
    'HK$': 'HKD',
    'MX$': 'MXN',
    'NT$': 'TWD',
    'NZ$': 'NZD',
    'R$': 'BRL',
}

API_HOST = 'currency-exchange.p.rapidapi.com'
API_KEY = os.environ['CURRENCY_API_KEY']
SNAPSHOT_DIR = path.join(path.dirname(__file__), '../currency_snapshot')


def normalizeCurrency(sym: str) -> str:
    return CURRENCY_TO_TLS_MAP.get(sym, sym)


def fetchRate(src: str, tgt: str) -> float:
    print(f'querying exchange rate for: {src} > {tgt}')

    querystring = {"to": tgt, "from": src}
    headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': API_HOST}
    response = requests.request("GET",
                                f"https://{API_HOST}/exchange",
                                headers=headers,
                                params=querystring)
    data = response.text
    return float(data)


@lru_cache(maxsize=256)
def getRateToJPY(tls: str) -> float:
    try:
        with open(path.join(SNAPSHOT_DIR, tls), 'r') as f:
            return float(f.read())
    except FileNotFoundError:
        time.sleep(5)
        rate = fetchRate(tls, "JPY")
        with open(path.join(SNAPSHOT_DIR, tls), 'w') as f:
            f.write(str(rate))
        return rate


import math


@lru_cache(maxsize=256)
def convertToJPY(amount: float, currency: str) -> float:
    return round(amount * getRateToJPY(currency))


def applyJPY(col):
    res = convertToJPY(col['amount'], col['currency'])
    if math.isinf(res):
        print(col)
        raise col
    return res