
#!/bin/bash/python
# -*- coding: utf-8 -*-
# Author: Chen weihua
# Date: 2013-10-16
# Descripteion: Get AP and AC information via SNMP

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pprint import pprint
from ast import literal_eval
from collections import defaultdict,namedtuple
import time
import urllib2
import urllib
import uuid
import json
import re
import hashlib
import random



SNMP_PORT = 161

AC_SET = {
    '58.67.159.89': 'GuangZhou1',
    '58.67.159.90': 'GuangZhou2'
}

AC_OID = {
    '1.3.6.1.4.1.31656.6.1.2.1.1.3': 'acRunningTime',
    '1.3.6.1.4.1.31656.6.1.2.1.1.4': 'acSampleTime',
    '1.3.6.1.4.1.31656.6.1.2.1.1.5': 'acSystemTime',
    '1.3.6.1.4.1.31656.6.1.2.1.2.8': 'acMemRTUsage',
    '1.3.6.1.4.1.31656.6.1.2.1.2.9': 'acMemPeakUsage',
    '1.3.6.1.4.1.31656.6.1.2.1.2.10': 'acMemAvgUsage',
    '1.3.6.1.4.1.31656.6.1.2.1.2.13': 'acCPURTUsage',
    '1.3.6.1.4.1.31656.6.1.2.1.2.14': 'acCPUPeakUsage',
    '1.3.6.1.4.1.31656.6.1.2.1.2.15': 'acCPUAvgUsage',
    '1.3.6.1.4.1.31656.6.1.2.3.1.1': 'acNumAPInAC',
    '1.3.6.1.4.1.31656.6.1.2.2.5': 'acMacAddress',
    '1.3.6.1.4.1.31656.6.1.2.2.1': 'acIp'
}

AP_OID = {
    '1.3.6.1.4.1.31656.6.1.1.1.1.1.1': 'wtpMacAddr',
    '1.3.6.1.4.1.31656.6.1.1.1.1.1.2': 'wtpDevName',
    '1.3.6.1.4.1.31656.6.1.1.1.1.1.7': 'wtpUpTime',
    '1.3.6.1.4.1.31656.6.1.1.1.1.1.8': 'wtpOnlineTime',
    '1.3.6.1.4.1.31656.6.1.1.1.2.1.11': 'wtpMemAvgUsage',
    '1.3.6.1.4.1.31656.6.1.1.2.4.1.6':  'wtpOnlineUsrNum',
    '1.3.6.1.4.1.31656.6.1.1.17.1.1.1': 'portalCurusernum',
    '1.3.6.1.4.1.31656.6.1.1.1.2.1.18': 'wtpIP',
    '1.3.6.1.4.1.31656.6.1.1.2.5.1.10': 'wtpState',
    '1.3.6.1.4.1.31656.6.1.2.12.1.1.1': 'wtpID'
}

def send_snmp_request_for_AC(SNMP_SERVER):
    gen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget((SNMP_SERVER, SNMP_PORT)),
        '1.3.6.1.4.1.31656.6.1.2.1.1.3',
        '1.3.6.1.4.1.31656.6.1.2.1.1.4',
        '1.3.6.1.4.1.31656.6.1.2.1.1.5',
        '1.3.6.1.4.1.31656.6.1.2.1.2.8',
        '1.3.6.1.4.1.31656.6.1.2.1.2.9',
        '1.3.6.1.4.1.31656.6.1.2.1.2.10',
        '1.3.6.1.4.1.31656.6.1.2.1.2.13',
        '1.3.6.1.4.1.31656.6.1.2.1.2.14',
        '1.3.6.1.4.1.31656.6.1.2.1.2.15',
        '1.3.6.1.4.1.31656.6.1.2.3.1.1',
        '1.3.6.1.4.1.31656.6.1.2.2.5',
        '1.3.6.1.4.1.31656.6.1.2.2.1'
    )
    # record format like: [[(ObjectName(1.3.6.1.4.1.31656.6.1.2.3.1.1.0), Integer(229))]]
    return varBinds


def send_snmp_request_for_AP(SNMP_SERVER):
    gen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget((SNMP_SERVER, SNMP_PORT)),
        '1.3.6.1.4.1.31656.6.1.1.1.1.1.1',
        '1.3.6.1.4.1.31656.6.1.1.1.1.1.2',
        '1.3.6.1.4.1.31656.6.1.1.1.1.1.7',
        '1.3.6.1.4.1.31656.6.1.1.1.1.1.8',
        '1.3.6.1.4.1.31656.6.1.1.1.2.1.11',
        '1.3.6.1.4.1.31656.6.1.1.2.4.1.6',
        '1.3.6.1.4.1.31656.6.1.1.17.1.1.1',
        '1.3.6.1.4.1.31656.6.1.1.1.2.1.18',
        '1.3.6.1.4.1.31656.6.1.1.2.5.1.10',
        '1.3.6.1.4.1.31656.6.1.2.12.1.1.1'
    )
    # record format like: [[(ObjectName(1.3.6.1.4.1.31656.6.1.2.3.1.1.0), Integer(229))]]
    return varBinds


def get_wtpStaMacAddr(SNMP_SERVER):
    gen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget((SNMP_SERVER, SNMP_PORT)),
        '1.3.6.1.4.1.31656.6.1.1.8.1.1.1', # 'wtpStaMacAddr'
    )

    addr_list = defaultdict()
    for item in varBinds:
        for objname,objvalue in item:
            objname = re.search(r'(?<=\().+(?=\))', repr(objname)).group()
            objvalue = re.search(r'(?<=\().+(?=\))', repr(objvalue).replace('\'','')).group()
            addr_list[objname] =  objvalue

    return addr_list


def get_portalUserIP(SNMP_SERVER):

    OID = '1.3.6.1.4.1.31656.6.1.1.17.2.1.1' # 'portalUserip'
    gen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget((SNMP_SERVER, SNMP_PORT)),
        OID
    )

    ip_list = defaultdict()
    for item in varBinds:
        for objname,objvalue in item:
            objname = re.search(r'(?<=\().+(?=\))', repr(objname)).group()
            objvalue = re.search(r'(?<=\().+(?=\))', repr(objvalue).replace('\'','').replace('hexValue=','')).group()
            if len(objvalue) != 8:
                ipaddr = objvalue
            else:
                ipaddr = hex_to_ipaddress(objvalue)

            ip_list[objname[len(OID):]] = ipaddr

    # ip_list record format:
    # '.48.48.58.49.70.58.54.52.58.69.69.58.56.70.58.52.51.': '20.1.55.240',
    # '.48.48.58.49.70.58.54.52.58.69.69.58.57.48.58.57.57.': '20.1.84.102',

    return ip_list


def hex_to_ipaddress(hex_value):
    hex_map = defaultdict()
    for item in range(0, 16):
        if item < 10:
            hex_map[str(item)] = item
        else:
            if item == 10:
                hex_map['a'] = item
            if item == 11:
                hex_map['b'] = item
            if item == 12:
                hex_map['c'] = item
            if item == 13:
                hex_map['d'] = item
            if item == 14:
                hex_map['e'] = item
            if item == 15:
                hex_map['f'] = item

    addr = []
    for index in range(0, len(hex_value), 2):
        res = hex_map[hex_value[index]] * 16 + hex_map[hex_value[index + 1]]
        addr.append(str(res))

    return '.'.join(addr)


def package_info(device, snmp_info):
    if not snmp_info:
        return

    item_set = []
    item = defaultdict()
    iter_snmp_info = None
    OID_SET = None

    if device == 'AC':
        OID_SET = AC_OID

    elif device == 'AP':
        OID_SET = AP_OID

    OID_SET_KEY = OID_SET.keys()

    try:
        # snmp info format: [[(),(),...],[(),(),...]]
        for objname, objvalue in snmp_info:
            for key in OID_SET_KEY:

                objname = repr(objname)
                objvalue = repr(objvalue).replace('\'','').replace('hexValue=','')

                if key in objname:

                    if 'IpAddress' in objvalue:
                        # there are two format:
                        # IpAddress(59.41.33.52)
                        # IpAddress(hexValue=71671e4e) & IpAddress(hexValue=00000000)

                        # ip_pat = r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'

                        search_string = r'(?<=\().+(?=\))'
                        hex_value = re.search(search_string, repr(objvalue)).group()
                        if len(hex_value) != 8:
                            ipaddr = hex_value
                        else:
                            ipaddr = hex_to_ipaddress(hex_value)

                        item[OID_SET[key]] = ipaddr

                    else:
                        search_string = r'(?<=\().+(?=\))'
                        item[OID_SET[key]] = re.search(search_string, objvalue).group()

        return dict(item)

    except Exception as error:
        print error


def auth(act):
    try:
        passwd = "V1dian0!@BL"
        app_id = 1001
        app_version = "1.0"
        call_time = int(time.time())
        call_code = random.randint(1000, 9999)
        auth_key = hashlib.md5(hashlib.md5(str(call_time)[0:3]
                                           + str(app_id) + act
                                           + passwd + str(call_time)[3:]).hexdigest()
                               + str(call_code)).hexdigest()

        data = {"auth_key": auth_key,
                "app_id": app_id,
                "app_version": app_version,
                "call_time": call_time,
                "call_code": call_code,
                "act": act
                }
    except Exception as error:
        print error
    return data

def get_server_ip():

    def get_uid():
        node = uuid.getnode()
        mac = uuid.UUID(int=node).hex[-12:].upper()
        return mac


    try:
        address="http://shanlink-interface.iushare.com"
        act = 'get_ipinfo'
        data = auth(act)
        data['uid'] = get_uid()
        data['python_ver'] = 'v2.7.5'

        params = urllib.urlencode(data)
        req = urllib2.Request(address, params)
        response = urllib2.urlopen(req, timeout=15)
        page_str = response.read()
        page_dict = literal_eval(page_str)
        url = page_dict['interface_url'].replace('\\', '')
        return url

    except Exception as error:
        print error


def send_to_server(server_ip, device, snmp_info,acip):
    """

    :param server_ip:最终信息接受中心
    :param device: 要提交哪种设备的信息
    :param snmp_info: 要提交的信息
    :param acip: 要提交信息的设备IP
    :return:
    """

    try:
        act = None
        if device == 'AC':
            act = 'ac_heartbeat_py'
        elif device == 'AP':
            act = 'ap_heartbeat_py'

        data = auth(act)
        #data['acIp'] = re.search(r'(?<=//).+(?=:)',server_ip).group()
        data['acIp'] = acip
        data['data'] = json.dumps(snmp_info)
        params = urllib.urlencode(data)
        req = urllib2.Request(server_ip, params)
        response = urllib2.urlopen(req, timeout=15)
        page_str = response.read()
        print 'response: ', page_str

    except Exception as error:
        print error


def main():

    try:
        # =========================================
        # Get AC/AP heartbeat interface IP address
        # =========================================
        server_set = AC_SET.keys()
        while 1:
            server_ip = get_server_ip() #得到的是URL
            if server_ip:
                # print 'server_ip is: ', server_ip
                break
            else:
                print 'wait 5s to retry.'
                time.sleep(5)

        # ================================
        # Get status informateion for AC
        # ================================
        ac_info = []
        ac_pack_info = []

        for server in server_set: #58.67.159.89
            acinfo = send_snmp_request_for_AC(server)
            ac_info.extend(acinfo)

        for ac in ac_info:
            su = package_info('AC', ac)
            ac_pack_info.append(su)

        print 'There are {0} AC(s) is/are working.'.format(len(ac_pack_info))

#        send_to_server(server_ip,'AC',ac_pack_info)

        del ac_info
        del ac_pack_info
        print 'Upload AC info done.'
        print '============================'

        # ================================
        # Get status informateion for AP
        # ================================

        for server in server_set:
            # oid_dev is a map of AP OID & MAC address
            # record format: {'17.48.48.58.49.70.58.54.52.58.69.69.58.50.55.58.56.68': '00:1F:64:EE:27:8D'}
            oid_dev = defaultdict()
            ap_info = []
            ap_pack_info = []

            apinfo = send_snmp_request_for_AP(server)

# ----------------------------Get OID of AP-----------------------------------------------
            for record in apinfo:
                dev_oid = re.search(r'(?<=\().+(?=\))',repr(record[0][0])).group()[len(AP_OID.keys()[0]):]
                dev_name = '1.3.6.1.4.1.31656.6.1.1.1.1.1.1' # wtpMacAddr
                for keyname,keyvalue in record:
                    keyname = repr(keyname)
                    keyvalue = repr(keyvalue).replace('\'','')

                    if dev_name in keyname:
                        oid_dev[dev_oid] = re.search(r'(?<=\().+(?=\))',keyvalue).group()


# --------------------------Get usr mac address in AP------------------------------------
            oid_dev_keys = oid_dev.keys()

            # wtpStaMacAddr_list record format:
            # {'1.3.6.1.4.1.31656.6.1.1.8.1.1.1.17.48.48.58.49.70.58.54.52.58.69.67.58.49.69.58.49.65.17.67.67.58.51.65.58.54.49.58.68.66.58.56.49.58.70.55': 'CC:3A:61:DB:81:F7'}
            wtpStaMacAddr_list = get_wtpStaMacAddr(server)
            wtpStaMacAddr_list_keys = wtpStaMacAddr_list.keys()

            sta = defaultdict(list)
            for one in oid_dev_keys:
                for two in wtpStaMacAddr_list_keys:
                    if one in two:
                        sta[oid_dev[one]].append(wtpStaMacAddr_list[two])

# ------------------Add Portal user mac address-------------------------------------

            portal_user_list = get_portalUserIP(server)

            # portal is a map of dev oid & ip address
            # record format:
            # {'.17.48.48.58.49.70.58.54.52.58.69.67.58.49.70.58.53.50.17.57.67.58.66.55.58.48.68.58.48.68.58.55.51.58.66.57': '20.1.3.75'}
            portal = defaultdict(list)
            for ic in portal_user_list.keys():
                for ie in wtpStaMacAddr_list_keys:
                    if ic in ie:
                        for item in oid_dev_keys:
                            if item in ic:
                                portal[oid_dev[item]].append(wtpStaMacAddr_list[ie])

# ------------------------------------------------------------------------------
            for ap in apinfo:
                kk = package_info('AP', ap)
                ap_pack_info.append(kk)

            for dev in ap_pack_info:
                # Add field 'wtpStaMacAddr' to record
                if dev['wtpMacAddr'] in sta.keys():
                    dev['wtpStaMacAddr'] = sta[dev['wtpMacAddr']]
                else:
                    dev['wtpStaMacAddr'] = []

                # Add field 'portalMacAddr' to record
                if dev['wtpMacAddr'] in portal.keys():
                    dev['portalMacAddr'] = portal[dev['wtpMacAddr']]
                else:
                    dev['portalMacAddr'] = []

            print 'AC server {0} has {1} APs'.format(server,len(ap_pack_info))

            send_to_server(server_ip,'AP',ap_pack_info,server)

            print 'Upload AP info done.'

            # in case of memory leak
            del oid_dev_keys
            del wtpStaMacAddr_list_keys
            del portal
            del apinfo
            del ap_pack_info

        print 'operations done.'
        print '~~~~~~~~~~~~~~~~'

    except Exception as error:
        print error

if __name__ == '__main__':
    while 1:
        try:
            main()
            time.sleep(30)
        except Exception as error:
            print error
            time.sleep(5)
