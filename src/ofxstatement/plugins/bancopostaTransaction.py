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
    ADDEBITO_DIRITTI_DI_CUSTODIA = "ADDEBITO DIRITTI DI CUSTODIA"
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

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
    def __init__(self, date, settlement_date, amount, description, currency):
        self.date = date
        self.settlement_date = settlement_date
        self.amount = amount
        self.currency = currency
        self.type = None
        self.description = description
        self.payee = description
        self.extract_info(description)

    def extract_info(self, description):
        raise NotImplementedError("This method must be implemented by a subclass")

    def to_statement_line(self):
        statement_line = StatementLine()
        statement_line.date = self.settlement_date
        statement_line.amount = self.amount
        statement_line.trntype = TRANSACTION_TYPES[self.type]
        statement_line.memo = self.description
        statement_line.payee = self.payee
        statement_line.currency = self.currency
        statement_line.id = generate_transaction_id(statement_line)
        return statement_line

class CreditTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.CREDIT

    def extract_info(self, description):
        self.payee = description

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line

class DebitTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.DEBIT

    def extract_info(self, description):
        if description.find(TransactionType.ADDEBITO_DIRITTI_DI_CUSTODIA.value) != -1:
            self.payee = TransactionType.ADDEBITO_DIRITTI_DI_CUSTODIA.value
        else:
            self.payee = description

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line

class BonificoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.BONIFICO

    def extract_info(self, description):
        payee = None
        reason = None

        # Version 1 with "BENEF"
        if "DA" in description or "BENEF" in description:
            payee_start_index = description.find("DA")
            if payee_start_index == -1:
                payee_start_index = description.find("BENEF")
                if payee_start_index == -1:
                    return None, description, description
                payee_start_index += len("BENEF")
            else:
                payee_start_index += len("DA")

            payee_end_index = description.find("PER ")
            if payee_end_index == -1:
                payee_end_index = len(description)
            
            payee = description[payee_start_index:payee_end_index].strip()
            
            reason_start_index = payee_end_index + len("PER ")
            reason = description[reason_start_index:].strip()

        # Version 2 with "A"
        elif "Da " in description or "A " in description:
            payee_start_index = description.find("Da ")
            if payee_start_index == -1:
                payee_start_index = description.find("A ")
                if payee_start_index == -1:
                    return None, description, description
                payee_start_index += len("A ")
            else:
                payee_start_index += len("Da ")

            payee_end_index = description.find(" per ")
            if payee_end_index == -1:
                payee_end_index = len(description)
            
            payee = description[payee_start_index:payee_end_index].strip()
            
            reason_start_index = payee_end_index + len(" per ")
            reason_end_index = description.find(" TRN ", reason_start_index)
            if reason_end_index == -1:
                reason_end_index = len(description)
            
            reason = description[reason_start_index:reason_end_index].strip()

        self.payee = payee
        self.reason = reason

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        if self.reason:
            statement_line.payee = f"{self.payee} - {self.reason}"
        else:
            statement_line.payee = self.payee
        return statement_line

class PostagiroTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.POSTAGIRO

    def extract_info(self, description):
        # if description is equal to "POSTAGIRO ONLINE" then the payee and the reason is "POSTAGIRO ONLINE"
        if description == "POSTAGIRO ONLINE":
            self.payee = description
            self.reason = ""
            return
        
        # Version 2 with "A" and "Da"
        if description.startswith("POSTAGIRO A") or description.startswith("POSTAGIRO Da"):
            # Split the description to exclude the TRN part
            parts = description.split(" TRN ")
            if len(parts) > 1:
                description = parts[0]
            
            # Split the description to extract payee and reason
            parts = description.split(" per ")
            if len(parts) == 2:
                self.payee = parts[0].replace("POSTAGIRO A", "").replace("POSTAGIRO Da", "").strip()
                self.reason = parts[1].strip()
                return

        # Version 1 with "BENEF"
        payee_start_index = description.find("DA")
        if payee_start_index == -1:
            payee_start_index = description.find("BENEF")
            if payee_start_index == -1:
                return None, description, description
            payee_start_index += len("BENEF")
        else:
            payee_start_index += len("DA")
        
        # reason
        payee_end_index = description.find("PER ")
        if payee_end_index == -1:
            self.payee = description[payee_start_index:].strip()
            self.reason = ""
        else:
            self.payee = description[payee_start_index:payee_end_index].strip()
            self.reason = description[payee_end_index + len("PER "):].strip()

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        if self.reason:
            statement_line.payee = f"{self.payee} - {self.reason}"
        else:
            statement_line.payee = self.payee
        return statement_line

class BolloTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.BOLLO

    def extract_info(self, description):
        if description.find("IMPOSTA DI BOLLO PRODOTTI FINANZIARI") != -1:
            self.payee = "IMPOSTA DI BOLLO PRODOTTI FINANZIARI"
        else:
            self.payee = description

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line

class CommissioneTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.COMMISSIONE

    def extract_info(self, description):
        if description.find("COMMISSIONE SDD") != -1:
            self.payee = "COMMISSIONE SDD"
        elif description.find("COMMISSIONE BONIFICO INSTANT") != -1:
            self.payee = "COMMISSIONE BONIFICO INSTANT"
        elif description.find("COMMISSIONE RICARICA PREPAGATA") != -1:
            self.payee = "COMMISSIONE RICARICA PREPAGATA"
        else:   
            self.payee = "COMMISSIONE"

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee

        return statement_line

class PagamentoPostamatTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.PAGAMENTO_POSTAMAT

    def extract_info(self, description):      
        date_time_pattern = r"\d{2}/\d{2}/\d{4} \d{2}\.\d{2}"
        match = re.search(date_time_pattern, description)
        if match:
            payee_start_index = match.end()
            payee_end_index = description.find(" OPERAZIONE ")
            if payee_end_index != -1:
                payee = description[payee_start_index:payee_end_index].strip()
            else:
                payee = description[payee_start_index:].strip()
        else:
            payee = ""

        if ' OPERAZIONE ' in description and ' CARTA ' in description:
            self.operation = description.split(" OPERAZIONE ")[1].split(" CARTA ")[0]
            self.card = description.split(" CARTA ")[1]

        self.payee = payee

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        statement_line.payee = self.payee
        return statement_line

class ATMTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ATM

    def extract_info(self, description):
        if description.find("PRELIEVO") != -1:
            trntype = "PRELIEVO"
        else:
            if description.find("VERSAMENTO") != -1:
                trntype  = "VERSAMENTO"

        self.payee = trntype

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line

class AddebitoDirettoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ADDEBITO_DIRETTO

    def extract_info(self, description):
        trntype = TransactionType.ADDEBITO_DIRETTO.value
        
        payee_start_index = description.find(trntype) + len(trntype)
        payee_end_index = description.find("CID")
        payee = description[payee_start_index:payee_end_index].strip()

        if payee.startswith("**"):
            payee = payee[2:].strip()
        
        reason = trntype + " " + payee

        self.payee = payee

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line

class AddebitoPreautorizzatoTransaction(BancoPostaTransaction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = TransactionType.ADDEBITO_PREAUTORIZZATO

    def extract_info(self, description):
        trntype = TransactionType.ADDEBITO_PREAUTORIZZATO.value
        
        payee_start_index = description.find(trntype) + len(trntype)
        payee_end_index = description.find("CID")
        payee = description[payee_start_index:payee_end_index].strip()
        
        reason = trntype + " " + payee
        self.payee = payee

    def to_statement_line(self):
        statement_line = super().to_statement_line()
        return statement_line