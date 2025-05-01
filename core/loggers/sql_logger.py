import logging
import re

from sqlalchemy import event, Engine


sql_log = logging.getLogger('sql_logger')

sql_log.setLevel(logging.INFO)
sql_handler = logging.StreamHandler()
sql_formatter = logging.Formatter('%(message)s')
sql_handler.setFormatter(sql_formatter)
sql_log.addHandler(sql_handler)


@event.listens_for(Engine, "before_cursor_execute")
def log_sql_query(conn, cursor, statement, parameters, context, executemany):
	pass
	formatted_statement = re.sub(
		r"(\s)(SELECT|FROM|WHERE|AND|OR|JOIN|GROUP BY|ORDER BY|HAVING|INSERT|UPDATE|DELETE|LEFT|RIGHT|INNER|OUTER|ON|LIMIT|OFFSET|AS|IN|IS NULL|IS NOT NULL|NOT|BETWEEN|EXISTS)\s",
		r"\1\2 ", statement.upper())
	sql_log.info(f"SQL ---> STARTS\n\n{formatted_statement}\n\nSQL ---> STOPS")
