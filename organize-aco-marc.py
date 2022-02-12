#!/usr/bin/env python3

from pymarc import parse_xml_to_array, map_xml, record_to_xml, MARCWriter

from xml.etree import ElementTree as ET

from pathlib import Path

import argparse
import glob
import logging
import os
import subprocess

from datetime import datetime
from pprint import pprint


partners = ["LeBAU", "NIC", "NNC", "NNU", "NjP", "UaCaAUL", "aeadna"]

MARCXML_SCHEMA = "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"

nsmap = {"m": "http://www.loc.gov/MARC21/slim"}

ET.register_namespace('', nsmap["m"])

# https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
def remove_namespace(doc, namespace):
    """Remove namespace in the passed document in place."""
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in doc.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]

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
    process = None
    try:
        process = subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        logging.exception(e)
    except Exception as e:
        logging.exception(e)
    if process and process.returncode == 0:
        return True
    else:
        return False


def validate(xml_file):
    return do_cmd(['xmllint', '--noout',
        '--schema', 'MARC21slim.xsd', xml_file])


def merge_xml(input_paths, output_path):
    indent = 2
    with open(output_path, 'w') as outfile:
        outfile.write("""
<?xml version="1.0" encoding="UTF-8" ?>
<collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/MARC21/slim
        {}"
    xmlns="http://www.loc.gov/MARC21/slim">
""".format(MARCXML_SCHEMA).lstrip())
        for input_path in input_paths:
            logging.debug(f"marc xml file: {input_path}")

            tree = ET.parse(input_path)
            root = tree.getroot()
            remove_namespace(root, nsmap['m'])
            for attr in list(root.attrib):
                root.attrib.pop(attr)

            if root.tag.endswith('record'):
                root.tag = "record"
            else:
                records = root.findall('./record')

            for record in records:
                outfile.write(ET.tostring(record, encoding="unicode"))

        outfile.write('</collection>')
    return validate(output_path)

def save_as_marc(marcxml_files):
    for marcxml_file in marcxml_files:
        records = parse_xml_to_array(marcxml_file)
        logging.debug(f"number of {len(records)}")
        for record in records:
            logging.debug(record.leader)
            print(record.as_marc())

# https://www.oahelper.org/2018/09/06/pymarc-python-marc-record-processing-convert-marcxml-to-marc/
def xml2mrc(input_xml_file, output_mrc_file=None):
#     if not os.path.exists(input_xml_file):
#         logging.error(f"{input_xml_file} does not exist.")
#         exit(1)
    try:
        Path(input_xml_file).resolve(strict=True)
    except Exception as e:
        logging.exception(e)
    if not output_mrc_file:
        output_mrc_file = input_xml_file.replace('.xml', '.mrc')
    writer = MARCWriter(open(output_mrc_file, 'wb'))
    records = map_xml(writer.write, input_xml_file)
    writer.close()


parser = argparse.ArgumentParser(
    description="Organize all ACO marc records in one place.")
parser.add_argument("work_dir", metavar="WORK_DIRECTORY",
    help="Work directory")
parser.add_argument("-o", "--output-dir", metavar="OUTPUT_DIRECTORY",
    required=True,
    help="Output directory")
parser.add_argument("-d", "--debug",
    help="Enable debugging messages", action="store_true")
parser.add_argument("-v", "--validate",
    help="Validate marcxml files in marcxml_out direcory",
    action="store_true")
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

marc_dirs = find_dirs("marcxml_out", args.work_dir)

# pprint(marc_dirs)
partner_pos = len(args.work_dir) + 1

partner_files = dict.fromkeys(partners, [])

all_files = []

if args.validate:
    invalid = open('invalid.txt', 'w')

for marc_dir in marc_dirs:
    logging.debug(f"marcxml_out dir: {marc_dir}")
    
    marc_dir_rel = marc_dir[partner_pos:]
    logging.debug(f"relative marcxml_out dir: {marc_dir_rel}")

    partner, batch, marcout = marc_dir_rel.split(os.sep)
    logging.debug(f"partner {partner}")
    
    batch_date = get_batch_date(partner, batch)
    logging.debug(f"batch date: {batch_date}")

    batch_files = sorted(glob.glob(f"{marc_dir}/*_marcxml.xml"))

    for file in batch_files:
        if args.validate:
            if validate(file):
                partner_files[partner].append(file)
                all_files.append(file)
            else:
                invalid.write(file + '\n')
        else:
            partner_files[partner].append(file)
            all_files.append(file)

if args.validate:
    invalid.close()

for partner in partners:

    out_xml = os.path.join(args.output_dir, f"{partner}.xml")
    logging.debug(out_xml)

    logging.debug(f"merging partner {partner} files to {out_xml}")
    merge_xml(partner_files[partner], out_xml)

    logging.debug(f"converting {out_xml} to mrc format")
    xml2mrc(out_xml)

out_xml = os.path.join(args.output_dir, "all.xml")
logging.debug(f"merging all files to {out_xml})")
merge_xml(all_files, out_xml)

logging.debug(f"converting {out_xml} to mrc format")
xml2mrc(out_xml)

