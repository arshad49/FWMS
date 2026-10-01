from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import PaymentCreate, PaymentResponse
import uuid

router = APIRouter()

@router.post("/", response_model=PaymentResponse, status_code=201)
def record_payment(payment: PaymentCreate, db = Depends(get_db)):
    cursor = db.cursor()
    
    # 1. Get current invoice details
    cursor.execute("SELECT total_amount, amount_paid FROM invoices WHERE id = %s;", (str(payment.invoice_id),))
    invoice = cursor.fetchone()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 2. Calculate new amount paid
    new_amount_paid = float(invoice['amount_paid']) + float(payment.amount)
    total_amount = float(invoice['total_amount'])
    
    # 3. Determine new status
    if new_amount_paid >= total_amount:
        new_status = "Paid"
    elif new_amount_paid > 0:
        new_status = "Partial"
    else:
        new_status = "Unpaid"
    
    # 4. Insert Payment
    cursor.execute("""
        INSERT INTO payments (invoice_id, amount, payment_date, payment_method, notes)
        VALUES (%s, %s, %s, %s, %s) RETURNING *;
    """, (str(payment.invoice_id), payment.amount, payment.payment_date, payment.payment_method, payment.notes))
    new_payment = cursor.fetchone()
    
    # 5. Update Invoice with new amount_paid and status
    cursor.execute("""
        UPDATE invoices SET amount_paid = %s, status = %s WHERE id = %s;
    """, (new_amount_paid, new_status, str(payment.invoice_id)))
    
    db.commit()
    cursor.close()
    
    # Fetch invoice number for response
    cursor = db.cursor()
    cursor.execute("SELECT invoice_number FROM invoices WHERE id = %s;", (str(payment.invoice_id),))
    inv = cursor.fetchone()
    cursor.close()
    
    new_payment['invoice_number'] = inv['invoice_number'] if inv else None
    return new_payment

@router.get("/invoice/{invoice_id}")
def get_payments_for_invoice(invoice_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM payments WHERE invoice_id = %s ORDER BY payment_date DESC;", (invoice_id,))
    payments = cursor.fetchall()
    cursor.close()
    return payments