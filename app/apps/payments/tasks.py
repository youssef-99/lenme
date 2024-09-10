from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.payments import config
from apps.loans import config as loan_config
from apps.transfers import config as transfer_config
from apps.payments.models import Payment
from apps.transfers.models import Transfer

logger = get_task_logger(__name__)


@shared_task
def update_due_payments():
    now = timezone.now()

    # Fetch payments that are due
    payments_due = Payment.objects.filter(
        ~Q(payment_status=config.PAYMENT_STATUS_PAID),
        payment_due_date__lte=now,
    )
    # Process each payment
    for payment in payments_due:
        # Lock the payment and related loan record to prevent concurrent updates
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment.id)

            # Check if payment is already paid to avoid redundant processing
            if payment.payment_status == config.PAYMENT_STATUS_PAID:
                continue

            borrower_wallet = payment.loan.borrower.wallet
            lender_wallet = payment.loan.lender.wallet

            # Validate payment amount and update balances
            if borrower_wallet.balance >= payment.payment_amount:
                borrower_wallet.balance -= payment.payment_amount
                lender_wallet.balance += payment.payment_amount

                # Save wallets after adjustments
                borrower_wallet.save()
                lender_wallet.save()

                # Mark the payment as paid
                payment.payment_status = config.PAYMENT_STATUS_PAID
                payment.save()

                # Create transfer records for both users
                Transfer.objects.create(
                    user=payment.loan.borrower,
                    amount=payment.payment_amount,
                    transfer_status=transfer_config.TRANSFER_TYPE_MONTHLY_PAYMENT,
                    loan=payment.loan,
                    to_account=payment.loan.lender,
                )
                # Check if all payments are completed for the loan
                remaining_payments = Payment.objects.filter(
                    ~Q(payment_status=config.PAYMENT_STATUS_PAID),
                    loan=payment.loan
                )
                if not remaining_payments.exists():
                    payment.loan.status = loan_config.COMPLETED
                    payment.loan.save()
            else:
                # Update payment status to overdue if insufficient funds
                payment.payment_status = config.PAYMENT_STATUS_OVERDUE
                payment.save()
