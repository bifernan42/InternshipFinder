from os import PathLike
from typing import Dict, Tuple
from loguru import logger
import json
from datetime import datetime, timezone

def get_file_content(path: str) -> str:

    with open(path, 'r') as file:
        file_content = file.read()
    return file_content

def load_json_data(file: PathLike) -> Dict:

    try:
        with open(file, "r") as fp:
            return json.load(fp)
    except Exception as e:
        logger.error(f"couldn't process file: {file}: {e}")
        return None

def load_schema(schema_file: str) -> dict:

    try:
        with open(schema_file, 'r') as fp:
            data = json.load(fp)
            #print("type of data = ", type(data))
            return {
                table: [tuple(column) for column in data[table]]
                for table in data
            }
    except Exception as e:
            logger.error(f"couldn't process file: {schema_file}: {e}")
            return None

def now_iso8601_utc():

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
