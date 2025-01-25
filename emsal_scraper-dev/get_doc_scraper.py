"""
EMSAL Document Scraper

This script implements an asynchronous scraper for fetching individual court decision
documents from the EMSAL UYAP system. It uses Tor for anonymity and implements various
anti-detection measures.

Features:
    - Asynchronous document fetching using aiohttp
    - Concurrent batch processing (69 requests at a time)
    - User agent rotation
    - Tor circuit rotation based on response times
    - Progress tracking and state preservation
    - Automatic retry mechanism

Usage:
    python3 get_doc_scraper.py

The script will fetch documents based on randomly generated IDs within a specified range
and save them as JSON files in the docs/ directory.
"""

import os
import json
from os import path
import time
import asyncio
import aiohttp
import aiofiles

from ip_handler import change_tor_circuit
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from aiohttp_socks import ProxyConnector
# import requests

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# Change IP
# check_ip_url = "https://api.ipify.org/?format=json"
# old = requests.get(check_ip_url, proxies=proxies).json()['ip']
while not change_tor_circuit():
    print("Failed to change Tor circuit. Retrying...")
    time.sleep(1)
# new = requests.get(check_ip_url, proxies=proxies).json()['ip']
# print(f"Old IP: {old}\nNew IP: {new}")

async def fetch_document(session, doc_id, user_agent_rotator, save_dir, stats):
    url = f'https://emsal.uyap.gov.tr/getDokuman?id={doc_id}'
    # url = f'http://karararama.yargitay.gov.tr/getDokuman?id={doc_id}'
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': user_agent_rotator.get_random_user_agent()
    }
    
    try:
        start_time = time.time()
        async with session.get(url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            end_time = time.time()
            time_taken = end_time - start_time
            
            stats['counter'] += 1
            stats['ip_counter'] += 1
            
            print(f"Request Time taken: {time_taken:.2f} seconds")
            stats['ip_resp_time'] = (stats['ip_resp_time'] * (stats['ip_counter'] - 1) + time_taken) / stats['counter']
            
            resp = json.loads(response_text)
            
            if resp['metadata']['FMTY'] != 'SUCCESS':
                print('CAPTCHA', doc_id)
                return False
                
            print(stats['counter'], f'{(time.time() - stats["init_time"]):.2f}', 'seconds')
            print(f'{((time.time() - stats["init_time"]) / stats["counter"]):.2f}', 'seconds per request', end='\n'*2)
            
            async with aiofiles.open(path.join(save_dir, f"{doc_id}.json"), "w") as f:
                await f.write(json.dumps(resp, ensure_ascii=False))
                
            return True

    except asyncio.TimeoutError:
        print(f"Request timed out for doc_id: {doc_id}")
        return False
    except Exception as e:
        print(f"Error fetching doc_id {doc_id}: {str(e)}")
        return False

async def process_batch(session, doc_ids_batch, user_agent_rotator, save_dir, stats):
    tasks = []
    for doc_id in doc_ids_batch:
        task = asyncio.create_task(
            fetch_document(session, doc_id, user_agent_rotator, save_dir, stats)
        )
        tasks.append((doc_id, task))
    
    failed_docs = []
    for doc_id, task in tasks:
        try:
            success = await task
            if not success:
                failed_docs.append(doc_id)
                # Cancel all remaining tasks
                for _, remaining_task in tasks:
                    if not remaining_task.done():
                        remaining_task.cancel()
                return failed_docs, False
        except asyncio.CancelledError:
            failed_docs.append(doc_id)
    
    return failed_docs, True

async def main():
    BATCH_SIZE = 69  # Number of concurrent requests

    # start_id = 8_442_378
    from numpy import random
    ids_to_scrape = list(random.randint(2_000_000, 10_000_000, BATCH_SIZE * 10))
    ids_to_scrape = list(map(lambda i: str(i) + '00', ids_to_scrape))
    # start_id = 8_600_000 + 100_000
    
    # Initialize UserAgent
    software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value,
                     SoftwareName.SAFARI.value, SoftwareName.OPERA.value, SoftwareName.BRAVE.value,
                     SoftwareName.CHROMIUM.value, SoftwareName.GOOGLEBOT.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value,
                        OperatingSystem.MAC.value, OperatingSystem.ANDROID.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
    
    # Setup directories
    save_dir = path.join(os.getcwd(), 'docs')
    if not path.exists(save_dir):
        os.makedirs(save_dir)

    # Get existing documents
    # existing_docs = list(map(lambda i: i.split('.')[0], os.listdir(save_dir)))
    # existing_docs = filter(lambda i: bool(i), existing_docs)
    # existing_docs = list(map(lambda i: int(i) // 100, existing_docs))

    with open('existing_docs.txt', 'r') as f:
        existing_docs = list(map(lambda i: i.strip(), f.readlines()))

    existing_docs = list(set(existing_docs))
    
    print(f'Existing: {len(existing_docs)}', sep='\n')

    with open('existing_docs.txt', 'w') as f:
        for i in os.listdir(save_dir):
            if not i.endswith('.json'):
                continue
            doc_id = i.split('.')[0]
            if doc_id not in existing_docs:
                f.write(f"{doc_id}\n")
                existing_docs.append(doc_id)

    
    stats = {
        'counter': 0,
        'ip_counter': 0,
        'ip_resp_time': 0.0,
        'init_time': time.time()
    }

    get_docs = list(set(ids_to_scrape) - set(existing_docs))

    connector = ProxyConnector.from_url('socks5://127.0.0.1:9050', rdns=True)
    # connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while get_docs:
            # Take a batch of documents
            current_batch = get_docs[:BATCH_SIZE]
            get_docs = get_docs[BATCH_SIZE:]
            
            failed_docs, batch_success = await process_batch(
                session, current_batch, user_agent_rotator, save_dir, stats
            )
            stats['ip_resp_time'] /= BATCH_SIZE
            
            print(batch_success)
            print(stats['ip_resp_time'])
            # If batch failed or average response time is too high
            if not batch_success or stats['ip_resp_time'] > 1:
                stats['ip_resp_time'] = 0.0
                stats['ip_counter'] = 0
                # Put failed documents back in the queue
                get_docs = failed_docs + get_docs
                exit(35)

if __name__ == "__main__":
    asyncio.run(main())