import re

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
        if len(filecontent) == bufferindex:
            return "EOF"
        elif filecontent[bufferindex] == "\n":
            startline = True
            bufferindex += 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])
        bufferindex += 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex[2:]], 16)
        bufferindex += 1
        return ('NUM')
    elif filecontent[bufferindex] in ['-','#', ",", "@"]:
        c = filecontent[bufferindex]
        bufferindex += 1
        return c
    # Complete this function


def error(s):
    global lineno
    print("Line " + str(lineno) + ": " + s)

def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error("Syntax Error")


def parse():
    pass

def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    filecontent = re.split("([\W])", w)
    i = 0
    while True:
        while (filecontent[i] == " ") or(filecontent[i] == '') or (filecontent[i] == "\t"):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != "\n":
        filecontent.append("\n")
    for pass1or2 in range(1,3):
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()


main()