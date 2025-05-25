from typing import Dict, Tuple
from db.DBManager import DBManager
from job.ReverseHeadHunter import ReverseHeadHunter
from mailing.DeliveryMachine import DeliveryMachine
from dotenv import load_dotenv, dotenv_values
from utils.helpers import now_iso8601_utc
from loguru import logger
from sentence_transformers import SentenceTransformer
import time

class Orchestrator:

    def __init__(self):

        load_dotenv('.env')
        self.conf = dotenv_values('.env')
        self.db = DBManager(self.conf)
        self.hr = ReverseHeadHunter(self.conf)
        self.dm = DeliveryMachine(self.conf)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.add("logs/app.log", rotation="500 MB", level="INFO")

    def create_db_tables(self) -> None:

        for table_name in self.db.schema:
            self.db.create_table(table_name, self.db.schema[table_name])

    def download_offers(self) -> None:

        new_offers = 0
        page = 1
        total = 0
        while True:
            offers = self.hr.fetch_offers_by_page(self.conf["RH_OFFERS_URL"], page)
            new_offers = self.db.add_offers_clean(offers, self.model)
            total += new_offers
            if new_offers < 30:
                break
            page += 1
            time.sleep(1)
        if total:
            logger.info(f"{total} new offers added to database")
        else:
            logger.info("Database already up to date.")

    def create_drafts(self) -> None:

        drafts_created = 0
        offers = list(self.db.get_internships())
        try:
            for offer in offers:
                email = self.dm.create_email(offer, self.conf['DM_ATTACHMENT'])
                draft = self.dm.create_draft(email)
                if draft is not None:
                    self.db.validate_application(offer[0])
                    application = self.create_application(offer, draft)
                    self.db.register_application(application, self.db.schema[self.db.application_table][1:-1])
                    drafts_created += 1
        except Exception as e:
            logger.error(f"Application process stopped: {e}")
        if drafts_created:
            logger.info(f"successfully created {drafts_created} draft(s)")
        else:
            logger.info(f"Couldn't find any new job  !")

    def send_emails(self) -> None:

        email_sent = 0
        #necessary to avoid cursor's reset:
        offers = list(self.db.get_internships())
        try:
            for offer in offers:
                email = self.dm.create_email(offer, self.conf['DM_ATTACHMENT'])
                sent_message = self.dm.send_email(email)
                if sent_message is not None:
                    self.db.validate_application(offer[0])
                    application = self.create_application(offer, sent_message)
                    self.db.register_application(application, self.db.schema[self.db.application_table][1:-1])
                    email_sent += 1
        except Exception as e:
            logger.error(f"Application process stopped: {e}")
        if email_sent:
            logger.success(f"Successfully sent {email_sent} application(s)")
        else:
            logger.info(f"Couldn't find any new job offers !")


    def create_application(self, offer: Tuple, email: Dict, attachment=None) -> Tuple:
        return (
            self.conf["DM_SENDER"], #sent_from
            offer[6],               #sent_to
            now_iso8601_utc(),      #date
            email["id"],            #email_id
            0,                      #got_response
            None,                   #response_date
            attachment,             #attachment
            offer[0],               #offer_id (foreign key)
        )
