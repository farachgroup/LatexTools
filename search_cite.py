#!/usr/bin/env python3
# -*- coding: utf-8; -*-
#
# This script finds all DBLP citations and adds the DBLP bibtex entry
# to a bibtex file.  In addition, if a citation is of the form
# \cite{!list:of:keywords}, then it performs a keyword search on DBLP.
# If a unique entry is found, that entry is added to the bibtex file,
# and a bibalias is added to map the ! citation to the corresponding
# DBLP citation. Tested with Python 2.7.  That means that this feature
# only works if the bibalias package is included in the latex file.
#
# Copyright (c) 2017 Martin Farach-Colton <martin@farach-colton.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os, os.path
import re
import sys
import time
import argparse
import getopt
from urllib.request import urlopen

def existing_DBLP_tags(bib_files, quiet):
    """Fetch existing DBLP tags from bibtex files"""

    re_bibtex_dblp_citations = re.compile(r'@.*\{(DBLP:[^,]*),')

    known_tags = set([])

    if not quiet: print('Looking for DBLP tags in:')
    for fname in bib_files:
        if os.path.isfile(fname):
            if not quiet: print(' > %s' % fname)
            with open(fname, 'r') as fin:
                for line in fin:
                    for match in re.finditer(re_bibtex_dblp_citations,line):
                        for tag in match.groups():
                            known_tags.add(tag)
                for tags in known_tags:
                    if not quiet: print('      * %s' % tags)

    if not quiet: print()
    return known_tags

def existing_bibalias(bibalias_files, tex_files, quiet):
    """look up and return a dictionary of existing bibalias entries"""

    re_bibalias_defs = re.compile(r'^[^%]bibalias\{([^}]*\}\{[^}]*)')

    known_aliases = dict()

    if not quiet: print('Looking for bibaliases in {}:'.format(bibalias_files))

    for bal_file in bibalias_files:
        if os.path.isfile(bal_file):
            if not quiet: print(' > %s' % bal_file)
            with open(bal_file, 'r') as fin:
                for line in fin:
                    for match in re.finditer(re_bibalias_defs,line):
                        for pair in match.groups():
                            key, dblp = pair.split('}{')
                            known_aliases[key]=dblp
                            print_pair = key + ' -> ' + dblp
                            if not quiet: print('      * %s' % print_pair)

    for tex_file in tex_files:
        if os.path.isfile(tex_file):
            if not quiet: print(' > %s' % tex_file)
            with open(tex_file, 'r') as fin:
                for line in fin:
                    for match in re.finditer(re_bibalias_defs,line):
                        for pair in match.groups():
                            key, dblp = pair.split('}{')
                            known_aliases[key]=dblp
                            print_pair = key + ' -> ' + dblp
                            if not quiet: print('      * %s' % print_pair)

    if not quiet: print()

    return known_aliases



def existing_citations_of_interest(main_tex_file, quiet):
    """Find and return pair of DBLP, search citation lists"""

    aux_file = main_tex_file + '.aux'

    other_keys = set()
    constrained_keys = set()
    dblp_keys = set()

    if not quiet: print("Looking for citations in %s" % aux_file)
    with open(aux_file, 'r') as fin:
        for line in fin:
            if line.startswith(r'\citation'):
                tags = line[10:-2]
                for tag in tags.split(','):
                    if tag.startswith('DBLP:'):
                        dblp_keys.add(tag)
                    elif tag.startswith(r'!'):
                        constrained_keys.add(tag)
                    else:
                        other_keys.add(tag)


    if not quiet:
        print('   DBLP citations:')
        for key in dblp_keys:
            print('    * %s' % key)

        print('   Constrained citations:')
        for key in constrained_keys:
            print('    * %s' % key)

        print('   Other citations:')
        for key in other_keys:
            print('    * %s' % key)

        print()

    return (dblp_keys, constrained_keys)


def add_bibalias(constrained_missing_bibalias, bibalias_file, quiet):
    """adds needed bibaliases to the bibalias file

    Fetch the bibalias keys from DBLP
    Check that there's only one match
    If not, report
    If so, write out a bibalias entry and add DBLP key to the return value
    """

    re_get_count = re.compile(r'<c sc="([^\"]*)')
    re_get_tag = re.compile(r'<key>([^<]*)</key>')
    added_dblp = set()

    with open(bibalias_file, 'a') as fout:
        if not quiet: print('\nAdding missing bibaliases to %s:' % bibalias_file)

        for key in constrained_missing_bibalias:
            # relaplace : with +
            key_translate_for_url = '+'.join(key[1:].split(r':'))

            url_fmt = 'http://dblp.org/search/publ/api?q={0}&format=xml'
            dblp_fetch_tag_url = url_fmt.format(key_translate_for_url)
            dblp_query_result = urlopen(dblp_fetch_tag_url).read().decode(encoding='UTF-8', errors='strict')

            for match in re.finditer(re_get_count, dblp_query_result):
                dblp_count = int(match.group(0)[7:])
                if (dblp_count != 1):
                    print(' * Warning: search key %s does not match '
                          'a unique DBLP entry' % key)
                    break
                else:
                    for tag in re.finditer(re_get_tag,dblp_query_result):
                        tag_string = 'DBLP:' + tag.group(0)[5:-6]
                        added_dblp.add(tag_string)
                        if not quiet: print(' * {}'.format(key))
                        bibalias_string = r'\bibalias{' + key + r'}{' + tag_string + r'}' + '\n\n'
                        print(bibalias_string, file=fout)
                time.sleep(1)


    return added_dblp


def add_bibtex(missing_bibtex, main_bibtex_file, quiet):
    """adds needed dblp bibtex to the dblp bibtex file file"""

    if not quiet: print('\nFetching BibTeX records from DBLP for missing keys:')

    re_bibtex_items = re.compile(r'(@[a-zA-Z]+\{[^@]*\n\})',re.DOTALL)
    re_bibtex_item_key = re.compile(r'@[a-zA-Z]+\{(DBLP\:[^,]+),\s*',re.DOTALL)

    fetched_keys = set()

    with open(main_bibtex_file, 'a') as fout:

        for unknown_key in missing_bibtex:
            if not quiet: print(' * %s' % unknown_key)

            url_fmt = 'http://dblp.uni-trier.de/rec/bib2/{0}.bib'
            dblp_url = url_fmt.format(unknown_key[5:])
            dblp_bibtex_entry = urlopen(dblp_url).read().decode(encoding='UTF-8', errors='strict')

            for match in re.finditer(re_bibtex_items,dblp_bibtex_entry):
                for dblp_bibtex_item in match.groups():
                    key = re.match(re_bibtex_item_key,dblp_bibtex_item).group(1)
                    if key not in fetched_keys:
                        print(dblp_bibtex_item, file=fout, end="\n\n")
                        fetched_keys.add(key)
            time.sleep(1)


def get_tex_files(main_tex_file, quiet):
    """parses log file to find the tex files"""

    tex_filenames = re.compile('\((\.[^\s]*\.tex)')

    log_file = main_tex_file + '.log'

    tex_files = set()
    if os.path.isfile(log_file):
        if not quiet: print('Finding all tex files in {}:'.format(log_file))
        with open(log_file, 'r') as fin:
            for line in fin:
                for match in re.finditer(tex_filenames,line):
                    for new_file in match.groups():
                        tex_files.add(new_file)
                        if not quiet: print(' > %s' % new_file)
    else:
        print('Missing log file. Run latex before running this script.',
              file=sys.stderr)
        sys.exit(1)
    if not quiet: print()
    return tex_files

def get_bal_files(main_tex_file, main_bal_file, quiet):
    """parses log file to find the bal files"""

    bal_filenames = re.compile('\((\.[^\s]*\.bal)')

    log_file = main_tex_file + '.log'

    bal_files = set()
    bal_files.add(main_bal_file)
    if os.path.isfile(log_file):
        if not quiet: print('Finding all bal files in {}:'.format(log_file))
        with open(log_file, 'r') as fin:
            for line in fin:
                for match in re.finditer(bal_filenames,line):
                    for group in match.groups():
                        new_file = group
                        bal_files.add(new_file)
                        if not quiet: print(' > %s' % new_file)
    else:
        print('Missing log file. Run latex before running this script.',
              file=sys.stderr)
        sys.exit(1)

    if not quiet: print()
    return bal_files


def get_bib_files(main_tex_file, main_bibtex_file, quiet):
    """parses aux file to find the bib files"""

    bib_filenames = re.compile(r'bibdata{(.*)}')

    aux_file = main_tex_file + '.aux'
    bib_files = set()
    bib_files.add(main_bibtex_file)

    if os.path.isfile(aux_file):
        if not quiet: print('Finding all bib files in {}:'.format(aux_file))
        with open(aux_file, 'r') as fin:
            for line in fin:
                for match in re.finditer(bib_filenames,line):
                    for file in line[9:-2].split(','):
                        new_file = file + '.bib'
                        bib_files.add(new_file)
                        if not quiet: print(' > %s' % new_file)
    else:
        print('Missing aux file. Run latex before running this script.',
              file=sys.stderr)
        sys.exit(1)

    if not quiet: print()
    return bib_files


#  Here's the main body of code

def main(argv):

    parser = argparse.ArgumentParser(description='Scans through log, aux, '
    'bibtex and bibalias file.  Finds missing citation entries.  If the '
    + 'citation entry is a DBLP key, it downloads the corresponding bibtex '
    + 'entry from DBLP to a bibtex file (default dblp.bib).  If the citation '
    + 'is of the form !list:of:keywords, then it checks if the keyword '
    + 'combination matches a unique DBLP entry.  If so, it adds a bibalias '
    + 'from the !list:of:keywords to the corresponding DBLP tag and downloads '
    + 'the bibtex entry from DBLP, if needed.')
    parser.add_argument('file', help='Main tex file')
    parser.add_argument('-b', '--bibtex_file',
                        help='File in which to store fetched DBLP Bibtex items',
                        default='dblp.bib')
    parser.add_argument('-q', '--quiet',
                        help='Dial down the verbosity of message output',
                        action='store_true')
    args = parser.parse_args()

    main_tex_file = args.file[:-4] if args.file.endswith('.tex') else args.file
    if not os.path.isfile(main_tex_file + '.tex'):
        print('File %s.tex does not exist' % main_tex_file)
        sys.exit(1)
    if not args.quiet: print('Main tex file: %s' % main_tex_file)

    main_bibalias_file = main_tex_file + '.bal'

    tex_files = get_tex_files(main_tex_file, args.quiet)
    bib_files = get_bib_files(main_tex_file,args.bibtex_file, args.quiet)
    bibalias_files = get_bal_files(main_tex_file, main_bibalias_file, args.quiet)

    known_DBLP_tags = existing_DBLP_tags(bib_files, args.quiet)
    known_aliases = existing_bibalias(bibalias_files, tex_files, args.quiet)

    alias_constrained_keys = {x for x in known_aliases.keys() if x.startswith(r'!')}
    alias_DBLP_tags = {x for x in known_aliases.values() if x.startswith(r'DBLP:')}

    (cited_dblp_keys, cited_constrained_keys) = existing_citations_of_interest(main_tex_file, args.quiet)

    new_possibly_missing_dblp_tags = set()
    missing_constrained_bibalias_keys = cited_constrained_keys - alias_constrained_keys # I think the - alias_contrained_keys might not do anything 
    if missing_constrained_bibalias_keys != set():
        new_possibly_missing_dblp_tags = add_bibalias(missing_constrained_bibalias_keys,main_bibalias_file, args.quiet)


    missing_bibtex = (new_possibly_missing_dblp_tags|cited_dblp_keys|alias_DBLP_tags) - known_DBLP_tags
    if missing_bibtex != set():
        add_bibtex(missing_bibtex,args.bibtex_file, args.quiet)

    if not args.quiet: print('\nDone.')


if __name__ == "__main__":
   main(sys.argv[1:])

sys.exit(0)
