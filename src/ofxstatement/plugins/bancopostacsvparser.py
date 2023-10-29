from typing import Optional, Any, List
from decimal import Decimal
import csv

from ofxstatement.plugins.bancopostapdfparser import DESCRIPTION_TYPE_MAP
from ofxstatement.parser import CsvStatementParser
from ofxstatement.statement import StatementLine, Currency, Statement
from ofxstatement.plugins.bancopostaTransaction import DebitTransaction, CreditTransaction


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
        for key, value in DESCRIPTION_TYPE_MAP.items():
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
        settlementDateString = line[c["Valuta"]].strip()
        if settlementDateString == "" or settlementDateString == "Valuta":
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