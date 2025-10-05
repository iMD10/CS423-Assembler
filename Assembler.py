

import instfile


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute

symtable = []

def lookup(s):
    for sym in range(0,symtable.__len__()):
        if s == symtable[sym].string:
            return sym
        return -1

def insert(s,t,a):
    symtable.append(Entry(s,t,a))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i],instfile.token[i],instfile.opcode[i])
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i],instfile.dirtoken[i],instfile.dircode[i])
    for i in range(0,instfile.dir_ex.__len__()):
        insert(instfile.dir_ex[i],instfile.dir_token_ex[i],instfile.dir_ex_code[i])
    for i in range(0,instfile.inst_ex.__len__()):
        insert(instfile.inst_ex[i],instfile.inst_token_ex[i],instfile.inst_ex_opcode[i])

file = open('input.sic','r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startline = True

Xbit4set = 0X800000
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
    if s[0:2].upper() == "0X":
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def lexan():
    global filecontent,lineno,lookahead,tokenval,bufferindex,locctr,startline

    while True:

