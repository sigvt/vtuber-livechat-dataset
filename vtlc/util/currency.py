import os
from os import path
import time
from functools import lru_cache
import requests

# convert currency to three-letter symbol
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
    'AED': 'AED',
    'ARS': 'ARS',
    'BAM': 'BAM',
    'BGN': 'BGN',
    'BOB': 'BOB',
    'BYN': 'BYN',
    'CA$': 'CAD',
    'CHF': 'CHF',
    'CLP': 'CLP',
    'COP': 'COP',
    'CRC': 'CRC',
    'CZK': 'CZK',
    'DKK': 'DKK',
    'DOP': 'DOP',
    'EGP': 'EGP',
    'GTQ': 'GTQ',
    'HK$': 'HKD',
    'HNL': 'HNL',
    'HRK': 'HRK',
    'HUF': 'HUF',
    'INR': 'INR',
    'ISK': 'ISK',
    'JOD': 'JOD',
    'MAD': 'MAD',
    'MKD': 'MKD',
    'MX$': 'MXN',
    'MYR': 'MYR',
    'NIO': 'NIO',
    'NOK': 'NOK',
    'NT$': 'TWD',
    'NZ$': 'NZD',
    'PEN': 'PEN',
    'PHP': 'PHP',
    'PLN': 'PLN',
    'PYG': 'PYG',
    'QAR': 'QAR',
    'R$': 'BRL',
    'RON': 'RON',
    'RSD': 'RSD',
    'RUB': 'RUB',
    'SAR': "SAR",
    'SEK': 'SEK',
    'SGD': 'SGD',
    'TRY': 'TRY',
    'UYU': 'UYU',
    'ZAR': 'ZAR',
}

API_HOST = 'currency-exchange.p.rapidapi.com'
API_KEY = os.environ['CURRENCY_API_KEY']
SNAPSHOT_DIR = path.join(path.dirname(__file__), '../currency_snapshot')


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