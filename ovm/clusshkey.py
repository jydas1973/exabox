"""
$Header:

 Copyright (c) 2019, 2021, Oracle and/or its affiliates.

NAME:
    clusshkey.py - ssh key related code using sk_command function

FUNCTION:
    ssh key manipulation code for nodes and vmnodes

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    12/14/21 - Increase coverage for ndesanto files.
    ndesanto    12/10/21 - Increase coverage on ndesanto files.
    ndesanto    08/08/19 - Create file
"""


import re


__escape_dict = {
    '\a':r'\a',
    '\b':r'\b',
    '\c':r'\c',
    '\f':r'\f',
    '\n':r'\n',
    '\r':r'\r',
    '\t':r'\t',
    '\v':r'\v',
    '\'':r'\'',
    '\"':r'\"',
    '\0':r'\0',
    '\1':r'\1',
    '\2':r'\2',
    '\3':r'\3',
    '\4':r'\4',
    '\5':r'\5',
    '\6':r'\6',
    '\7':r'\7',
    '\8':r'\8',
    '\9':r'\9'
}


def to_raw_str(text):
    """Returns a raw string representation of text"""
    new_string=''
    for char in text:
        try:
            new_string += __escape_dict[char]
        except KeyError:
            new_string += char
    return new_string


def get_sshkey_and_parts(ssh_key):
    _protocol = ""
    _key = ""
    _user = ""
    _comment = ""
    _matches = re.findall(r"((\S+)\s)(\S+)(\s(.+@\w+)){0,1}(.*){0,1}", ssh_key.replace("\n", ""))[0]
    if len(_matches) > 3:
        _protocol = _matches[1]
        _key = _matches[2]
    if len(_matches) > 4:
        _user = _matches[4]
    if len(_matches) > 5:
        _comment = _matches[5]
    return _protocol, _key, _user, _comment


def get_only_sshkey(ssh_key):
    _protocol, _key, _user, _comment = get_sshkey_and_parts(ssh_key)
    return _key


def get_sshkey_user(ssh_key):
    _protocol, _key, _user, _comment = get_sshkey_and_parts(ssh_key)
    return _user

    
