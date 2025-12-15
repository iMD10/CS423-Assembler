import re
from symtable import SymbolTable
import instfile


# String: Mnemonic
# Token: Format number
# Attribute: opcode
class Entry:
    def __init__(self, string, token, attribute, block=0):
        self.string = string
        self.token = token
        self.att = attribute
        self.block = block


symtable = []
inst = 0
objectCode = True
startLoadingAddress = 0
programSize = 0
relocationList = []


# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))

def lookup(s):
    for i in range(0, len(symtable)):
        if s == symtable[i].string:
            return i
    return -1


def insert(string, token, attribute, block=0):
    symtable.append(Entry(string, token, attribute, block))
    return len(symtable) - 1


def init():
    for i in range(0, instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0, instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])


file = open('input.sic', 'r')
fileContent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = [0, 0, 0]  # Blocks [Default, CDATA, CBLCK]
block = 0  # Block index. 1- Default, 2- CDATA, 3- CBLCK
lookahead = ''
startLine = True
baseValue = -1

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000


def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False


def lexan():
    global fileContent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(fileContent) == bufferindex:
            return 'EOF'
        #     # Removed to make immedate work
        # elif fileContent[bufferindex] == '#':
        #     startLine = True
        #     while fileContent[bufferindex] != '\n':
        #         bufferindex = bufferindex + 1
        #     lineno += 1
        #     bufferindex = bufferindex + 1
        elif fileContent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if fileContent[bufferindex].isdigit():
        tokenval = int(fileContent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(fileContent[bufferindex]):
        tokenval = int(fileContent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif fileContent[bufferindex] in ['+', '#', '@', ',']:
        c = fileContent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (fileContent[bufferindex].upper() == 'C') and (fileContent[bufferindex + 1] == '\''):
            bytestring = ''
            bufferindex += 2
            while fileContent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += fileContent[bufferindex]
                bufferindex += 1
                if fileContent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (fileContent[bufferindex] == '\''):  # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while fileContent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += fileContent[bufferindex]
                bufferindex += 1
                if fileContent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (fileContent[bufferindex].upper() == 'X') and (fileContent[bufferindex + 1] == '\''):
            bufferindex += 2
            bytestring = fileContent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue) % 2 == 1:
                bytestringvalue = '0' + bytestringvalue
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue)  # should we deal with literals?
            tokenval = p
        else:
            p = lookup(fileContent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    p = insert(fileContent[bufferindex].upper(), 'ID', locctr[block],
                               block)  # should we deal with case-sensitive?
                else:
                    p = insert(fileContent[bufferindex].upper(), 'ID', -1, -1)  # forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr[block]
                    symtable[p].block = block  # ADDED BY ME, TO FIX INCORRECT BLOCKS FOR FORWARD REFERENCE
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return (symtable[p].token)


def error(s):
    global lineno
    print('line ' + str(lineno) + ': ' + s)


def checkRelAddressRange(PCrelAddress):
    global lineno, baseValue, locctr
    baseRelAddress = symtable[tokenval].att - baseValue
    if 2047 >= PCrelAddress and PCrelAddress >= -2048:
        return 'PC'
    elif baseValue < 0:  # base = -1 by default
        error('Base not initialized')
    elif 4096 >= baseRelAddress and baseRelAddress >= 0:
        return 'BASE'
    else:
        error('Relative addressing out of range (B and P) in line:')
        return None


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')


# def checkindex():
#     global bufferindex, symtable, tokenval
#     if lookahead == ',':
#         match(',')
#         if symtable[tokenval].att != 1:
#             error('index regsiter should be X')
#         match('REG')
#         return True
#     return False

def index(plusPrefix=False):
    global inst
    if lookahead == ',':
        match(',')

        if pass1or2 == 2:  # Adding 1 to the X bit in the instruction
            if plusPrefix:  # Index for +F3 Format
                inst += Xbit4set
            else:  # Index for F3 Format
                inst += Xbit3set
        prevRegIndex = tokenval
        match('REG')
        if (symtable[prevRegIndex].string != 'X') and (pass1or2 == 2):
            error('Index register should be X')


def rest3(prevStmtIndex):
    global inst
    if startLine == False:  # not taking into account the next line IDs
        inst += symtable[tokenval].att
        match('ID')
        index()
    else:
        if symtable[prevStmtIndex].string != 'RSUB':  # only RSUB is allowed to not have an operand
            error('Statement without operand')
        # Otherwise it is epsilon


def rest4():
    global lookahead, pass1or2, inst
    if lookahead == ",":  # , REG
        match(',')
        if pass1or2 == 2:
            inst += symtable[tokenval].att  # REG2 bits
        match('REG')


def rest6(plusPrefix, hashOrAt):  # For # and @
    global lookahead, pass1or2, inst, baseValue

    if lookahead == 'ID':
        if pass1or2 == 2:
            # Relative addressing
            PCRelAddress = symtable[tokenval].att - locctr[block]  # Get the PC rel address
            baseRelAddress = baseValue - locctr[block]  # Get the Base rel address
            PCorBase = checkRelAddressRange(PCRelAddress)
            if PCorBase == 'PC':
                inst += PCRelAddress
                inst += Pbit3set
            elif PCorBase == 'BASE':
                inst += baseRelAddress
                inst += Bbit3set

            # Add NBit and possibly Ebit
            if plusPrefix:  # +F3 format, False if NO PLUS
                inst += Nbitset << 24
                inst += Ebit4set
            else:  # F3 Format
                inst += Nbitset << 16
        match('ID')
    elif lookahead == 'NUM':
        if pass1or2 == 2:
            if hashOrAt == '#':  # Immedate
                inst += tokenval
                if plusPrefix:  # +F3 format, False if NO PLUS
                    inst += Ibitset << 24
                    inst += Ebit4set
                else:  # F3 Format
                    inst += Ibitset << 16
            elif hashOrAt == '@':  # Indirect
                if plusPrefix:  # +F3 format, False if NO PLUS
                    inst += tokenval  # Get the absolute address
                    inst += Nbitset << 24
                    inst += Ebit4set
                else:  # F3 Format
                    # Relative addressing
                    PCRelAddress = symtable[tokenval].att - locctr[block]  # Get the PC rel address
                    baseRelAddress = baseValue - symtable[tokenval].att  # Get the Base rel address
                    PCorBase = checkRelAddressRange(PCRelAddress)
                    if PCorBase == 'PC':
                        inst += PCRelAddress & 0xFFF
                        inst += Pbit3set
                    elif PCorBase == 'BASE':
                        inst += baseRelAddress
                        inst += Bbit3set
                    inst += Nbitset << 16
        match('NUM')


def rest5(prevStmtIndex, plusPrefix=False):  # For F3 and +F3
    global lookahead, pass1or2, inst, startLine

    if lookahead == 'ID':
        if startLine == False:  # not taking into account the next line IDs
            if pass1or2 == 2:
                if plusPrefix:  # +F3 format, False if NO PLUS
                    inst += symtable[tokenval].att  # Absolute addressing
                    inst += Nbitset << 24
                    inst += Ibitset << 24
                    inst += Ebit4set
                else:  # F3 Format
                    PCRelAddress = symtable[tokenval].att - locctr[block]  # Get the PC rel address
                    baseRelAddress = baseValue - symtable[tokenval].att  # Get the Base rel address
                    PCorBase = checkRelAddressRange(PCRelAddress)
                    if PCorBase == 'PC':
                        inst += PCRelAddress & 0xFFF
                        inst += Pbit3set
                    elif PCorBase == 'BASE':
                        inst += baseRelAddress
                        inst += Bbit3set
                    inst += Nbitset << 16
                    inst += Ibitset << 16
            match('ID')
            index(plusPrefix)
        else:
            if symtable[prevStmtIndex].string != 'RSUB':  # only RSUB is allowed to not have an operand
                error('Statement without operand')
    elif lookahead == 'NUM':
        if plusPrefix:  # +F3 format, False if NO PLUS
            inst += tokenval  # Get the absolute address
            inst += Nbitset << 24
            inst += Ebit4set
        else:  # F3 Format
            # Relative addressing
            PCRelAddress = tokenval - locctr[block]  # Get the PC rel address
            baseRelAddress = baseValue - locctr[block]  # Get the Base rel address
            PCorBase = checkRelAddressRange(PCRelAddress)
            if PCorBase == 'PC':
                inst += PCRelAddress
                inst += Pbit3set
            elif PCorBase == 'BASE':
                inst += baseRelAddress
                inst += Bbit3set
            inst += Nbitset << 16
        match('NUM')
    elif lookahead == '#':
        match('#')
        rest6(plusPrefix, '#')
    elif lookahead == '@':
        match('@')
        rest6(plusPrefix, '@')


def stmt():
    global locctr, startLine, inst

    startLine = False  # to know whatever next coming up is on the same line
    prevStmtIndex = tokenval  # store the token for checking for RSUB later

    # FORMATS
    if lookahead == 'f1':
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        locctr[block] += 1
        match('f1')

        if pass1or2 == 2:
            if not objectCode:
                print('0x{:06x}'.format(inst))
            else:
                print('T {:06x} {:02x} {:02x}'.format(locctr[block] - 1, 1, inst))

    elif lookahead == 'f2':
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8  # shift the instruction by 16 bits, to take the instruction from right side to left side to work
        locctr[block] += 2
        match('f2')
        startLine = True
        if pass1or2 == 2:
            inst += symtable[tokenval].att << 4  # REG1 bits
        match('REG')
        rest4()

        if pass1or2 == 2:
            if not objectCode:
                print('0x{:06x}'.format(inst))
            else:
                print('T {:06x} {:02x} {:04x}'.format(locctr[block] - 2, 2, inst))

    elif lookahead == 'f3':
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 16  # shift the instruction by 16 bits, to take the instruction from right side to left side to work
        locctr[block] += 3
        match('f3')
        rest5(prevStmtIndex)

        if pass1or2 == 2:
            if not objectCode:
                print('0x{:06x}'.format(inst))
            else:
                print('T {:06x} {:02x} {:06x}'.format(locctr[block] - 3, 3, inst))

    elif lookahead == '+':  # For "+F3"
        match('+')
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 24  # Take the instruction to the "opcode" part

        if locctr[block] + 1 not in relocationList:  # if the address of the instruction not on the list, then add it to relocation list. we add 1 to skip the instruction (1 byte = 8 bits)
            relocationList.append(locctr[block] + 1)
        locctr[block] += 4
        match('f3')

        rest5(prevStmtIndex, True)

        if pass1or2 == 2:
            if not objectCode:
                print('0x{:06x}'.format(inst))
            else:
                print('T {:06x} {:02x} {:08x}'.format(locctr[block] - 4, 4, inst))


def rest2():
    global locctr, symtable
    if lookahead == 'STRING':
        size = int(len(symtable[
                           tokenval].att) / 2)  # each letter is 8 bits, we need a string hex value, we divide by 2 to make it into half byte for each letter
        locctr[block] += size
        if pass1or2 == 2:
            if objectCode:
                print('T {:06x} {:02x}'.format(locctr[block] - size, size) + ' ' + symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('STRING')

    elif lookahead == 'HEX':
        size = int(len(symtable[tokenval].att) / 2)
        locctr[block] += size
        if pass1or2 == 2:
            if objectCode:
                print('T {:06x} {:02x}'.format(locctr[block] - size, size) + ' ' + symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('HEX')
    else:
        error("wrong byte initialization")


def data():
    global locctr
    if lookahead == 'WORD':
        match('WORD')
        locctr[block] += 3
        if pass1or2 == 2:
            if objectCode:
                print('T {:06x} {:02x} {:06x}'.format(locctr[block] - 3, 3, tokenval))
            else:
                print('0x{:06x}'.format(tokenval))
        match('NUM')

    elif lookahead == 'RESW':
        match('RESW')
        locctr[block] += tokenval * 3
        if (pass1or2 == 2) and not objectCode:
            for i in range(tokenval):
                print("000000")  # This is text only, not hex
        match('NUM')
    elif lookahead == 'RESB':
        match('RESB')
        locctr[block] += tokenval
        if (pass1or2 == 2) and not objectCode:
            for i in range(tokenval):
                print("00")  # This is text only, not hex
        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()
    else:
        error("wrong data declaration")


def header():
    global locctr, symtable, startLoadingAddress, programSize
    tok = tokenval

    match('ID')
    match('START')
    startLoadingAddress = locctr[block] = tokenval
    symtable[tok].att = tokenval
    match('NUM')

    if pass1or2 == 2:
        if objectCode:
            print('H ' + symtable[tok].string + ' {:06x} {:06x}'.format(startLoadingAddress, programSize))


def rest7():
    global block
    if lookahead == 'CDATA':
        block = 1
        match('CDATA')
    elif lookahead == 'CBLCK':
        block = 2
        match('CBLCK')
    else:  # Default
        block = 0


def rest1():
    if lookahead in ['WORD', 'RESW', 'RESB', 'BYTE']:
        data()
        body()
    elif lookahead in ['f1', 'f2', 'f3', '+']:
        stmt()
        body()


def body():
    global baseValue, startLine
    if lookahead == 'ID':  # ID
        match('ID')
        rest1()
    elif lookahead in ['f1', 'f2', 'f3', '+']:  # STMT
        stmt()
        body()
    elif lookahead == "BASE":  # BASE ID BODY
        startLine = False
        match('BASE')
        if pass1or2 == 2:
            baseValue = symtable[tokenval].att
        match('ID')
        body()
    elif lookahead == 'USE':  # BLOCKS
        match('USE')
        rest7()
        body()
    elif lookahead != 'END':
        error('Syntax Error')

    # Left factoring to account for 'rsub'
    # Stop the loop when you find the directive 'END'


def tail():
    global programSize, startLine
    programSize = locctr[block] - startLoadingAddress
    match('END')
    startLine = False
    previousTokenIndex = tokenval
    match('ID')

    if (pass1or2 == 2) and objectCode:
        for i in relocationList:
            print('M {0:06x} 5'.format(i))
        print('E {:06x}'.format(symtable[previousTokenIndex].att))

    # Shifting block addresses
    if pass1or2 == 1:
        sizeDefault = locctr[0]
        sizeCDATA = locctr[1]

        for symbol in symtable:
            if symbol.token == 'ID' and symbol.block == 1:
                symbol.att += sizeDefault
            elif symbol.token == 'ID' and symbol.block == 2:
                symbol.att += sizeDefault + sizeCDATA  # = sizeCBLCK


def parse():
    global lookahead
    lookahead = lexan()
    header()
    body()
    tail()


def main():
    global file, fileContent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    fileContent = re.split(r"([\W])", w)
    i = 0
    while True:
        while (fileContent[i] == ' ') or (fileContent[i] == '') or (fileContent[i] == '\t'):
            del fileContent[i]
            if len(fileContent) == i:
                break
        i += 1
        if len(fileContent) <= i:
            break
    if fileContent[len(fileContent) - 1] != '\n':  # to be sure that the content ends with new line
        fileContent.append('\n')
    for pass1or2 in range(1, 3):
        parse()
        bufferindex = 0
        locctr = [0, 0, 0]
        lineno = 1

    file.close()


main()

