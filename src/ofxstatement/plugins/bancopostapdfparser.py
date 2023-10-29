from ast import Dict
from typing import Optional, Any, List
from decimal import Decimal, InvalidOperation
import pandas
import tabula
import PyPDF2

from ofxstatement.parser import StatementParser
from ofxstatement.statement import StatementLine, Currency, Statement
from ofxstatement.plugins.bancopostaTransaction import DebitTransaction, CreditTransaction, ATMTransaction, AddebitoDirettoTransaction, AddebitoPreautorizzatoTransaction, BolloTransaction, BonificoTransaction, CommissioneTransaction, PagamentoPostamatTransaction, PostagiroTransaction

DESCRIPTION_TYPE_MAP = {
    "BONIFICO": BonificoTransaction,
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

class BancoPostaPdfStatementParser(StatementParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
    
    date_format = "%d/%m/%y"

    def parse_currency(self, value: Optional[str]) -> Currency:
        return Currency(symbol=value)
    
    def parse_amount(self, value: str) -> Decimal:
        try:
            result = Decimal(value.replace(" ", "").replace(".", "").replace(",", "."))
            if result.is_nan():
                return Decimal(0)
            else:
                return result
        except (InvalidOperation, TypeError):
            return Decimal(0)

    def parse_value(self, value: Optional[str], field: str) -> Any:
        value = value.strip() if value else value

        if field == "date":
            # check if value is a date in the format dd/mm/yy
            if value and len(value) == 8 and value[2] == "/" and value[5] == "/":
                return super().parse_value(value, field)
            else:
                return None

        if field == "amount":
            return self.parse_amount(value)

        if field == "currency":
            return self.parse_currency(value)

        return super().parse_value(value, field)
    
    def split_records(self) -> List[Dict]:
        num_pages = self.count_pages()
        
        dataFrame = tabula.read_pdf(self.filename, multiple_tables=False, pages="1", stream=True, area=(284.637,13.462,731.112,586.438), pandas_options={'header': None, 'names': self.columns})

        if(num_pages > 1):
            i = 2
            while i <= num_pages:
                dataFrame = dataFrame + tabula.read_pdf(self.filename, multiple_tables=False, pages=str(i), stream=True, area=(106.797,11.974,772.045,586.438), pandas_options={'header': None, 'names': self.columns})
                i += 1

        if(len(dataFrame) == 0):
            print("Error: no data found in pdf file")
            return []
        
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
    
        result = dfresult.to_dict(orient='records')
        return result

    def count_pages(self):
        pdf = open(self.filename, 'rb')
        pdfReader = PyPDF2.PdfReader(pdf)
        num_pages = len(pdfReader.pages)
        print(f'The PDF has {num_pages} pages.')
        return num_pages
    
    def create_transaction(self, text, date, settlement_date, amount, currency):
        for key, value in DESCRIPTION_TYPE_MAP.items():
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
        settlementDate = self.parse_value(line["Valuta"], "date")
        if(settlementDate is None):
            return None
        
        date = self.parse_value(line["Data"], "date")
        
        income = self.parse_value(line["Accrediti"], "amount")
        outcome = self.parse_value(line["Addebiti"], "amount")

        amount = income - outcome
        currency = self.parse_value("EUR", "currency")

        description = line["Descrizione operazioni"]
        
        transaction = self.create_transaction(description, date, settlementDate, amount, currency)
        stmt_line = transaction.to_statement_line()

        return stmt_line

    # noinspection PyUnresolvedReferences
    def parse(self) -> Statement:
        statement = super().parse()
        print(statement)
        return statement