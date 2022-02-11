#!/usr/bin/env python3

from pymarc import parse_xml_to_array, marcxml

import argparse
import glob
import logging
import os
import subprocess

from datetime import datetime
from pprint import pprint


partners = ["LeBAU", "NIC", "NNC", "NNU", "NjP", "UaCaAUL", "aeadna"]

marcxml_schema = "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"


def find_dirs(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in dirs:
            result.append(os.path.join(root, name))
            # dirs[:] = []
            # del(dirs)
            # dirs.remove(name)
    return result


def get_batch_date(partner, batch):
    return datetime.strptime(batch, f"{partner}_%Y%m%d")

def do_cmd(cmdlist, **kwargs):
    cmd = list(map(str, cmdlist))
    logging.debug("Running command: %s", " ".join(cmd))
    try:
        process = subprocess.run(cmd, check=True, **kwargs)
    except Exception as e:
        logging.exception(e)
        exit(1)
    return process


def merge_xml(input_paths, output_path):
    indent = 2
    with open(output_path, 'w') as outfile:
        outfile.write("""
<?xml version="1.0" encoding="UTF-8" ?>
<collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/MARC21/slim
        {}"
    xmlns="http://www.loc.gov/MARC21/slim">
""".format(marcxml_schema).lstrip())
        for input_path in input_paths:
            logging.debug(f"marc xml file: {input_path}")
            with open(input_path) as infile:
                lines = infile.readlines()
                for line in lines[5:-1]:
                    outfile.write(" " * indent)
                    outfile.write(line)
        outfile.write('</collection>')
    do_cmd(['xmllint', '--noout',
        '--schema', marcxml_schema, output_path])


parser = argparse.ArgumentParser(
    description="Organize all ACO marc records in one place.")
parser.add_argument("work_dir", metavar="WORK_DIRECTORY",
    help="Work directory")
parser.add_argument("-o", "--output-dir", metavar="OUTPUT_DIRECTORY",
    required=True,
    help="Output directory")
parser.add_argument("-d", "--debug",
    help="Enable debugging messages", action="store_true")
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

marc_dirs = find_dirs("marcxml_out", args.work_dir)

# pprint(marc_dirs)

partner_pos = len(args.work_dir) + 1

for marc_dir in marc_dirs:
    logging.debug(f"marcxml_out dir: {marc_dir}")
    
    marc_dir_rel = marc_dir[partner_pos:]
    print(f"relative marcxml_out dir: {marc_dir_rel}")

    partner, batch, marcout = marc_dir_rel.split(os.sep)
    logging.debug(f"partner {partner}")
    
    batch_date = get_batch_date(partner, batch)
    logging.debug(f"batch date: {batch_date}")

    marc_files = sorted(glob.glob(f"{marc_dir}/*_marcxml.xml"))

    out_xml = os.path.join(args.output_dir, "out.xml")
    logging.debug(out_xml)

    merge_xml(marc_files, out_xml)



#     for marc_file in marc_files:
#         record = parse_xml_to_array(marc_file)[0]   
# 
#     print(marcxml.record_to_xml(record))

    exit(1)


