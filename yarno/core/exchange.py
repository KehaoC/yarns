import os, uuid
from .utils import dump_json, load_json

BUS = {
    "tenders": "bus/tenders",
    "bids": "bus/bids",
    "awards": "bus/awards",
    "results": "bus/results",
}

def publish_tender(tender: dict):
    """把 Tender 写到 bus/tenders 目录下"""
    tid = tender.get("tender_id") or str(uuid.uuid4())
    tender["tender_id"] = tid
    path = os.path.join(BUS["tenders"], f"{tid}.json")
    dump_json(path, tender)
    return tid