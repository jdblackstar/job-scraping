import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker


def write_to_mysql(data, table_name, logger):
    """
    :param data - data to be written to the database
    :param table_name - name of the table in the database
    :param logging - the logging object

    :returns nothing
    """
    load_dotenv()

    # From .env file
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    # Use SQLAlchemy's URL object to create a more elegant connection string

    DATABASE_CONNECTION_URI = URL(
        drivername="mysql+pymysql",
        username=DB_USERNAME,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

    # create sqlalchemy engine
    engine = create_engine(DATABASE_CONNECTION_URI)

    # create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("Writing data to the database...")
        data.to_sql(table_name, engine, if_exists="append", index=False)
        session.commit()
        logger.info("Data successfully written to the database.")
    except Exception as e:
        logger.error(f"Failed to write data to the database. Error: {str(e)}")
    finally:
        session.close()
