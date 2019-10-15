from enum import Enum
import os
import sys

'''
Config format:
CONFIG ::= #lang [locale]+ \n Begin BODY* End
BODY   ::=  BeginCategory
                BeginMeta 
                    CATEGORY DESCRIPTION+
                EndMeta
                BeginBody
                    < LINES >+
                EndBody
            EndCategory
LINE   ::= filename {format=mp3} (I18N)+
I18N   ::= locale translation
'''

ERROR               = 0
ACCEPT_BEGIN        = 1
ACCEPT_END          = 1 << 1
ACCEPT_BEGIN_META   = 1 << 2
ACCEPT_STR          = 1 << 3
ACCEPT_END_META     = 1 << 4
ACCEPT_BEGIN_BODY   = 1 << 5
ACCEPT_FILE_TYPE    = 1 << 6
ACCEPT_END_BODY     = 1 << 7
ACCEPT_BEGIN_CATE   = 1 << 8
ACCEPT_END_CATE     = 1 << 9
ACCEPT_LANGLE       = 1 << 10
ACCEPT_RANGLE       = 1 << 11
DONE                = 1 << 12

def translate(state):
    return {
        ERROR : 'ERROR',
        ACCEPT_BEGIN : 'Begin',
        ACCEPT_END   : 'End',
        ACCEPT_BEGIN_META : 'BeginMeta',
        ACCEPT_STR : 'String',
        ACCEPT_END_META : 'EndMeta',
        ACCEPT_BEGIN_BODY : 'BeginBody',
        ACCEPT_FILE_TYPE  : 'FileType',
        ACCEPT_END_BODY   : 'EndBody',
        ACCEPT_BEGIN_CATE : 'BeginCategory',
        ACCEPT_END_CATE   : 'EndCategory',
        ACCEPT_LANGLE     : '<',
        ACCEPT_RANGLE     : '>',
        DONE              : 'DONE'
    }.get(state, 'Unknown State')

def expected(state):
    i = 1 << 11
    while i:
        if i & state:
            yield translate(i)
        i >>= 1

escape = ('', ' ', '\t', '\r', '\a', '\n')


def sanitize(data: str) -> str:
        return ''.join(map(lambda x: x if x not in escape else '', data))

class Parser:
    def __init__(self, locale_conf, *args, **kwargs):
        self.locale = locale_conf
        self.locale_cnt = len(locale_conf)
        self.state = ACCEPT_BEGIN
        self.result = []
        self.tempResult = {}
        self.store      = []
        self.current_ft = 'mp3'
        self.rule = {
            ACCEPT_BEGIN      : lambda x: x == 'Begin',
            ACCEPT_END        : lambda x: x == 'End',
            ACCEPT_BEGIN_META : lambda x: x == 'BeginMeta',
            ACCEPT_STR        : lambda x: type(x) == str,
            ACCEPT_END_META   : lambda x: x == 'EndMeta',
            ACCEPT_BEGIN_BODY : lambda x: x == 'BeginBody',
            ACCEPT_FILE_TYPE  : lambda x: x.startswith('{') and x.endswith('}'),
            ACCEPT_END_BODY   : lambda x: x == 'EndBody',
            ACCEPT_BEGIN_CATE : lambda x: x == 'BeginCategory',
            ACCEPT_END_CATE   : lambda x: x == 'EndCategory',
            ACCEPT_LANGLE     : lambda x: x == '<',
            ACCEPT_RANGLE     : lambda x: x == '>',
        }
    
    def emit(self, data):
        # print('Ending State', bin(self.state))
        if self.state & ACCEPT_END and self.rule[ACCEPT_END](data):
            self.state = DONE
        elif self.state & ACCEPT_END_META and self.rule[ACCEPT_END_META](data):
            assert len(self.store) == self.locale_cnt + 1
            # print('Store:', self.store)
            cat_name, *desc = self.store
            self.tempResult['categoryName'] = cat_name
            self.tempResult['categoryDescription'] = dict(zip(self.locale, desc))
            self.tempResult['voiceList'] = []
            self.store = []
            self.state = ACCEPT_BEGIN_BODY
        elif self.state & ACCEPT_END_BODY and self.rule[ACCEPT_END_BODY](data):
            self.state = ACCEPT_END_CATE
        elif self.state & ACCEPT_END_CATE and self.rule[ACCEPT_END_CATE](data):
            self.result.append(self.tempResult.copy())
            self.tempResult = {}
            self.state = ACCEPT_END | ACCEPT_BEGIN_CATE
        elif self.state & ACCEPT_RANGLE and self.rule[ACCEPT_RANGLE](data):
            assert len(self.store) >= self.locale_cnt + 1
            name, *desc = self.store
            self.tempResult['voiceList'].append({
                'name' : name,
                'path' : f'{name}.{self.current_ft}',
                'description': dict(zip(self.locale, desc))
            })
            self.store = []
            self.current_ft = 'mp3'
            self.state = ACCEPT_LANGLE | ACCEPT_END_BODY
        else:
            print(f'Error: no state matched. expected: {list(expected(self.state))}')
            self.state = ERROR
        return self.state

    def match_rule(self, data):
        i = 1 << 11
        while i:
            if self.state & i and self.rule[i](data):
                return i
            i >>= 1
        return 0

    def consume(self, data):
        # print(data, bin(self.state))
        if (data.startswith('End') or data == '>'):
            assert self.emit(data) != ERROR
        else:
            matched_state = self.match_rule(data)
            assert matched_state != ERROR
            if matched_state == ACCEPT_BEGIN:
                self.state = ACCEPT_END | ACCEPT_BEGIN_CATE
            elif matched_state == ACCEPT_BEGIN_CATE:
                self.state = ACCEPT_BEGIN_META
            elif matched_state == ACCEPT_BEGIN_META:
                self.state = ACCEPT_STR | ACCEPT_END_META
            elif matched_state == ACCEPT_STR:
                self.store.append(data)
            elif matched_state == ACCEPT_BEGIN_BODY:
                self.state = ACCEPT_LANGLE
            elif matched_state == ACCEPT_LANGLE:
                self.state = ACCEPT_STR | ACCEPT_FILE_TYPE | ACCEPT_RANGLE
            elif matched_state == ACCEPT_FILE_TYPE:
                self.current_ft = data.replace('{', '').replace('}', '')
                self.state = ACCEPT_STR | ACCEPT_RANGLE
            else:
                print(
                    f'Error: no state matched. expected: {list(expected(self.state))}')
                self.state = ERROR
        assert self.state != ERROR
    
    def parse(self, data):
        data = list(filter(lambda x: len(x) > 0, map(sanitize, data)))
        # print(data)
        while self.state != DONE and len(data):
            self.consume(data[0])
            data = data[1:]
        # print(self.locale)
        print(self.result)
        assert self.state == DONE
        assert (not len(data))
        return self.result

def parse_locale(fp):
    line = fp.readline().split(' ')
    assert len(line) != 0
    lang, *locale = line
    assert len(locale) != 0
    return tuple(map(sanitize, locale))

def main() :
    argv = sys.argv[1:]
    if argv[0] == '-template':
        if len(argv) >= 2:
            print(f'Reading folder {argv[1]}')
        else:
            raise Exception('Invalid Command')
    elif argv[0] == '-g':
        if len(argv) >= 3:
            conf_file = open(argv[1], 'r')
            write     = open(argv[2], 'w')
            locale    = parse_locale(conf_file)
            parser = Parser(locale)
            conf_file = conf_file.readlines()
            data = []
            for each in conf_file:
                data += each.split(' ')
            print(parser.parse(data))
        else:
            raise Exception('Invalid Command')
    else:
        raise Exception('Invalid Command')

main()
