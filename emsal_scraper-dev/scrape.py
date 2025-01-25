"""
EMSAL Search Results Scraper

This script implements a scraper for fetching paginated search results from the
EMSAL UYAP court decisions database. It handles pagination, saves results as JSON,
and implements various anti-detection measures.

Features:
    - PycURL-based requests
    - User agent rotation
    - Tor circuit rotation every 20 pages
    - Progress tracking
    - CAPTCHA detection
    - Automatic retry mechanism
    - Response validation

Usage:
    python3 scrape.py

The script will fetch search results pages and save them in the data/{year}/pages/
directory. It tracks progress to allow for interrupted/resumed scraping sessions.
"""

import pycurl
from io import BytesIO
import json
import os
import time

from ip_handler import change_tor_circuit, get_tor_session
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from os import path
year = '2024'
save_dir = path.join(os.getcwd(), 'data', year, 'pages')
if not path.exists(save_dir):
    os.makedirs(save_dir)

# Configure software names and operating systems
software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value,
                  SoftwareName.SAFARI.value, SoftwareName.OPERA.value, SoftwareName.BRAVE.value,
                  SoftwareName.CHROMIUM.value,SoftwareName.GOOGLEBOT.value
                  ]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value,
                     OperatingSystem.MAC.value, OperatingSystem.ANDROID.value]

# Initialize the UserAgent object
user_agent_rotator = UserAgent(software_names=software_names, 
                             operating_systems=operating_systems)

existing_pages = list(map(lambda i: i.split('.')[0], os.listdir(save_dir)))
existing_pages = filter(lambda i: bool(i), existing_pages)
existing_pages = list(map(lambda i: int(i), existing_pages))

page = max(existing_pages, default=0) + 1
missing_pages = list(set(range(1, page)) - set(existing_pages))
get_missing_pages = True

while True:
    # Perform request
    try:
        if get_missing_pages and missing_pages:
            page = missing_pages.pop()
            existing_pages.append(page)
        elif page in existing_pages:
            page += 1
            continue
        else:
            page = max(existing_pages, default=0) + 1

        # Initialize buffer and curl object
        buffer = BytesIO()
        c = pycurl.Curl()

        # Get random user agent
        random_user_agent = user_agent_rotator.get_random_user_agent()
        # Request data
        data = {
            "data": {
                "arananKelime": "",
                "esasYil": year,
                "esasIlkSiraNo": "",
                "esasSonSiraNo": "",
                "kararYil": "",
                "kararIlkSiraNo": "",
                "kararSonSiraNo": "",
                "baslangicTarihi": "",
                "bitisTarihi": "",
                "siralama": "1",
                "siralamaDirection": "desc",
                "birimHukukMah": "",
                "pageSize": 100,
                "pageNumber": page
            }
        }

        # Set curl options
        c.setopt(pycurl.TIMEOUT, 5)
        c.setopt(pycurl.ENCODING, 'gzip,deflate')
        c.setopt(c.URL, 'https://emsal.uyap.gov.tr/aramadetaylist')
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.HTTPHEADER, [
            'Content-Type: application/json',
            f'User-Agent: {random_user_agent}'
        ])
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, json.dumps(data))
        c.setopt(c.FOLLOWLOCATION, True)
        
        # Add SSL options
        c.setopt(c.SSL_VERIFYPEER, 0)
        c.setopt(c.SSL_VERIFYHOST, 0)
        # c.setopt(c.SSLVERSION, c.SSLVERSION_MAX_DEFAULT)  # Use highest supported SSL/TLS version
        
        # Proxy configuration
        c.setopt(c.PROXY, 'socks5h://127.0.0.1:9050')
        # c.setopt(c.PROXYUSERNAME, 'username')
        # c.setopt(c.PROXYPASSWORD, 'password')

        start_time = time.time()
        c.perform()
        end_time = time.time()
        print(f"Request Time taken: {(end_time - start_time):.2f} seconds")
        
        # Get response
        response = buffer.getvalue().decode('utf-8')
        resp = json.loads(response)
        if resp['metadata']['FMTY'] != 'SUCCESS':
            print('CAPTCHA', page)
            break
        elif page > int(resp['data']['draw']) and not missing_pages:
            print('No data', page)
            break
            
        print(page)
        with open(path.join(save_dir, f"{page}.json"), "w") as f:
            json.dump(resp, f, ensure_ascii=False)

        if page % 20 == 0:
            start_time = time.time()
            change_tor_circuit()
            end_time = time.time()
            print(f"IP Change Time taken: {(end_time - start_time):.2f} seconds")




    except pycurl.error as e:
        print(f'Error: {e}')
    finally:
        # Clean up
        c.close()
        buffer.close()
        time.sleep(0.1)
