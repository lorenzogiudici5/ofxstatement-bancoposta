import os
import datetime
from decimal import Decimal

from ofxstatement.plugins.bancoposta import BancoPostaPlugin
from ofxstatement.ui import UI

HERE = os.path.dirname(__file__)

def test_bancoposta_simple() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "bancoposta.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert statement.account_id == "BancoPosta"

    assert len(statement.lines) == 4

    line0 = statement.lines[0]
    assert line0.amount == Decimal("-2.90")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 1, 3, 0, 0, 0)
    assert line0.payee == "IMPOSTA DI BOLLO"
    assert line0.memo == "IMPOSTA DI BOLLO"
    assert line0.trntype == "FEE"

    line1 = statement.lines[1]
    assert line1.amount == Decimal("-250.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 1, 13, 0, 0, 0)
    assert line1.payee == "ADDEBITO PER RICARICA CARTA PREPAGATA DA APP/WEB Ricarica Postepay da APP addebito su conto"
    assert line1.memo == "ADDEBITO PER RICARICA CARTA PREPAGATA DA APP/WEB Ricarica Postepay da APP addebito su conto"
    assert line1.trntype == "DEBIT"

    line2 = statement.lines[2]
    assert line2.amount == Decimal("-1.00")
    assert line2.currency.symbol == "EUR"
    assert line2.date == datetime.datetime(2018, 1, 13, 0, 0, 0)
    assert line2.payee == "COMMISSIONE RICARICA PREPAGATA"
    assert line2.memo == "COMMISSIONE RICARICA PREPAGATA ADDEBITO IN CONTO DA APP/WEB Ricarica Postepay da APP addebito su conto"
    assert line2.trntype == "SRVCHG"

    line3 = statement.lines[3]
    assert line3.amount == Decimal("1250.00")
    assert line3.currency.symbol == "EUR"
    assert line3.date == datetime.datetime(2018, 1, 23, 0, 0, 0)
    assert line3.payee == "NOME_MITTENTE - CAUSALE_BONIFICO"
    assert line3.memo == "BONIFICO A VOSTRO FAVORE TRN BBBBBBBB XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT DA NOME_MITTENTE PER CAUSALE_BONIFICO"
    assert line3.trntype == "XFER"

def test_bancoposta_postagiro() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "postagiro.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 3

    line0 = statement.lines[0]
    assert line0.amount == Decimal("200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "Lorenzo Giudici - Pizze"
    assert line0.memo == "POSTAGIRO TRN BBBBBBBB XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT DA Lorenzo Giudici PER Pizze"
    assert line0.trntype == "XFER"

    line1 = statement.lines[1]
    assert line1.amount == Decimal("200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "PERCASSI Lorenzo"
    assert line1.memo == "POSTAGIRO TRN BBBBBBBB XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT BENEF PERCASSI Lorenzo"
    assert line1.trntype == "XFER"

    line2 = statement.lines[2]
    assert line2.amount == Decimal("200.00")
    assert line2.currency.symbol == "EUR"
    assert line2.date == datetime.datetime(2018, 8, 3, 0, 0, 0)
    assert line2.payee == "POSTAGIRO ONLINE"
    assert line2.memo == "POSTAGIRO ONLINE"
    assert line2.trntype == "XFER"

def test_bancoposta_pagamento_postamat() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "pagamento_postamat.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 1

    line0 = statement.lines[0]
    assert line0.trntype == "PAYMENT"
    assert line0.amount == Decimal("-200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.memo == "PAGAMENTO POSTAMAT ALTRI GESTORI 20/08/2020 10.27 RICARICA HYPE BIELLA ITA OPERAZIONE AAAA CARTA 123456"
    assert line0.payee == "RICARICA HYPE BIELLA ITA"

def test_bancoposta_bonifico() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "bonifico.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 6

    line0 = statement.lines[0]
    assert line0.trntype == "XFER"
    assert line0.amount == Decimal("-100.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "Lorenzo Giudici - Buon compleanno!"
    assert line0.memo == "VOSTRA DISPOS. DI BONIFICO TRN XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT BENEF Lorenzo Giudici PER Buon compleanno!"

    line1 = statement.lines[1]
    assert line1.trntype == "XFER"
    assert line1.amount == Decimal("2000.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "Lorenzo Giudici - Tanti Auguri!"
    assert line1.memo == "BONIFICO A VOSTRO FAVORE TRN BBBBBBBB XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT DA Lorenzo Giudici PER Tanti Auguri!"

    line2 = statement.lines[2]
    assert line2.trntype == "XFER"
    assert line2.amount == Decimal("100.55")
    assert line2.currency.symbol == "EUR"
    assert line2.date == datetime.datetime(2018, 8, 3, 0, 0, 0)
    assert line2.payee == "Lorenzo Giudici - Buon Natale"
    assert line2.memo == "BONIFICO TRN BBBBBBBB XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT DA Lorenzo Giudici PER Buon Natale"

    line3 = statement.lines[3]
    assert line3.trntype == "XFER"
    assert line3.amount == Decimal("-100.55")
    assert line3.currency.symbol == "EUR"
    assert line3.date == datetime.datetime(2018, 8, 4, 0, 0, 0)
    assert line3.payee == "Lorenzo Giudici - Buon Natale"
    assert line3.memo == "BONIFICO TRN XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT BENEF Lorenzo Giudici PER Buon Natale"

    line4 = statement.lines[4]
    assert line4.trntype == "XFER"
    assert line4.amount == Decimal("500.50")
    assert line4.currency.symbol == "EUR"
    assert line4.date == datetime.datetime(2018, 8, 5, 0, 0, 0)
    assert line4.payee == "Lorenzo Giudici - Buona Cresima"
    assert line4.memo == "BONIFICO INSTANT IN ENTRATA TRN XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT DA Lorenzo Giudici PER Buona Cresima"

    line5 = statement.lines[5]
    assert line5.trntype == "XFER"
    assert line5.amount == Decimal("-500.50")
    assert line5.currency.symbol == "EUR"
    assert line5.date == datetime.datetime(2018, 8, 5, 0, 0, 0)
    assert line5.payee == "PERCASSI Lorenzo - Felicitazioni"
    assert line5.memo == "BONIFICO INSTANT IN USCITA TRN AAAAAXXX XXXXXXXXXXXXXXX BENEF PERCASSI Lorenzo PER Felicitazioni"


def test_bancoposta_atm() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "atm.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 2

    line0 = statement.lines[0]
    assert line0.trntype == "ATM"
    assert line0.amount == Decimal("200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "VERSAMENTO"
    assert line0.memo == "VERSAMENTO IN CONTANTI U.P. 10000 MILANO"

    line1 = statement.lines[1]
    assert line1.trntype == "ATM"
    assert line1.amount == Decimal("-200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "PRELIEVO"
    assert line1.memo == "PRELIEVO POSTAMAT NOSTRO SPORTELLO AUTOMATICO 24/11/2020 08.21 ATM N. XXX UFFICIO POSTALE ROMA CARTA 11111"

def test_bancoposta_addebito_diretto() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "addebito_diretto.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 3

    line0 = statement.lines[0]
    assert line0.trntype == "DIRECTDEBIT"
    assert line0.amount == Decimal("-200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "E ON ENERGIA"
    assert line0.memo == "ADDEBITO PREAUTORIZZATO E ON ENERGIA CID.XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT 100820 MAN. X"

    line1 = statement.lines[1]
    assert line1.trntype == "DIRECTDEBIT"
    assert line1.amount == Decimal("-200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "Postepay S.p."
    assert line1.memo == "ADDEBITO DIRETTO SDD Postepay S.p. CID. XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT 020623 MAN. XX"

    line2 = statement.lines[2]
    assert line2.trntype == "DIRECTDEBIT"
    assert line2.amount == Decimal("-0.40")
    assert line2.currency.symbol == "EUR"
    assert line2.date == datetime.datetime(2018, 8, 3, 0, 0, 0)
    assert line2.payee == "REGIONE LOMBA"
    assert line2.memo == "ADDEBITO DIRETTO SDD** REGIONE LOMBA CID. XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT 020623 MAN. XX"

def test_bancoposta_commissione() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "commissione.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 3

    line0 = statement.lines[0]
    assert line0.amount == Decimal("-1.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "COMMISSIONE BONIFICO INSTANT"
    assert line0.memo == "COMMISSIONE BONIFICO INSTANT IN USCITA TRN CCCCCCCCCCC BENEF Lorenzo Giudici PER Ricarica"
    assert line0.trntype == "SRVCHG"

    line1 = statement.lines[1]
    assert line1.amount == Decimal("-2.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "COMMISSIONE SDD"
    assert line1.memo == "COMMISSIONE SDD REGIONE ITALIA CID.XXXXXXXXXXXXXXXXXXXXXXXXXXXXIT 000000 MAN. 10000000000000000XXXXXXX"
    assert line1.trntype == "SRVCHG"

    line2 = statement.lines[2]
    assert line2.amount == Decimal("-1.00")
    assert line2.currency.symbol == "EUR"
    assert line2.date == datetime.datetime(2018, 8, 3, 0, 0, 0)
    assert line2.payee == "COMMISSIONE RICARICA PREPAGATA"
    assert line2.memo == "COMMISSIONE RICARICA PREPAGATA ADDEBITO IN CONTO DA APP/WEB Ricarica Postepay da APP addebito su conto"
    assert line2.trntype == "SRVCHG"