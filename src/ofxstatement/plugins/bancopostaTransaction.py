from enum import Enum
from ofxstatement.statement import StatementLine, generate_transaction_id
import re

class TransactionType(Enum):
    BONIFICO = "BONIFICO"
    POSTAGIRO = "POSTAGIRO"
    BOLLO = "IMPOSTA DI BOLLO"
    COMMISSIONE = "COMMISSIONE"
    PAGAMENTO_POSTAMAT = "PAGAMENTO_POSTAMAT"
    ATM = "ATM"
    ADDEBITO_DIRETTO = "ADDEBITO DIRETTO SDD"
    ADDEBITO_PREAUTORIZZATO = "ADDEBITO PREAUTORIZZATO"
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

TRANSACTION_TYPES = {
    TransactionType.BONIFICO: "XFER",
    TransactionType.POSTAGIRO : "XFER",
    TransactionType.BOLLO: "FEE",
    TransactionType.COMMISSIONE: "SRVCHG",
    TransactionType.PAGAMENTO_POSTAMAT: "PAYMENT",
    TransactionType.ATM: "ATM",
    TransactionType.ADDEBITO_DIRETTO: "DIRECTDEBIT",
    TransactionType.ADDEBITO_PREAUTORIZZATO: "DIRECTDEBIT",
    TransactionType.CREDIT: "CREDIT",
    TransactionType.DEBIT: "DEBIT"
}

class BancoPostaTransaction:
    def __init__(self, date, settlement_date, amount, text, currency):
        self.date = date
        self.settlement_date = settlement_date
        self.amount = amount
        self.currency = currency
        self.type = None
        self.extract_info(text)

    def extract_info(self, text):
        raise NotImplementedError("This method must be implemented by a subclass")

    def to_statement_line(self):
        statement_line = StatementLine()
        statement_line.date = self.settlement_date
        statement_line.amount = self.amount
        statement_line.trntype = TRANSACTION_TYPES[self.type]
        statement_line.id = generate_transaction_id(statement_line)
        return statement_line



class BonificoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.BONIFICO

    def extract_info(self, text):
        # type_end_index = text.find("TRN")
        # if type_end_index == -1:
        #     return None, text, text
        # trntype = text[:type_end_index].strip()
        
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

        self.payee = payee
        self.description = memo

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class PostagiroTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.POSTAGIRO

    def extract_info(self, text):
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
            payee = text[payee_start_index:].strip()
            memo = ""
        else:
            payee = text[payee_start_index:payee_end_index].strip()
            memo_start_index = payee_end_index + len("PER")
            memo = text[memo_start_index:].strip()

        self.payee = payee
        self.description = memo

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        if self.description:
            statement_line.payee = f"{self.payee} - {self.description}"
        else:
            statement_line.payee = self.payee
        statement_line.memo = statement_line.payee
        return statement_line

class CreditTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.CREDIT

    def extract_info(self, text):
        self.payee = text
        self.description = text

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class DebitTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.DEBIT

    def extract_info(self, text):
        self.payee = text
        self.description = text

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class BolloTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.BOLLO

    def extract_info(self, text):
        self.payee = TransactionType.BOLLO.value
        self.description = TransactionType.BOLLO.value

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class CommissioneTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.COMMISSIONE

    def extract_info(self, text):
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

        self.payee = payee
        self.description = memo

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class PagamentoPostamatTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.PAGAMENTO_POSTAMAT

    def extract_info(self, text):      
        date_time_pattern = r"\d{2}/\d{2}/\d{4} \d{2}\.\d{2}"
        match = re.search(date_time_pattern, text)
        if match:
            payee_start_index = match.end()
            payee = text[payee_start_index:].strip()
        else:
            payee = text

        self.payee = payee
        self.description = "PAGAMENTO POSTAMAT"

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class ATMTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ATM

    def extract_info(self, text):
        self.payee = "ATM"
        self.description = text

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class AddebitoDirettoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ADDEBITO_DIRETTO

    def extract_info(self, text):
        trntype = TransactionType.ADDEBITO_DIRETTO.value
        
        payee_start_index = text.find(trntype) + len(trntype)
        payee_end_index = text.find("CID")
        payee = text[payee_start_index:payee_end_index].strip()
        
        memo = trntype + " " + payee

        self.payee = payee
        self.description = memo

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line

class AddebitoPreautorizzatoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ADDEBITO_PREAUTORIZZATO

    def extract_info(self, text):
        trntype = TransactionType.ADDEBITO_PREAUTORIZZATO.value
        
        payee_start_index = text.find(trntype) + len(trntype)
        payee_end_index = text.find("CID")
        payee = text[payee_start_index:payee_end_index].strip()
        
        memo = trntype + " " + payee

        self.payee = payee
        self.description = memo

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        statement_line.memo = self.description
        return statement_line