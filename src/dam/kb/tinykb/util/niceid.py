#!/usr/bin/env python
#########################################################################
#
# NotreDAM, Copyright (C) 2011, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################

import random
import string
import unicodedata

random.seed()
VALID_CHARS = string.ascii_lowercase + string.digits

def generate(length=8):
    id_ = ''
    i = 0
    while i < length:
        id_ += VALID_CHARS[random.randint(0, len(VALID_CHARS) - 1)]
        i += 1
    return id_

def generate_unique(used_ids, length=8):
    '''
    Return an ID that is not in our list of already used IDs.
    '''
    # trying infinitely is a bad idea
    LIMIT = 1000

    count = 0
    while count < LIMIT:
        id = generate(length)
        if id not in used_ids:
            break
        count += 1
        id = ''
    return id


def niceid(base, extra_chars=8):
    '''
    Create a nice ID based on the given string, eventually adding
    extra random characters
    '''
    # Convert Unicode into string, strip forbidden chars, replace spaces
    if isinstance(base, unicode):
        base = unicodedata.normalize('NFKD', base).encode('ascii',
                                                          'ignore')
    safe_base = string.translate(base, None, deletions)
    safe_base = safe_base.replace(' ', '_').lower()

    if (0 == extra_chars):
        return safe_base
    else:
        return safe_base + '_' + generate(extra_chars)


if __name__ == '__main__':
    from sets import Set

    print 'Some sample unique IDs:'
    used_ids = Set()
    for i in xrange(50):
        id = generate_unique(used_ids)
        if not id:
            print 'Something broke'
            break
        used_ids.add(id)
        print id
