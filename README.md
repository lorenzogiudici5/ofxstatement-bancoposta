# ofxstatement-bancoposta

![badge](https://github.com/lorenzogiudici5/ofxstatement-bancoposta/actions/workflows/build-and-publish.yml/badge.svg)

This is a plugin for [ofxstatement](https://github.com/kedder/ofxstatement).

Bancoposta bank statement is available in PDF format only. This plugin converts PDF statement to OFX format, suitable for importing into GnuCash.
In case you used to parse PDF statement yourself in a CSV format, this plugin contains a CSV parser as well.

## Installation

### From PyPI repositories
```
pip3 install ofxstatement-bancoposta
```

### From source
```
git clone https://github.com/lorenzogiudici5/ofxstatement-bancoposta.git
python3 setup.py install
```

## Usage
Download your statement pdf file from Poste web site and then run
```bash
$ ofxstatement convert -t bancoposta EC_2023_10.pdf EC_2023_10.ofx
```