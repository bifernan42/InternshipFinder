from schedule.Orchestrator import Orchestrator

def main():
    otr = Orchestrator()
    otr.create_db_tables()
    otr.download_offers()
    otr.send_emails()

if __name__ == '__main__':
    main()
