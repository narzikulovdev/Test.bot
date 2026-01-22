import os
from dotenv import load_dotenv

load_dotenv()

botTOKEN = os.getenv("botTOKEN")

# База данных (MySQL)
mysqlHost = os.getenv("mysqlHost")
mysqlUser = os.getenv("mysqlUser")
mysqlPassword = os.getenv("mysqlPassword")
mysqlDatabase = os.getenv("mysqlDatabase")

# Логи в группу (опционально)
logsGroupID = int(os.getenv("logsGroupID", '0'))

