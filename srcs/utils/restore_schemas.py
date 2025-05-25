import json
from loguru import logger

def load_schema(schema_file: str) -> dict:
    """
        This function loads the current database schema from
        <schema_file> and returns it as a dict
    """
    try:
        with open(schema_file, 'r') as fp:
            data = json.load(fp)
            #print("type of data = ", type(data))
            return {
                table: [tuple(column) for column in data[table]]
                for table in data
            }
    except:
            logger.error(f"couldn't process file: {schema_file}")
            return None
