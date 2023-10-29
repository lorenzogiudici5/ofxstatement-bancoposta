import os
from ofxstatement.plugins.bancopostacsvparser import BancoPostaCSVStatementParser
from ofxstatement.plugins.bancopostapdfparser import BancoPostaPdfStatementParser

from ofxstatement.plugin import Plugin

class BancoPostaPlugin(Plugin):
    """BancoPosta plugin (for developers only)"""

    def get_parser(self, filename: str):
        extension = os.path.splitext(filename)[1]

        required_columns = [
            "Data",
            "Valuta",
            "Addebiti",
            "Accrediti",
            "Descrizione operazioni",
        ]

        if extension == '.csv':
            f = open(filename, "r", encoding='utf-8')
            signature = f.readline()

            csv_columns = [col.strip() for col in signature.split(";")]
            
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
        elif extension == '.pdf':
            # dataFrame = tabula.read_pdf(filename, pages="all")
            parser = BancoPostaPdfStatementParser(filename)
            parser.columns = {col: required_columns.index(col) for col in required_columns}
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
        else:
            print('Unsupported file type')
    
        