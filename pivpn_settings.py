#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a simple script used to keep your pivpn settings updated in case you don't have a static public ip address
and you don't want to use a dynamic DNS provider.
This script has been tested using pivpn and openvpn on a raspberry pi 4b.

If you publish this code or part of it please mention my Github profile:
https://github.com/davidmachinelearning

Before running this script please make sure you followed the instructions in the instructions.txt file!
"""

__author__ = "David Forino AI Solutions"
__license__ = "MIT"
__version__ = "0.0.1"

from requests import get
from time import sleep
import smtplib
import logging
import sys
import re
import os


def send_notification(actual_ip: str):
    """
    This function sends email as a notification.
    :param actual_ip: the current ip address.
    :return: None
    """
    sender_email = ""
    receiver_email = ""
    password = ""
    message = f"The new IP address is {actual_ip}"

    # send email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def get_ip():
    """
    This function is used to get the external IP address.
    :return (str): the ip address as a string
    """
    return get('https://api.ipify.org').text


def edit_text_file(filepath: str, regex_search_string: str, replace_string: str):
    """
    This function is used to replace text inside a file.
    :param filepath: the path where the file is located.
    :param regex_search_string: string used in the regular expression to find what has to be replaced.
    :param replace_string: the string which will replace all matches found using regex_search_string.
    :return: None
    :raise RuntimeError: if regex_search_string doesn't find any match.
    """

    # open the file and read the content
    with open(filepath, "r") as f:
        text_file = f.read()

    # find all matches
    matches = re.finditer(regex_search_string, text_file)
    if matches is None:
        raise RuntimeError("No match has been found using the given regex_search_string!")

    # replace all matches with replace_string
    for match in matches:
        text_file = text_file.replace(match.group(0), replace_string)

    # overwrite the file
    with open(filepath, "w") as f:
        f.write(text_file)

    return None


def keep_trying(function_):
    """
    This function is used to try in a while loop another function.
    If something goes wrong, like no internet, the program will try forever.
    :parameter function_: the function to use.
    :return: None
    """
    while True:
        try:
            return function_()

        except Exception as err:
            logging.warning(str(err))
            logging.info("Retrying in 60 seconds...")
            sleep(60)


def main():
    """
    The main function.
    :return: None
    """

    logging.basicConfig(filename="/home/pi/log_file.log",
                        filemode='a',
                        format='%(asctime)s, %(levelname)s %(message)s',
                        datefmt='%d-%m-%y - %H:%M:%S',
                        level=logging.INFO)

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    ipfilepath = "/home/pi/ip.txt"

    while True:
        try:

            # get ip address
            ip = keep_trying(get_ip)

            # get the previous ip
            if not os.path.isfile(ipfilepath):
                with open(ipfilepath, "w") as f:
                    f.write(ip)
                old_ip = ""
            else:
                with open(ipfilepath, "r") as f:
                    old_ip = f.read()

            if old_ip != ip:
                # update ip file
                with open(ipfilepath, "w") as f:
                    f.write(ip)

                # update files and send the notification
                edit_text_file(r"/etc/pivpn/setupVars.conf", r"pivpnHOST=[\d\.]+", f"pivpnHOST={ip}")
                edit_text_file(r"/etc/openvpn/easy-rsa/pki/Default.txt", r"remote\s[\d\.]+\s", f"remote {ip} ")
                keep_trying(lambda: send_notification(ip))

                # log information
                logging.info(f"New IP address available! New: {ip}\tOld: {old_ip}")

            else:
                # log information
                logging.info(f"Same IP address: {ip}")

        except Exception as err:
            logging.error(str(err))

        # stop for 1 day
        sleep(1 * 24 * 3600)


if __name__ == "__main__":
    main()
