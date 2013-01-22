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
        id_ = generate(length)
        if id_ not in used_ids:
            break
        count += 1

    if count == LIMIT:
        raise RuntimeError('Unable to generate new unique ID after %d trials'
                           % (LIMIT, ))
    return id_


_valid_chars = ' _-' + string.digits + string.ascii_letters
_all_chars = string.maketrans('', '')
DELETIONS = ''.join(set(_all_chars) - set(_valid_chars))

def niceid(base, extra_chars=8):
    '''
    Create a nice ID based on the given string, eventually adding
    extra random characters
    '''
    # Convert Unicode into string, strip forbidden chars, replace spaces
    if isinstance(base, unicode):
        base = unicodedata.normalize('NFKD', base).encode('ascii',
                                                          'ignore')
    safe_base = string.translate(base, None, DELETIONS)
    safe_base = safe_base.replace(' ', '_').lower()
    safe_base = safe_base.replace('-', '_')

    # Remove all pairs of underscores until the string is "normalized"
    normalized = False
    old_safe_base = safe_base
    while not normalized:
        safe_base = safe_base.replace('__', '_')
        normalized = (old_safe_base == safe_base)
        old_safe_base = safe_base

    if (0 == extra_chars):
        return safe_base
    else:
        return safe_base + '_' + generate(extra_chars)


if __name__ == '__main__':
    from sets import Set

    print '*** Some sample unique IDs:'
    used_ids = Set()
    for i in xrange(50):
        id_ = generate_unique(used_ids)
        used_ids.add(id)
        print id_

    base = u'A Nasty & StrING    \xda\xd0Fk\xfb'
    print '*** Some sample IDs with base "%s":' % (base, )
    for i in xrange(50):
        id_ = niceid(base)
        print id_
