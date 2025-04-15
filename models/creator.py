import os
import sys
import yaml
from models import user,products,invoice,excel

configfile = {}
scriptDir = os.path.dirname(os.path.abspath(__file__))
config_filepath = str(os.path.dirname(scriptDir)+"/configfile.yml")

if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

async def create_table():
    await user.create_table_user(configfile)
    await products.create_table_shop_invoice(configfile)
    await invoice.create_invoice_table(configfile)
    await excel.create_excel_table(configfile)
