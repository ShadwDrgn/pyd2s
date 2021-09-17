#!/bin/env python
import os
import bitstring
from math import ceil
import numpy as np

def reverse_bytes(bit_stream):
    bit_stream.pos = 0
    newbits = bitstring.BitArray()
    while bit_stream.pos <= len(bit_stream)-1:
        b = bit_stream.read(8)
        b.reverse()
        newbits += b
    return newbits

# Python d2 save model
class D2Character:
    """params (Your character name)"""
    def __init__(self, char_name, savedir=None):
        self.CLASSES = ['Amazon', 'Sorceress', 'Necromancer', 'Paladin', 'Barbarian', 'Druid', 'Assassin']
        if savedir is None:
            self.savedir = os.environ['USERPROFILE'] + '\\Saved Games\\Diablo II\\'
        else:
            self.savedir = savedir
        self.savename = char_name
        self.savefile = self.savedir + char_name + '.d2s'
        self.data = bytearray(D2Character.load(self.savefile))
        self.header = self.data[0:765]
        self.adata = self.attribute_data()
        self.skills_offset, self.attributes = self.get_attributes()
        # truncate the attribute data at the last byte we care about for future writing
        self.adata = self.adata[:(self.skills_offset) * 8]
        sdata_offset = len(self.header) + self.skills_offset
        # Skills data is 32 bytes including a 2 byte header we don't care about
        self.sdata = self.data[sdata_offset+2:sdata_offset+32]
        # FIX THIS. Currently we're just grabbing EVERYTHING after skills, but this is actually items + corpse currently.
        idata_offset = sdata_offset+32
        self.idata = self.data[idata_offset:]
        # TODO: parse shared plugy stash

    def attribute_data(self):
        # read starting AFTER known structured data (765 bytes).
        # This should give us a bit array of all bytes starting with the attributes header

        bit_stream = bitstring.BitStream(self.data[765:])
        bit_stream.pos = 0

        # header check (should be 0x67 and 0x66 which is b'gf')
        header = bit_stream.read(16)
        if (header.bytes != b'gf'):
            print("No girlfriend found! Is anyone surprised?")
            return None

        # something is wrong. no one knows why, but this fixes it.
        # reverse the bit representation of every single byte in our data.
        # NO CLUE WHY THIS WORKS. UPDATE: NOW I KNOW
        fixed_data = '0b'
        for cbyte in bit_stream[bit_stream.pos:].bytes:
            fixed_data += bin(cbyte)[2:].zfill(8)[::-1]
        bit_stream = bitstring.BitStream(fixed_data)
        return bit_stream

    def get_attributes(self, tattr=None):
        bit_stream = self.adata
        bit_stream.pos = 0
        ATTRMAP = [10,10,10,10,10,8,21,21,21,21,21,21,7,32,25,25]
        ATTRNAMEMAP = ['Strength', 'Energy', 'Dexterity', 'Vitality', 'Stat points', 'Skill points', 'Current HP', 'Max HP', 'Current Mana', 'Max Mana', 'Current Stamina', 'Max Stamina', 'Level', 'Experience', 'Gold', 'Stashed Gold']
        attrs = dict(zip(ATTRNAMEMAP, [0] * 16))
        while True:
            # get the first attribute id
            # This seems to output 000000000 (Strength) on both of the charfiles i've tested
            attr1id = bit_stream.read(9)
            attr1id.reverse()

            if attr1id.uint == 511:
                return ceil(bit_stream.pos/8), attrs

            # Debug by telling me what stat we found
            k = ATTRNAMEMAP[attr1id.uint]
            if k == tattr:
                return bit_stream.pos, ATTRMAP[attr1id.uint]

            # get the length in bits of the value for this attribute
            attrlen = ATTRMAP[attr1id.uint]

            # read it
            v = bit_stream.read(attrlen)
            v.reverse()
            v = v.uint
            if attr1id.uint >=6 and attr1id.uint <= 11:
                v = int(v / 256)
            attrs[k] = v

    @staticmethod
    def checksum(data, start_value=0):
        acc = np.int32(start_value)

        for value in data:
            acc = np.int32((acc << 1) + value + (acc<0))

        return np.int32(acc)

    def fix_checksum(self):
        data = self.data
        data[12:16] = b'\0' * 4
        data[12:16] = D2Character.checksum(data).tobytes()
        self.data = data

    @staticmethod
    def load(savefile):
        with open(savefile, 'rb') as f:
            return f.read()

    def set_attr(self, attr_name, val):
        self.get_attributes(attr_name)
        o, bsz = self.get_attributes(attr_name)
        ns = bitstring.BitArray(uint=val, length=bsz)
        ns.reverse()
        self.adata[o:o+bsz] = ns
        self.skills_offset, self.attributes = self.get_attributes()
        self.data[767:767+self.skills_offset] = reverse_bytes(self.adata).tobytes()

    def save(self):
        if self.savename != self.name:
            print(f'*ERROR: Character name does not match filename*\nname: {self.name}\nfilename: {self.savename}\nNOT Saving')
            return
        self.fix_checksum()
        with open(self.savefile, 'wb') as f:
            f.write(self.data)
        print('Saved!')

    @property
    def savename(self):
        return self.savename

    @savename.setter
    def savename(self, val):
        self.savename = val
        self.savefile = self.savedir + char_name + '.d2s'

    @property
    def strength(self):
        return self.attributes['Strength']

    @strength.setter
    def strength(self, val):
        self.set_attr('Strength', val)

    @property
    def energy(self):
        return self.attributes['Energy']

    @energy.setter
    def energy(self, val):
        self.set_attr('Energy', val)

    @property
    def dexterity(self):
        return self.attributes['Dexterity']

    @dexterity.setter
    def dexterity(self, val):
        self.set_attr('Dexterity', val)

    @property
    def vitality(self):
        return self.attributes['Vitality']

    @vitality.setter
    def vitality(self, val):
        self.set_attr('Vitality', val)


    @property
    def name(self):
        return self.data[20:20+16].decode("utf-8").rstrip('\0')

    @name.setter
    def name(self, sName):
        sName = sName[0:16]
        self.data[20:36] = bytearray(sName.ljust(16, '\0'), encoding='ascii')

    @property
    def class_(self):
        return self.CLASSES[self.data[40]]
        
    @class_.setter
    def class_(self, sClass):
        self.data[40] = self.CLASSES.index(sClass)

    @property
    def level(self):
        return self.data[43]
        
    @level.setter
    def level(self, iLevel):
        self.data[43] = iLevel
