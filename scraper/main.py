# remember, disconnect from vpn
# sudo protonvpn d

from functions import switch_ip, create_long_tail_keywords, create_qa, create_mds, get_simple_answer
import pandas as pd

switch_ip()

# create question and answer
# create_long_tail_keywords()

# create question and answer
for index in range(100):
    create_qa(10)
    switch_ip()

# create markdown pages
# create_mds()
