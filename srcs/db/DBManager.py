from datetime import datetime, timezone
from sqlite3 import Connection, Cursor
import sqlite3
from typing import Iterator, List, Tuple
from utils.helpers import load_schema
from utils.vectorize import get_vector_as_str
from langdetect import detect
from loguru import logger

class DBManager:

    db_connection: Connection
    db_name: str
    offers_table: str
    application_table: str
    cursor: Cursor
    schema: dict[str,list[tuple[str,str]]]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self.db_connection.commit()
        self.db_connection.close()

    def __init__(self, config):

        self.db_name = config["DB_NAME"]
        self.offers_table = config["DB_OFFERS_TABLE"]
        self.application_table = config["DB_APPLICATION_TABLE"]
        self.schema = load_schema(config["DB_SCHEMA"])
        try:
            self.db_connection = sqlite3.connect(self.db_name)
            self.cursor = self.db_connection.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
        except Exception as e:
           logger.error(f"Error while connecting to {self.db_name}: {e}")
           exit(1)
        logger.info(f"Successfully connected to {self.db_name} database")

    def delete_table(self, table_name: str) -> None:

        try:
            self.cursor.execute(f"DROP TABLE {table_name}")
            logger.info(f"Succesfully deleted {table_name} table from {self.db_name} database.")
        except Exception as e:
            logger.error(f"Couldn't remove {table_name} table from {self.db_name} database: {e}.")

    def delete_everything(self):

        self.delete_table(self.offers_table)
        self.delete_table(self.application_table)

    def get_internships(self) -> Iterator:

        query = f"""
        SELECT o.*
            FROM {self.offers_table} o
            JOIN (
                SELECT email, MAX(id) AS max_offer_id
                FROM Offers
                WHERE invalid_at > ?
                AND NOT has_applied
                AND email NOT IN (
                    SELECT sent_to FROM {self.application_table}
                )
                GROUP BY email
            ) latest
            ON o.email = latest.email AND o.id = latest.max_offer_id;
            """
        now = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        self.cursor.execute(query, (now,))
        return self.cursor

    def get_apprenticeships(self) -> Iterator:

        now = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        self.cursor.execute(f"SELECT * FROM {self.offers_table} WHERE invalid_at > ? AND contract_type == 'apprenticeship' AND NOT has_applied", (now,))
        return self.cursor

    def validate_application(self, offer_id: int):

        self.cursor.execute(f"UPDATE {self.offers_table} SET has_applied = 1 WHERE id = ?", (offer_id,))
        self.db_connection.commit()

    def validate_many_applications(self, offer_ids: list):

        self.cursor.executemany(f"UPDATE {self.offers_table} SET has_applied = 1 WHERE id = ?", offer_ids)
        self.db_connection.commit()

    def get_offers_count(self) -> int:

        count = self.cursor.execute(f"SELECT COUNT(*) FROM {self.offers_table}").fetchone()[0]
        return count

    def add_offers_clean(self, offers: list, model, columns = 18) -> int:

        count_before = self.get_offers_count()
        try:
            self.cursor.executemany(
                f"INSERT INTO {self.offers_table} VALUES ({','.join(['?'] * columns)})",
                [
                    (
                        int(offer['id']),
                        offer['title'],
                        offer['little_description'],
                        offer['big_description'],
                        offer['salary'],
                        offer['contract_type'],
                        offer['email'],
                        offer['full_address'],
                        offer['valid_at'],
                        offer['invalid_at'],
                        offer['min_duration'],
                        offer['max_duration'],
                        offer['slug'],
                        offer['created_at'],
                        int(offer['company_id']),
                        detect(offer['little_description']),
                        int(0),
                        get_vector_as_str(model, offer['big_description']),
                    ) for offer in offers
                ]
            )
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"An error occured: {e}")
        count_after = self.get_offers_count()
        added_offers_count = count_after - count_before
        if added_offers_count: logger.info(f"{added_offers_count} new offers added to database")
        return added_offers_count

    def delete_offer_by_email(self, email: str):

        try:
            self.cursor.execute(f"DELETE FROM {self.offers_table} WHERE email == '?'", (email,))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to remove {email[0]}: {e}")

    def create_table(self, table_name: str, columns: list[tuple[str,str]]):

        columns_def = ', '.join([f"{name} {data_type}" for name, data_type in columns])
        try:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});")
            logger.info(f"Successfully created {table_name} table")
        except Exception as e:
            logger.error(f"Failed to create {table_name} table: {e}")

    def get_applications_count(self):

        return self.cursor.execute(f"COUNT(*) FROM {self.application_table}").fetchone()[0]

    def get_all_applications(self):

        return self.cursor.execute(f"SELECT * FROM {self.application_table}")

    def register_application(self, application: Tuple, columns: List[Tuple[str,str]]):

        try:
            query = f"""INSERT INTO {self.application_table} ({', '.join([item[0] for item in columns])})
                VALUES ({', '.join('?' * len(columns))})"""
            self.cursor.execute(query, application)
            self.db_connection.commit()
            logger.info(f"Successfully registered application {application[3]} to {self.application_table} table.")
        except Exception as e:
            logger.error(f"Failed to register application {application[3]} to {self.application_table} table: {e}.")
            raise

    def get_vector_by_id(self, id: int) -> List[float]:

        return self.cursor.execute(f'SELECT vector FROM {self.offers_table} WHERE id = {id}').fetchone()[0]
