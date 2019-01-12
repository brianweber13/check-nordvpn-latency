#!/usr/bin/python3
import datetime
import os
import re
import subprocess
import sys
import time
import urllib.request

from bs4 import BeautifulSoup as bs

# constants
VPN_FILE_NAME = 'vpn-urls'


def get_servers_soup():
    site = 'https://nordvpn.com/ovpn/'
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(site, headers=hdr)
    server_list_html = urllib.request.urlopen(req).read()
    soup = bs(server_list_html, 'html.parser')
    return soup


def get_link_list():
    soup = get_servers_soup()
    vpn_urls = soup.find_all('span', class_='mr-2')
    return vpn_urls


def save_link_list():
    vpn_urls = get_link_list()
    with open(VPN_FILE_NAME, 'w') as f:
        for vpn in vpn_urls:
            f.write(vpn.text)
            f.write('\n')


def ping_each_server(num_pings):
    format_string_result = '{0:<25}{1}'
    format_numeric_result = '{0:<25}{1:3.3f}'
    ping_results_strings = [
        'Ping statistics - number of trials per server: ' + str(num_pings),
        format_string_result.format('server', 'avg latency (ms)')]
    ping_success_results = []
    ping_error_results = []
    update_vpn_url_files()
    with open(VPN_FILE_NAME, 'r') as f:
        for line in f:
            if len(line) > 1:
                line = line[:-1]
                print('pinging ', line)
                try:
                    output = subprocess.check_output(
                            ['ping', '-c', str(num_pings), line])
                    matches = re.findall(
                            r'mdev = \d+\.\d+/(?P<avg_ping_time>\d+.\d+)',
                            str(output))
                    avg_ping_time = float(matches[0])
                    ping_success_results.append((line, avg_ping_time))
                except subprocess.CalledProcessError as e:
                    error_message = None
                    if e.returncode == 1:
                        error_message = 'server did not respond'
                    elif e.returncode == 2:
                        error_message = 'name could not be resolved'
                    ping_error_results.append(
                            format_string_result.format(line, error_message))
    ping_success_results.sort(key=lambda tup: tup[1])
    for result in ping_success_results:
        ping_results_strings.append(format_numeric_result.format(result[0],
                                                                 result[1]))
    ping_results_strings += ping_error_results
    return ping_results_strings


def update_vpn_url_files():
    try:
        two_weeks_in_seconds = 14*24*60*60
        if(time.time() - os.path.getmtime(VPN_FILE_NAME) >
                two_weeks_in_seconds):
            save_link_list()
        else:
            return
    except FileNotFoundError:
        save_link_list()
        return


# used for printing ping results
def print_list(input_list):
    for item in input_list:
        print(item)


# used for saving ping results
def save_list_to_text_file(input_list):
    current_time_string = datetime.datetime.now().isoformat(
            timespec='seconds', sep='_')
    with open('ping-results_' + current_time_string, 'w') as f:
        for line in input_list:
            f.write(line)
            f.write('\n')


if __name__ == '__main__':
    ping_results = None
    if len(sys.argv) > 1:
        try:
            num_pings = int(sys.argv[1])
            ping_results = ping_each_server(num_pings)
        except ValueError as e:
            print('got a ValueError:', e)
            print('only command line argument accepted is a single integer')
            ping_results = ping_each_server(10)
    else:
        ping_results = ping_each_server(10)
    print_list(ping_results)
    print('would you like to save these results as a text file? Default = no')
    response = input('(y/n):')
    if response == 'y':
        save_list_to_text_file(ping_results)
