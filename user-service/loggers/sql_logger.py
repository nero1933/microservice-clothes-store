# import logging
# import re
#
# from sqlalchemy import event, Engine
#
# logging.basicConfig(
# 	format="%(message)s",
# 	level=logging.INFO)
#
#
# @event.listens_for(Engine, "before_cursor_execute")
# def log_sql_query(conn, cursor, statement, parameters, context, executemany):
# 	formatted_statement = re.sub(
# 		r"(\s)(SELECT|FROM|WHERE|AND|OR|JOIN|GROUP BY|ORDER BY|HAVING|INSERT|UPDATE|DELETE|LEFT|RIGHT|INNER|OUTER|ON|LIMIT|OFFSET|AS|IN|IS NULL|IS NOT NULL|NOT|BETWEEN|EXISTS)\s",
# 		r"\1\n\2 ", statement.upper())
# 	logging.info(f"SQL ---> STARTS\n\n{formatted_statement}\n\nSQL ---> STOPS")
