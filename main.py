import requests
from requests.auth import HTTPBasicAuth
import random
import string
import re
from bs4 import BeautifulSoup
import numpy as np
import hashlib
import binascii
import os

class SimHash:
    def __init__(self, bits=64):
        self.bits = bits
    def _hash(self, x):
        return bin(int(hashlib.md5(x.encode('utf-8')).hexdigest(), 16))[2:].zfill(128)
    def _compute(self, text):
        hashes = [self._hash(word) for word in text.split()]
        vector = [0] * self.bits
        for h in hashes:
            for i in range(self.bits):
                if h[i] == '1':
                    vector[i] += 1
                else:
                    vector[i] -= 1
        simhash = ''.join(['1' if v > 0 else '0' for v in vector])
        return simhash
    def get_simhash(self, text):
        return self._compute(text)
    def hamming_distance(self, simhash1, simhash2):
        return sum([1 for i in range(self.bits) if simhash1[i] != simhash2[i]])

def simHash(text1,text2):
    simhash = SimHash(bits=128)
    simhash1 = simhash.get_simhash(text1)
    simhash2 = simhash.get_simhash(text2)
    if simhash.hamming_distance(simhash1, simhash2) >= 25:
        return False
    return True

def simHash_textAndHash(text,hash):
    simhash = SimHash(bits=128)
    simhash1 = simhash.get_simhash(text)
    if simhash.hamming_distance(simhash1, hash) >= 25:
        return False
    return True

def getUrl(url,path):
    url = url if url[-1] == '/' else url+'/'
    if path[0] == '/':
        return url+path[1:]
    if path[0:2] == './':
        return url + path[2:]
    if path.startswith('http'):
        return url
    else:
        return url+path

def is_css_code(code):
    css_pattern = r'[a-zA-Z0-9\-\_]+\s*:\s*[^;]+;'
    return bool(re.search(css_pattern, code))

def is_javascript_code(code):
    js_keywords = ['function', 'var', 'let', 'const', 'return', 'if', 'else', 'for', 'while', 'switch', 'case', 'break',
                   'continue', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'document', 'window', 'alert',
                   'console']
    code_lower = code.lower()
    for keyword in js_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', code_lower):
            return True
    return False

def isHoneypot(url,timeout=500):
    jsBlackList = [
            '10110001100011110111000010101101110000010000100010000001011010001011001100001010000110101100100101101101010000010100111100100010',
            '11111001000110110111000011101101110000110000100010000101011010001011001100101010010110101100000100101101010001000100110100100110',
            '11110001000110110111000011101101110000110000100010000101011010001011001100001010010110101100000100101101010001000100110100100110',
            '11011001110110010011000011111101110001100000110011000101011101101001101001111101010011111100111100101100011101010100110100000011',
            '01000010101110000011001000001101000010100111001011010001001010001011111001011110110011111100100100101101100100101001011100100001',
            '11001000000101001100101110001010011001111110110000100111101100001011101111101101010000111101110010100111111000111110111001000101',
            '11001100100101001011011101100011011001001110000000011101101100000000111000001110100010000100101101001101000100011100001000010111',
            '00000011110101010111110010111101110001110110110011101101011100101111011100100110010011111110010100101110011000010100011100000010',
            '10110001000011110111010010101101110000100001100011000001011010001011001111001010000111001100100101101101010000010100011100100010',
            '10010110001001000100000111101011011000101010000001110111011011011001011000000011101101110011101111010110011000110010111100100010'
    ]

    response = requests.get(url,
                            timeout=timeout,
                            verify=False
                            ,headers={'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'})
    for h in response.headers:
        if 'www-authenticate' == h.lower():
            username = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])  # 替换为实际用户名
            password = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])  # 替换为实际密码
            response = requests.get(url, auth=HTTPBasicAuth(username, password),
                                    timeout=timeout,
                                    verify=False
                                    , headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'})
            if response.status_code == 200:
                return True

    soup = BeautifulSoup(response.text, 'html.parser')
    for script_tag in soup.find_all('script'):
        if 'src' in script_tag.attrs:
            try:
                text = requests.get(getUrl(url,script_tag['src']),
                                        timeout=timeout,
                                        verify=False
                                        , headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}).text.lower()
                if not is_javascript_code(text):
                    return True
                if 'finger' in text and 'print' in text:
                    return True
                for jsHash in jsBlackList:
                    if simHash_textAndHash(text, jsHash):
                        return True
            except:
                continue
        else:
            text = script_tag.get_text(strip=True).lower()
            if not is_javascript_code(text):
                return True
            if 'finger' in text and 'print' in text:
                return True
            for jsHash in jsBlackList:
                if simHash_textAndHash(text, jsHash):
                    return True

    for link in soup.find_all('link', rel='stylesheet'):
        text = requests.get(getUrl(url,link.get('href')),
                            timeout=timeout,
                            verify=False
                            , headers={
                'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}).text
        if not is_css_code(text):
            return True
    for style in soup.find_all('style'):
        if not is_css_code(style.get_text()):
            return True

    return False
