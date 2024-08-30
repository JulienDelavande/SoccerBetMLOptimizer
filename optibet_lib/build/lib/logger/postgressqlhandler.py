from logging import Handler, Filter
from sqlalchemy import text
import datetime

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT = '%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d]\n%(message)s\n'

class PostgreSQLHandler(Handler):
    def __init__(self, engine, service, module):
        super().__init__()
        self.engine = engine
        self.table_name = 'logs'
        self.service = service
        self.module = module

    def emit(self, record):
        try:
            log_entry = self.format(record)
            query = text(f"INSERT INTO {self.table_name} (timestamp, service, module, name, level, message, filename, lineno) VALUES (:timestamp, :service, :module, :name, :level, :message, :filename, :lineno)")
            with self.engine.begin() as connection:
                connection.execute(query, {
                    'timestamp': datetime.datetime.fromtimestamp(record.created),
                    'service': self.service,
                    'module': self.module,
                    'name': record.name,
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'filename': record.pathname,
                    'lineno': record.lineno
                })
        except Exception as e:
            print(f"Failed to log to database: {e}")


class ServiceModuleFilter(Filter):
    def __init__(self, service, module):
        super().__init__()
        self.service = service
        self.module = module

    def filter(self, record):
        record.service = self.service
        record.module = self.module
        return True

