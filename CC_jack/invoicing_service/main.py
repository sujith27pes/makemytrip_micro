from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4, UUID

app = FastAPI()

# Mock database for invoices and payouts
invoices_db = {}
payouts_db = {}

class Invoice(BaseModel):
    agent_id: UUID
    customer_name: str
    amount: float

class Payout(BaseModel):
    agent_id: UUID
    payout_amount: float

@app.post("/invoice")
def generate_invoice(invoice: Invoice):
    invoice_id = uuid4()
    invoices_db[invoice_id] = invoice
    return {"invoice_id": invoice_id, "amount": invoice.amount}

@app.get("/agents/{agent_id}/payouts")
def get_agent_payouts(agent_id: UUID):
    agent_payouts = [payout for payout in payouts_db.values() if payout.agent_id == agent_id]
    return agent_payouts

@app.post("/payout")
def trigger_payout(payout: Payout):
    payout_id = uuid4()
    payouts_db[payout_id] = payout
    return {"payout_id": payout_id, "amount": payout.payout_amount}
