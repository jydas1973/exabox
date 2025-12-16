#!/bin/python
#
# $Header: ecs/exacloud/exabox/network/NetworkUtils.py /main/3 2025/09/23 07:26:34 aararora Exp $
#
# NetworkUtils.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      NetworkUtils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/30/25 - ER 38132942: Single stack support for ipv6
#    aararora    08/28/24 - Bug 36998256: IPv6 fixes
#    aararora    04/16/24 - ER 36485120: IP Utility methods - IPv4 vs IPv6
#    aararora    04/16/24 - Creation
#
import ipaddress
from exabox.core.Error import ExacloudRuntimeError

class NetworkUtils:

    def mGetIPv4IPv6Payload(self, payload, key_single_stack='ip', key_dual_stack='ipv6'):

        ip_single_stack = None
        ipv6_dual = None
        if key_dual_stack in payload:
            ipv6_dual = payload.get(key_dual_stack)
        if key_single_stack in payload:
            ip_single_stack = payload.get(key_single_stack)
        if not ip_single_stack and not ipv6_dual:
            _msg = "Both single stack and dual stack IPs are not defined."
            raise ExacloudRuntimeError(0x0735, 0xA, _msg)
        elif ip_single_stack and not ipv6_dual:
            return (ip_single_stack, ipv6_dual)
        else:
            # v6netmask is a prefix length and not IPv6 IP
            if key_dual_stack == 'v6netmask':
                return (ip_single_stack, str(ipv6_dual))
            else:
                return (ip_single_stack, str(ipaddress.IPv6Address(ipv6_dual)))

    def mGetIPv4IPv6PayloadNotNoneValues(self, payload, key_single_stack='ip', key_dual_stack='ipv6'):

        ip_single_stack, ipv6_dual = self.mGetIPv4IPv6Payload(payload, key_single_stack, key_dual_stack)
        # IP for single stack config can never be None
        if not ipv6_dual:
            ipv6_dual = "::"
        if key_dual_stack == 'v6netmask':
            return (ip_single_stack, str(ipv6_dual))
        ipv4 = '0.0.0.0'
        ipv6 = '::'
        # Single stack ipv6
        if ':' in ip_single_stack:
            ipv6 = ip_single_stack
        # Dual stack
        if ipv6_dual != '::':
            ipv4 = ip_single_stack
            ipv6 = ipv6_dual
        # Single stack ipv4
        if ':' not in ip_single_stack and ipv6_dual == '::':
            ipv4 = ip_single_stack
        return (ipv4, str(ipaddress.IPv6Address(ipv6)))

    def mGetIPv4IPv6Scans(self, scanPayload, aReturnIPv4IPv6Scans=False):

        ipSingleStackScans = []
        ipv6DualScans = []
        if 'ips' in scanPayload:
            ipSingleStackScans = scanPayload['ips']
        if 'v6ips' in scanPayload:
            ipv6DualScans = scanPayload['v6ips']
        if not ipSingleStackScans and not ipv6DualScans:
            _msg = "Both single stack and dual stack Scan IPs are not defined."
            raise ExacloudRuntimeError(0x0735, 0xA, _msg)
        if not ipSingleStackScans:
            ipSingleStackScans = []
        if not ipv6DualScans:
            ipv6DualScans = []
        # Below is to take case of bond monitor configuration for ipv6 only config since it expects
        # ipv4 and ipv6 scans in a tuple format.
        # Whereas in xml update we don't expect blank ipv4 IPs (in mCustomerXMLUpdate method).
        if aReturnIPv4IPv6Scans:
            if len(ipv6DualScans) == 0 and len(ipSingleStackScans) > 0:
                # check for ipv6 config
                if ':' in ipSingleStackScans[0]:
                    ipv4Scans = []
                    ipv6Scans = ipSingleStackScans
                    return (ipv4Scans, ipv6Scans)
        return (ipSingleStackScans, ipv6DualScans)

    def mClassifyStack(self, aPayload, aIPKey="ip", aIPKeyDualStack="ipv6"):
        """
        Returns stack_type:
            - stack_type: 'dual' or 'single'
        """
        ip_single_stack = aPayload.get(aIPKey)
        ipv6_dual_stack = aPayload.get(aIPKeyDualStack)

        if ip_single_stack and ipv6_dual_stack:
            return 'dual'
        elif ip_single_stack:
            return 'single'

    @classmethod
    def mIsIPv6(self, aIP):
        """
        Checks if the given IP address is ipv6 or ipv4
        """
        try:
            ipaddress.IPv6Address(aIP)
            return True
        except ipaddress.AddressValueError:
            try:
                ipaddress.IPv4Address(aIP)
                return False
            except ipaddress.AddressValueError:
                raise ExacloudRuntimeError(f"Invalid IP address: {aIP}.")