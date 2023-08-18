# from hashlib import md5
from typing import Optional, Any, List, Iterable
from decimal import Decimal
import re
import csv

from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.statement import StatementLine, Currency, Statement, generate_transaction_id
from ofxstatement.plugins.bancopostaTransaction import BonificoTransaction, DebitTransaction, CreditTransaction, PostagiroTransaction, PagamentoPostamatTransaction, CommissioneTransaction, BolloTransaction, AddebitoDirettoTransaction, AddebitoPreautorizzatoTransaction, ATMTransaction

# Possible values for the trntype property of a StatementLine object:
# - CREDIT: Generic credit.
# - DEBIT: Generic debit.
# - INT: Interest earned or paid (Note: Depends on signage of amount).
# - DIV: Dividend.
# - FEE: FI fee.
# - SRVCHG: Service charge.
# - DEP: Deposit.
# - ATM: ATM debit or credit (Note: Depends on signage of amount).
# - POS: Point of sale debit or credit (Note: Depends on signage of amount).
# - XFER: Transfer.
# - CHECK: Check.
# - PAYMENT: Electronic payment.
# - CASH: Cash withdrawal.
# - DIRECTDEP: Direct deposit.
# - DIRECTDEBIT: Merchant initiated debit.
# - REPEATPMT: Repeating payment/standing order.
# - OTHER: Other.


# TRANSACTION_TYPES = {
#     "BONIFICO A VOSTRO FAVORE": "XFER",
#     "VOSTRA DISPOS. DI BONIFICO": "XFER",
#     "POSTAGIRO" : "XFER",
#     "IMPOSTA DI BOLLO": "FEE",
#     "COMMISSIONE RICARICA PREPAGATA": "SRVCHG",
#     "PAGAMENTO POSTAMAT": "PAYMENT",
#     "ATM": "ATM",
#     "ADDEBITO DIRETTO SDD": "DIRECTDEBIT",
#     "ADDEBITO PREAUTORIZZATO": "DIRECTDEBIT"
# }

class BancoPostaCSVStatementParser(CsvStatementParser):
    __slots__ = 'columns'

    date_format = "%d/%m/%y"

    def parse_currency(self, value: Optional[str], field: str) -> Currency:
        return Currency(symbol=value)

    def parse_amount(self, value: [Optional[str]]) -> Decimal:
        return Decimal(value.replace(" ", "").replace(".", "").replace(",", "."))

    def parse_value(self, value: Optional[str], field: str) -> Any:
        value = value.strip() if value else value
        # if field == "amount" and isinstance(value, float):
        #     return Decimal(value)

        # if field == "trntype":
            # Default: Debit card payment
            # return TRANSACTION_TYPES.get(value, "POS")
        if field == "currency":
            return self.parse_currency(value, field)

        return super().parse_value(value, field)
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=';')
    
    def create_transaction(self, text, date, settlement_date, amount, currency):
        transaction_type_map = {
            "BONIFICO A VOSTRO FAVORE": BonificoTransaction,
            "VOSTRA DISPOS. DI BONIFICO": BonificoTransaction,
            "POSTAGIRO": PostagiroTransaction,
            "IMPOSTA DI BOLLO": BolloTransaction,
            "COMMISSIONE": CommissioneTransaction,
            "PAGAMENTO POSTAMAT": PagamentoPostamatTransaction,
            "VERSAMENTO": ATMTransaction,
            "PRELIEVO": ATMTransaction,
            "ADDEBITO DIRETTO": AddebitoDirettoTransaction,
            "ADDEBITO PREAUTORIZZATO": AddebitoPreautorizzatoTransaction
        }
        for key, value in transaction_type_map.items():
            if text.startswith(key):
                return value(date, settlement_date, amount, text, currency)
        
        if amount > 0:
            return CreditTransaction(date, settlement_date, amount, text, currency)
        else:
            return DebitTransaction(date, settlement_date, amount, text, currency)

        return None

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        # Ignore the header
        if self.cur_record <= 1:
            return None

        c = self.columns

        # Ignore Saldo iniziale/finale
        if line[c["Valuta"]].strip() == "":
            return None

        date = self.parse_value(line[c["Data"]], "date")
        settlementDate = self.parse_value(line[c["Valuta"]], "date")

        if line[c["Accrediti"]]:
            income = self.parse_amount(line[c["Accrediti"]])
            outcome = 0
        elif line[c["Addebiti"]]:
            outcome = self.parse_amount(line[c["Addebiti"]])
            income = 0
        amount = income - outcome
        currency = self.parse_value("EUR", "currency")

        description = line[c["Descrizione operazioni"]]
        
        transaction = self.create_transaction(description, date, settlementDate, amount, currency)
        stmt_line = transaction.to_statement_line()

        stmt_line.currency = self.parse_value("EUR", "currency")

        return stmt_line

    # noinspection PyUnresolvedReferences
    def parse(self) -> Statement:
        statement = super().parse()
        return statement

class BancoPostaPlugin(Plugin):
    """BancoPosta plugin (for developers only)"""

    def get_parser(self, filename: str) -> BancoPostaCSVStatementParser:
        f = open(filename, "r", encoding='utf-8')
        signature = f.readline()

        csv_columns = [col.strip() for col in signature.split(";")]
        required_columns = [
            "Data",
            "Valuta",
            "Addebiti",
            "Accrediti",
            "Descrizione operazioni",
        ]

        if set(required_columns).issubset(csv_columns):
            f.seek(0)
            parser = BancoPostaCSVStatementParser(f)
            parser.columns = {col: csv_columns.index(col) for col in csv_columns}
            if 'account' in self.settings:
                parser.statement.account_id = self.settings['account']
            else:
                parser.statement.account_id = 'BancoPosta'

            if 'currency' in self.settings:
                parser.statement.currency = self.settings.get('currency', 'EUR')

            if 'date_format' in self.settings:
                parser.date_format = self.settings['date_format']
            
            parser.statement.bank_id = self.settings.get('bank', 'BancoPosta')
            return parser

        # no plugin with matching signature was found
        raise Exception("No suitable BancoPosta parser "
                        "found for this statement file.")