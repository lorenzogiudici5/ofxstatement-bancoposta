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
    assert line2.payee == "APP/WEB"
    assert line2.memo == "COMMISSIONE Ricarica Postepay da APP addebito su conto"
    assert line2.trntype == "SRVCHG"

    line3 = statement.lines[3]
    assert line3.amount == Decimal("250.00")
    assert line3.currency.symbol == "EUR"
    assert line3.date == datetime.datetime(2018, 1, 23, 0, 0, 0)
    assert line3.payee == "NOME_MITTENTE"
    assert line3.memo == "CAUSALE_BONIFICO"
    assert line3.trntype == "XFER"

def test_bancoposta_postagiro() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "postagiro.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 2

    line0 = statement.lines[0]
    assert line0.amount == Decimal("200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "Lorenzo Giudici - Pizze"
    assert line0.memo == "Lorenzo Giudici - Pizze"
    assert line0.trntype == "XFER"

    line1 = statement.lines[1]
    assert line1.amount == Decimal("200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "Lorenzo Giudici"
    assert line1.memo == "Lorenzo Giudici"
    assert line1.trntype == "XFER"

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
    assert line0.memo == "PAGAMENTO POSTAMAT"
    assert line0.payee == "RICARICA HYPE BIELLA ITA OPERAZIONE AAAA CARTA 123456"

def test_bancoposta_bonifico() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "bonifico.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 2

    line0 = statement.lines[0]
    assert line0.trntype == "XFER"
    assert line0.amount == Decimal("-200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "Lorenzo Giudici"
    assert line0.memo == "Buon compleanno!"

    line1 = statement.lines[1]
    assert line1.trntype == "XFER"
    assert line1.amount == Decimal("200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "Lorenzo Giudici"
    assert line1.memo == "Tanti Auguri!"

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
    assert line0.payee == "ATM"
    assert line0.memo == "VERSAMENTO IN CONTANTI U.P. 10000 MILANO"

    line1 = statement.lines[1]
    assert line1.trntype == "ATM"
    assert line1.amount == Decimal("-200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "ATM"
    assert line1.memo == "PRELIEVO IN CONTANTI U.P. 10000 MILANO"

def test_bancoposta_addebito_diretto() -> None:
    plugin = BancoPostaPlugin(UI(), {})
    filename = os.path.join(HERE, "samples", "transactions", "addebito_diretto.csv")

    parser = plugin.get_parser(filename)
    statement = parser.parse()

    assert len(statement.lines) == 2

    line0 = statement.lines[0]
    assert line0.trntype == "DIRECTDEBIT"
    assert line0.amount == Decimal("-200.00")
    assert line0.currency.symbol == "EUR"
    assert line0.date == datetime.datetime(2018, 8, 1, 0, 0, 0)
    assert line0.payee == "E ON ENERGIA"
    assert line0.memo == "ADDEBITO PREAUTORIZZATO E ON ENERGIA"

    line1 = statement.lines[1]
    assert line1.trntype == "DIRECTDEBIT"
    assert line1.amount == Decimal("-200.00")
    assert line1.currency.symbol == "EUR"
    assert line1.date == datetime.datetime(2018, 8, 2, 0, 0, 0)
    assert line1.payee == "Postepay S.p."
    assert line1.memo == "ADDEBITO DIRETTO SDD Postepay S.p."
