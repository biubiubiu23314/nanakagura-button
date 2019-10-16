#!/bin/bash

echo "Testing template generation"
python3 ../../src/util/generate_voice_conf.py -template . ./config_test.nana zh-CN ja-JP en-US
python3 ../../src/util/generate_voice_conf.py -g ./config_test.nana ./config_test.json