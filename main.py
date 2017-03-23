#!/usr/bin/python

import os, sys, re
import argparse
import socket
import time

BUFF_SIZE = 1024

def print_header():
    print """
     _   _                       _____              
    | | | |_   _ _ __   ___ _ __|  ___|   _ ________
    | |_| | | | | '_ \ / _ \ '__| |_ | | | |_  /_  /
    |  _  | |_| | |_) |  __/ |  |  _|| |_| |/ / / / 
    |_| |_|\__, | .__/ \___|_|  |_|   \__,_/___/___|
           |___/|_|                                 
    """

def write_data(filename, data):
    #FIXME: Check if file exists
    with open(filename, 'w') as package_file:
        package_file.write(data)
        
def fuzz(host, port, data):
    response = ""
    
    try:
        s = socket.socket()         # Create a socket object
    except socket.error as msg:
        print "[-] " + msg[1]
        s = None
        exit()
            
    try:
        s.connect((host, port))
        
        start = time.time()
        s.send(data);
        
        resp_temp = s.recv(BUFF_SIZE)
        while resp_temp:
            response += resp_temp
            resp_temp = s.recv(BUFF_SIZE)
            
        end = time.time()
        time_elapsed = end - start
        
        s.close
    except socket.error as msg:
        print "[-] " + msg[1]
        s.close()
        s = None
        exit()
        
    return (response, time_elapsed)

def run_sequal(host, port, package, file_handlers, output):
    first = True
    len_differ = False
    rows = 0
    for key, value in file_handlers.items():
        tmp = len(value.readlines())
        if first:
            rows = tmp
            first = False
        else:
            if rows != tmp:
                len_differ = True
                if tmp > rows:
                    rows = tmp
        
        value.seek(0)
    
    if len_differ:
        print "[!] Warning, the files have different number of rows"
    
    print "[*] Number of iterations: {0}".format(rows)
    
    items = []
    html = "<html>\n<head></head>\n<body>\n<table border=\"2\">"
    for i in range(rows):
        tmp = package
        for key, value in file_handlers.items():
            line = value.readline().strip()
            tmp = tmp.replace(key, line)
            items.append(line)
            if output:
                write_data(output + "/packages/" + str(i) + "_request.txt", tmp)
        
        response, time_elapsed = fuzz(host, port, tmp)
        return_code = response.split(' ')[1]
        
        if output:
            write_data(output + "/packages/" + str(i) + "_response.txt", response)
            
        item_str = '|'.join('"' + str(x) + '"' for x in items)
        print "[*] {0}: {1} : {2} : {3}".format(i, item_str, return_code, time_elapsed)
        if output:
            write_data(output + "/result.csv", "{0},{1},{2},{3}\n".format(i, item_str, return_code, time_elapsed))
            html += "<tr>\n<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td>\n".format(i, item_str, return_code, time_elapsed)
        
        items = []
    
    html += "</table>\n</body>\n</html>"
    write_data(output + "/result.html", html)
        
def main(hostname, port, data_file, mode, output):    
    with open(data_file, 'r') as package_file:
        package_data = package_file.read()
    
    m = re.findall('\$\S+\$', package_data)
    
    file_handlers = {}
    for f in m:
        file_handlers[f] = open(f.replace('$', ''), 'r')
        
    if mode == "seq":
        run_sequal(hostname, port, package_data, file_handlers, output)
    else:
        print "[-] Error, mode unknown"
        
    for key, value in file_handlers.items():
        value.close()

    
if __name__ == "__main__":

    print_header()
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('hostname', action='store', 
        help='Target Hostname or IP')

    parser.add_argument('port', action='store', help='Target port')
    
    parser.add_argument('data_file', action='store', 
        help='File containing http package')
        
    parser.add_argument('mode', action='store',
        help='Fuzzing mode(seq or brute)')
    
    parser.add_argument('-s', '--ssl', action='store_true', dest='ssl',
        default=False, help='Activate SSL')
    
    parser.add_argument('-o', '--out', action='store', dest='output',
        default="", help='Path to output directory')

    args = parser.parse_args()
    
    if args.output:
        if os.path.isdir(args.output):
            if os.listdir(args.output):
                print "[-] Error, output directory is not empty"
                exit()
        else:
            os.mkdir(args.output)
        os.mkdir(args.output + "/packages")
    
    # Should this be printed inside of main insted?
    print "[*] Hostname: {0}".format(args.hostname)
    print "[*] Port: {0}".format(args.port)
    print "[*] Package File: {0}".format(args.data_file)
    print "[*] Mode: {0}".format(args.mode)
    print "[*] SSL: {0}".format(args.ssl)
    
    if args.output:
        print "[*] Output Path: {0}\n".format(args.output)
    
    main(args.hostname, int(args.port), args.data_file, args.mode, args.output)
    
