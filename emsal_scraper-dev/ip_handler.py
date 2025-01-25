#!/usr/bin/env python
"""
Tor Circuit Handler

This module provides functionality for managing Tor circuits and proxy connections.
It includes methods for checking rate limiting, changing circuits, and creating
proxy sessions.

Features:
    - Tor circuit rotation
    - Rate limit detection
    - Country-specific exit node selection
    - Proxy session management
    - Circuit status monitoring

The module is designed to work with Tor running on port 9050 (SOCKS proxy)
and port 9051 (control port).

Functions:
    get_tor_session(): Creates a requests session with Tor SOCKS proxy
    is_rate_limited(): Checks if current circuit is rate limited
    change_tor_circuit(): Rotates to a new Tor circuit
"""
import time
from stem import Signal
from stem.control import Controller
import requests

def get_tor_session():
    """_summary_

    Returns:
        _type_: _description_
    """
    session = requests.session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return session

def is_rate_limited():
    """_summary_

    Returns:
        _type_: _description_
    """
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            
            # Check circuit status
            for circuit in controller.get_circuits():
                if circuit.status == 'FAILED':
                    # Check if failure is due to rate limiting
                    print(controller.get_info('status/events/guard'))
                    for log in controller.get_info('status/events/guard'):
                        if 'Rate limiting' in log or 'Exceeded' in log:
                            return True
            return False
        
    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")
        return False


def change_tor_circuit():
    """_summary_

    Returns:
        _type_: _description_
    """
    country_codes = ['TR', 'US', 'GB', 'DE', 'FR', 'IT', 'ES', 'CA']
    country_code = ','.join(country_codes)

    while is_rate_limited():
        print('waiting for rate limit')
        time.sleep(1)

    with Controller.from_port(port=9051) as controller:
        controller.authenticate()  # If you set a password, provide it here
        # controller.set_conf('ExitNodes', '{' + country_code + '}')
        controller.signal(Signal.NEWNYM)
        # time.sleep(0.1)  # Tor requires a minimum wait time between circuit changes

        # Check if circuit is established
        if controller.get_info('status/circuit-established') == '1':
            return True

        # Check if Tor is dormant
        if controller.get_info('dormant') == '0':
            return True

    return False
