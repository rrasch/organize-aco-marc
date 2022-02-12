# organize-aco-marc

## About ##

Organize all ACO marc records in one place for ticket DLTSACO-805

## Requirements ##

- python3
- pymarc
- xmllint

## Usage ##

To merge all the individual marcxml records into one file and into
files for each partner:

    organize-aco-marc.py -o <output_directory> /path/to/work/directory

The script will search the root of the work directory for all
marcxml_out directories.

For example

    $ cd ~
    $ git clone https://github.com/rrasch/organize-aco-marc.git
    $ cd organize-aco-marc
    $ ./organize-aco-marc.py -o /tmp ~/work/aco-karms/work

This will generate the following files:

    $ cd /tmp
    $ ls *.xml *.mrc

Output:

    aeadna.mrc  all.xml    NIC.mrc  NjP.xml  NNU.mrc  out.xml
    aeadna.xml  LeBAU.mrc  NIC.xml  NNC.mrc  NNU.xml  UaCaAUL.mrc
    all.mrc     LeBAU.xml  NjP.mrc  NNC.xml  out.mrc  UaCaAUL.xml

