# from hashlib import md5
from ast import Dict
from math import nan
from typing import Optional, Any, List
from decimal import Decimal
import csv
import pandas
from pandas import DataFrame
import tabula


from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import StatementLine, Currency, Statement
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

class BancoPostaPdfStatementParser(StatementParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
    
    date_format = "%d/%m/%y"

    def parse_currency(self, value: Optional[str]) -> Currency:
        return Currency(symbol=value)

    def parse_amount(self, value: [Optional[str]]) -> Decimal:
        return Decimal(value.replace(" ", "").replace(".", "").replace(",", "."))

    def parse_value(self, value: Optional[str], field: str) -> Any:
        value = value.strip() if value else value
        print(value)
        # if field == "amount" and isinstance(value, float):
        #     return Decimal(value)

        # if field == "trntype":
            # Default: Debit card payment
            # return TRANSACTION_TYPES.get(value, "POS")
        if field == "currency":
            return self.parse_currency(value, field)

        return super().parse_value(value, field)
    
    def split_records(self) -> List[Dict]:
        # return csv.reader(self.fin, delimiter=';')
        dataFrame = tabula.read_pdf(self.filename, pages="all", pandas_options={'header': None, 'names': self.columns})
        df = pandas.concat(dataFrame)
        df = df.astype(str)
              
        # Create a new DataFrame to store the result
        dfresult = pandas.DataFrame(columns=self.columns)

        # Iterate over the rows of the DataFrame
        i = 0
        while i < len(df):
            row = df.iloc[i]
            data = row["Data"]
            valuta = row["Valuta"]
            addebiti = row["Addebiti"]
            accrediti = row["Accrediti"]
            description = row["Descrizione operazioni"]

            # Check if the next row is a continuation of the current row
            while i + 1 < len(df) and df.iloc[i + 1]["Data"] == "nan":
                description += " " + df.iloc[i + 1]["Descrizione operazioni"]
                i += 1
            
            # Add the row to the result DataFrame
            dfresult = pandas.concat(
                [
                    dfresult,
                    pandas.DataFrame(
                        {
                            "Data": [data],
                            "Valuta": [valuta],
                            "Addebiti": [addebiti],
                            "Accrediti": [accrediti],
                            "Descrizione operazioni": [description],
                        }
                    ),
                ],
                ignore_index=True,
            )

            i += 1
    
        print(dfresult)
        result = dfresult.to_dict(orient='records')
        print(result)
        return result
    
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

    def parse_record(self, line: Dict) -> Optional[StatementLine]:
        # Ignore the header
        # if self.cur_record <= 1:
        #     return None

        # Ignore Saldo iniziale/finale
        settlementDateString = line["Valuta"]
        if settlementDateString == "nan" or settlementDateString == "Valuta":
            return None
        
        settlementDate = self.parse_value(settlementDateString, "date")
        date = self.parse_value(line["Data"], "date")
        
        if line["Accrediti"]:
            income = self.parse_amount(line["Accrediti"])
            outcome = 0
        elif line["Addebiti"]:
            outcome = self.parse_amount(line["Addebiti"])
            income = 0
        amount = income - outcome
        currency = self.parse_currency("EUR")

        description = line["Descrizione operazioni"]
        
        transaction = self.create_transaction(description, date, settlementDate, amount, currency)
        stmt_line = transaction.to_statement_line()

        stmt_line.currency = self.parse_currency("EUR")

        return stmt_line

    # noinspection PyUnresolvedReferences
    def parse(self) -> Statement:
        statement = super().parse()
        return statement