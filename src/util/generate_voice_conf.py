from enum import Enum
import os
import sys
import json

'''
Configuration (.nana) template generator.
Command format:
    python3 generate_voice_conf.py -template <folder> <output> [languages]+ -replace <language>
Place audio files in the same category in the same directory.
If an audio should be marked as uncategorized, then place it
in the root folder.
Example:
Consider a folder named ./audios/.
If the structure is:
./audios/
├── a-10.mp3
├── cate_1
│   ├── a-1.mp3
│   └── a-2.mp3
├── cate_2
│   ├── a-3.mp3
│   ├── a-4.mp3
│   ├── a-5.mp3
│   └── a-6.mp3
├── cate_3
│   ├── a-7.mp3
│   ├── a-8.mp3
└── └── a-9.mp3

Then a-10.mp3 will be marked as uncategorized and a-1.mp3, a-2.mp3 will be marked as `cate_1`, etc.
In the generated configuration file, you need to replace every occurence of the language marks except the first line to your translation. Once the replacement is done, you can use the next command to generate the json file. 
'''

'''
Configuration (.nana) -> JSON
Command Format:
    python3 generate_voice_conf.py -g <conf(.nana)> <output(.json)>
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
        def map_desc(desc):
            desc_map = {}
            for i in range(len(desc)):
                desc_map[self.locale[i]] = desc[i]
            return desc_map
        if self.state & ACCEPT_END and self.rule[ACCEPT_END](data):
            self.state = DONE
        elif self.state & ACCEPT_END_META and self.rule[ACCEPT_END_META](data):
            assert len(self.store) <= self.locale_cnt + 1
            cat_name, *desc = self.store
            self.tempResult['categoryName'] = cat_name
            self.tempResult['categoryDescription'] = map_desc(desc)
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
            # assert len(self.store) >= self.locale_cnt + 1
            name, *desc = self.store
            self.tempResult['voiceList'].append({
                'name' : name,
                'path' : f'{name}.{self.current_ft}',
                'description': map_desc(desc)
            })
            self.store = []
            self.current_ft = 'mp3'
            self.state = ACCEPT_LANGLE | ACCEPT_END_BODY
        else:
            print(f'Error: no state matched. expected: {list(expected(self.state))} found: {data}')
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
                if data.lower() != 'null':
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
                    f'Error: no state matched. expected: {list(expected(self.state))} found: {data}')
                self.state = ERROR
        assert self.state != ERROR
    
    def parse(self, data):
        data = list(filter(lambda x: len(x) > 0, map(sanitize, data)))
        while self.state != DONE and len(data):
            self.consume(data[0])
            data = data[1:]
        assert self.state == DONE
        assert (not len(data))
        return self.result

def get_replaced(translations, filename, replace=None):
    if replace and replace in translations:
        index = translations.index(replace)
        return translations[:index] + [ filename ] + translations[index + 1:]
    else:
        return translations

def parse_locale(fp):
    line = fp.readline().split(' ')
    assert len(line) != 0
    lang, *locale = line
    assert len(locale) != 0
    return tuple(map(sanitize, locale))

def indent(level):
    assert level >= 0
    return '    ' * level

def write_line(fp, msg, level=0):
    fp.write(indent(level) + msg + '\n')

def write_meta(fp, meta_name, translations, replace=None):
    write_line(fp, 'BeginMeta', level=2)
    write_line(fp, f'{meta_name} {" ".join(get_replaced(translations, meta_name, replace))}', level=3)
    write_line(fp, 'EndMeta', level=2)

def write_body(fp, filename, ftype, translations, replace=None):
    write_line(fp, f'< {filename} {{{ftype}}} {" ".join(get_replaced(translations, filename, replace=replace))} >', level=3)

def generate_template(folder, fp, lang, replace_lang=None):
    assert len(lang) > 0
    write_line(fp, f'#lang {" ".join(lang)}\n')
    write_line(fp, 'Begin')
    it = os.walk(folder)
    r, dirs, files = next(it)
    # Categorized files
    print(dirs)
    for subdir in dirs:
        write_line(fp, 'BeginCategory', level=1)
        write_meta(fp, subdir, lang, replace=replace_lang)
        write_line(fp, 'BeginBody', level=2)
        print(f'Reading {subdir}...')
        cnt = 0
        for subfiles in os.listdir(os.path.join(folder, subdir)):
            if os.path.isfile(os.path.join(folder, subdir, subfiles)) and '.' in subfiles:
                cnt += 1
                name, ftype = subfiles.split('.')
                write_body(fp, name, ftype, lang, replace=replace_lang)
        print(f'{cnt} files loaded.')
        write_line(fp, 'EndBody', level=2)
        write_line(fp, 'EndCategory', level=1)
    write_line(fp, 'BeginCategory', level=1)
    # Uncategorized files
    write_meta(fp, 'uncat', lang)
    write_line(fp, 'BeginBody', level=2)
    for each in files:
        if '.' in each:
            name, ftype = each.split('.')
            write_body(fp, name, ftype, lang)
    write_line(fp, 'EndBody', level=2)
    write_line(fp, 'EndCategory', level=1)
    write_line(fp, 'End')


def main() :
    argv = sys.argv[1:]
    if argv[0] == '-template':
        if len(argv) >= 3:
            with open(argv[2], 'w') as fp:
                print(f'Reading folder {argv[1]}. Generating with languages: {" ".join(argv[3:])}')
                if '-replace' in argv:
                    lang = argv[3:argv.index('-replace')]
                else:
                    lang = argv[3:]
                generate_template(argv[1], fp, lang,
                                  replace_lang=argv[argv.index('-replace') + 1:][-1] if '-replace' in argv else None)
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
            json.dump({
                'voices' : parser.parse(data)
            }, write)
        else:
            raise Exception('Invalid Command')
    else:
        raise Exception('Invalid Command')

main()
