import logging
from pydantic import BaseModel, Field
from itertools import cycle
import requests
import json
import time

logging.basicConfig(filename='debug.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class Call(BaseModel):
  from_address: str = Field(alias="from")
  to_address: str = Field(alias="to")
  value: str
  gas: str = Field(alias="gasUsed")

  class Config:
    extra = 'ignore'

def extract_calls(data):
  try:
    if isinstance(data, dict):
      if "result" in data:
        yield from extract_calls(data["result"])
      elif "calls" in data:
        yield from extract_calls(data["calls"])
      else:
        if data["type"].lower() == "call":
          yield Call(**data)
    elif isinstance(data, list):
      for item in data:
        yield from extract_calls(item)
  except Exception as e:
    print(f"Error while extracting calls: {e}")

if __name__ == "__main__":
  START_BLOCK = 19000000

  END_BLOCK = 19000000

  SLEEP_TIME = 1

  urls = cycle(json.load(open('source.json')).keys())

  payload = lambda block: {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "debug_traceBlockByNumber",
    "params": [str(block), { "tracer": "callTracer" }]
  }

  headers = {
      "accept": "application/json",
      "content-type": "application/json"
  }

  for block in range(START_BLOCK, END_BLOCK + 1):
    try:
      url = next(urls)
      response = requests.post(url=url, json=payload(block), headers=headers).json()
      with open(f"data/{block}.json", "w") as f:
        f.write(json.dumps(response, indent=2))
      with open(f"call/{block}.json", "w") as f:
        f.write(json.dumps([call.model_dump(mode="json") for call in extract_calls(response)], indent=2))
    except Exception as e:
      logging.error(f"block: {block} | url: {url} | error: {e}")
    finally:
      time.sleep(SLEEP_TIME)