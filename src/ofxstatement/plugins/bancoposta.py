# from hashlib import md5
from typing import Optional, Any, List
from decimal import Decimal
import re

from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.statement import StatementLine, Currency, Statement, generate_transaction_id

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


TRANSACTION_TYPES = {
    "BONIFICO A VOSTRO FAVORE": "XFER",
    "VOSTRA DISPOS. DI BONIFICO": "XFER",
    "POSTAGIRO" : "XFER",
    "IMPOSTA DI BOLLO": "FEE",
    "COMMISSIONE RICARICA PREPAGATA": "SRVCHG",
    "PAGAMENTO POSTAMAT": "PAYMENT",
    "ATM": "ATM",
    "ADDEBITO DIRETTO SDD": "DIRECTDEBIT",
    "ADDEBITO PREAUTORIZZATO": "DIRECTDEBIT"
}

class BancoPostaCSVStatementParser(CsvStatementParser):
    __slots__ = 'columns'

    date_format = "%d/%m/%y"

    def parse_currency(self, value: Optional[str], field: str) -> Currency:
        return Currency(symbol=value)

    def parse_description(self, text: str):
        if (text.find("BONIFICO A VOSTRO FAVORE") == 0 or text.find("VOSTRA DISPOS. DI BONIFICO") == 0):
            return self.extract_bonifico_info(text)

        if (text.find("ADDEBITO DIRETTO SDD") == 0 or text.find("ADDEBITO PREAUTORIZZATO") == 0):
            return self.extract_addebito_info(text)
        
        if (text.find("POSTAGIRO") == 0):
            return self.extract_postagiro_info(text)

        if (text.find("PAGAMENTO POSTAMAT") == 0):
            return self.extract_pagamento_postamat_info(text)
        
        if (text.find("IMPOSTA DI BOLLO") == 0):
            return text, text, text       

        if (text.find("VERSAMENTO") == 0 or text.find("PRELIEVO") == 0):
            return "ATM", "ATM", text   

        if (text.find("COMMISSIONE RICARICA PREPAGATA") == 0):
            return self.extract_ricarica_prepagata_info(text)
        
        if (text.find("COMMISSIONE SDD") == 0):
            return self.extract_ricarica_prepagata_info(text)

        return None, text, text
    
    def extract_ricarica_prepagata_info(self, text: str):
        type_end_index = text.find("ADDEBITO")
        if type_end_index == -1:
            return None, text, text
        trntype = text[:type_end_index].strip()
        
        payee_start_index = text.find("DA") + len("DA")
        payee_end_index = text.find("Ricarica")
        if payee_end_index == -1:
            return None, text, text
        payee = text[payee_start_index:payee_end_index].strip()
        
        memo_start_index = payee_end_index
        memo = "COMMISSIONE " + text[memo_start_index:].strip()
        
        return trntype, payee, memo

    def extract_bonifico_info(self, text: str):
        type_end_index = text.find("TRN")
        if type_end_index == -1:
            return None, text, text
        trntype = text[:type_end_index].strip()
        
        payee_start_index = text.find("DA")
        if payee_start_index == -1:
            payee_start_index = text.find("BENEF")
            if payee_start_index == -1:
                return None, text, text
            payee_start_index += len("BENEF")
        else:
            payee_start_index += len("DA")

        payee_end_index = text.find("PER")
        if payee_end_index == -1:
            return None, text, text
        payee = text[payee_start_index:payee_end_index].strip()
        
        memo_start_index = payee_end_index + len("PER")
        memo = text[memo_start_index:].strip()
        
        return trntype, payee, memo
    
    def extract_postagiro_info(self, text: str):
        trntype = "POSTAGIRO"
        
        # payee_start_index = text.find("DA")
        # if payee_start_index == -1:
        #     payee_start_index = text.find("BENEF")
        #     if payee_start_index == -1:
        #         return None, text, text
        #     payee_start_index += len("BENEF")
        # else:
        #     payee_start_index += len("DA")
        
        # payee_end_index = text.find("PER")
        # if payee_end_index == -1:
        #     payee = text[payee_start_index:].strip()
        #     memo = ""
        # else:
        #     payee = text[payee_start_index:payee_end_index].strip()
        #     memo_start_index = payee_end_index + len("PER")
        #     memo = text[memo_start_index:].strip()

        if " DA " in text:
            payee = text.split(" DA ")[1]
        elif " BENEF " in text:
            payee = text.split(" BENEF ")[1]
        else:
            payee = ""
        memo = payee
        
        return trntype, payee, memo

    def extract_pagamento_postamat_info(self, text):
        trntype = "PAGAMENTO POSTAMAT"
        memo = "PAGAMENTO POSTAMAT"
        
        date_time_pattern = r"\d{2}/\d{2}/\d{4} \d{2}\.\d{2}"
        match = re.search(date_time_pattern, text)
        if match:
            payee_start_index = match.end()
            payee = text[payee_start_index:].strip()
        else:
            payee = text
        
        return trntype, payee, memo
    
    def extract_addebito_info(self, text):
        if "ADDEBITO PREAUTORIZZATO" in text:
            trntype = "ADDEBITO PREAUTORIZZATO"
        elif "ADDEBITO DIRETTO SDD" in text:
            trntype = "ADDEBITO DIRETTO SDD"
        else:
            trntype = None
        
        if trntype is None:
            return None, text, text
        
        payee_start_index = text.find(trntype) + len(trntype)
        payee_end_index = text.find("CID")
        payee = text[payee_start_index:payee_end_index].strip()
        
        memo = trntype + " " + payee
        
        return trntype, payee, memo

    def parse_value(self, value: Optional[str], field: str) -> Any:
        value = value.strip() if value else value
        if field == "amount" and isinstance(value, float):
            return Decimal(value)

        # if field == "trntype":
            # Default: Debit card payment
            # return TRANSACTION_TYPES.get(value, "POS")
        if field == "currency":
            return self.parse_currency(value, field)

        return super().parse_value(value, field)

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        # Ignore the header
        if self.cur_record <= 1:
            return None

        c = self.columns

        # Ignore Saldo iniziale/finale
        if line[c["Valuta"]].strip() == "":
            return None

        # stmt_line = super().parse_record(line)

        stmt_line = StatementLine()        

        # date field
        stmt_line.date = self.parse_value(line[c["Valuta"]], "date")

        # amount field
        if line[c["Accrediti"]]:
            income = Decimal(line[c["Accrediti"]])
            outcome = 0
        elif line[c["Addebiti"]]:
            outcome = Decimal(line[c["Addebiti"]])
            income = 0
        stmt_line.amount = income - outcome
        
        trntype, payee, memo = self.parse_description(line[c["Descrizione operazioni"]])

        # transaction type field
        if trntype is None:
            if(stmt_line.amount < 0):
                stmt_line.trntype = "DEBIT"
            else:
                stmt_line.trntype = "CREDIT"
        else:
            stmt_line.trntype = TRANSACTION_TYPES.get(trntype)

        stmt_line.payee = payee
        stmt_line.memo = memo

        stmt_line.currency = self.parse_value("EUR", "currency")

        # id field
        stmt_line.id = generate_transaction_id(stmt_line)

        # Generate a unique ID
        # stmt_line.id = md5(f"{stmt_line.date}-{stmt_line.payee}-{stmt_line.amount}".encode())\
        #     .hexdigest()

        return stmt_line

    # noinspection PyUnresolvedReferences
    def parse(self) -> Statement:
        statement = super().parse()

        # # Generate fee transactions, if any fees exist
        # for stmt_line in statement.lines:
        #     if not hasattr(stmt_line, "fee"):
        #         continue

        #     fee = self.parse_decimal(stmt_line.fee)
        #     if fee:
        #         fee_line = StatementLine()
        #         fee_line.amount = -fee
        #         fee_line.currency = stmt_line.currency
        #         fee_line.date = stmt_line.date
        #         fee_line.id = f"{stmt_line.id}-feex"
        #         fee_line.payee = "BancoPosta"
        #         fee_line.trntype = "FEE"
        #         fee_line.memo = f"BancoPosta fee for {stmt_line.payee}, {stmt_line.currency.symbol} {stmt_line.amount}"

        #         statement.lines.append(fee_line)

        return statement

class BancoPostaPlugin(Plugin):
    """BancoPosta plugin (for developers only)"""

    def get_parser(self, filename: str) -> BancoPostaCSVStatementParser:
        f = open(filename, "r", encoding='utf-8')
        signature = f.readline()

        csv_columns = [col.strip() for col in signature.split(",")]
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