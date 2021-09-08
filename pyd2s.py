#!/bin/env python
import os
import bitstring
from math import ceil

# Python d2 save model
class D2Character:
    """docstring for D2Character"""
    def __init__(self, char_name, savedir=None):
        self.CLASSES = ['Amazon', 'Sorceress', 'Necromancer', 'Paladin', 'Barbarian', 'Druid', 'Assassin']
        if savedir is None:
            self.savedir = os.environ['USERPROFILE'] + '\\Saved Games\\Diablo II\\'
        else:
            self.savedir = savedir
        self.savefile = self.savedir + char_name + '.d2s'
        self.data = bytearray(D2Character.load(self.savefile))
        self.adata = D2Character.attribute_data(self.data)
        self.skills_offset, self.attributes = D2Character.get_attributes(self.adata)

    @staticmethod
    def attribute_data(chardata):
        # read starting AFTER known structured data (765 bytes).
        # This should give us a bit array of all bytes starting with the attributes header

        bit_stream = bitstring.BitStream(chardata[765:])
        bit_stream.pos = 0

        # header check (should be 0x67 and 0x66 which is b'gf')
        header = bit_stream.read(16)
        if (header.bytes != b'gf'):
            print("No girlfriend found! Is anyone surprised?")
            return None

        # something is wrong. no one knows why, but this fixes it.
        # reverse the bit representation of every single byte in our data.
        # NO CLUE WHY THIS WORKS.
        fixed_data = '0b'
        for cbyte in bit_stream[bit_stream.pos:].bytes:
            fixed_data += bin(cbyte)[2:].zfill(8)[::-1]
        bit_stream = bitstring.BitStream(fixed_data)
        return bit_stream

    @staticmethod
    def get_attributes(bit_stream):
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
    def load(savefile):
        with open(savefile, 'rb') as f:
            return f.read()

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

