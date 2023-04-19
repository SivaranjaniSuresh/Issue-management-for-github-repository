import snowflake.connector


class DBUtil:
    def __init__(self, user, password, account, warehouse, database, schema):
        self.conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

    def add_record(self, database, schema, table_name, record):
        cursor = self.conn.cursor()
        columns = ", ".join(record.keys())
        values = ", ".join(f"'{value}'" for value in record.values())
        query = f"INSERT INTO {database}.{schema}.{table_name} ({columns}) VALUES ({values})"
        cursor.execute(query)
        self.conn.commit()
        cursor.close()

    def update_record(self, database, schema, table_name, record, conditions):
        cursor = self.conn.cursor()
        set_values = ", ".join(
            f"{column} = '{value}'" for column, value in record.items()
        )
        conditions_str = " AND ".join(
            f"{column} = '{value}'" for column, value in conditions.items()
        )
        query = f"UPDATE {database}.{schema}.{table_name} SET {set_values} WHERE {conditions_str}"
        cursor.execute(query)
        self.conn.commit()
        cursor.close()

    def delete_record(self, database, schema, table_name, conditions):
        cursor = self.conn.cursor()
        conditions_str = " AND ".join(
            f"{column} = '{value}'" for column, value in conditions.items()
        )
        query = f"DELETE FROM {database}.{schema}.{table_name} WHERE {conditions_str}"
        cursor.execute(query)
        self.conn.commit()
        cursor.close()

    def close(self):
        self.conn.close()
