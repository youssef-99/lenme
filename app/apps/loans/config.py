PENDING = 'pending'
FUNDED = 'funded'
COMPLETED = 'completed'

LOAN_STATUS = [
    (PENDING, 'Pending'),
    (FUNDED, 'Funded'),
    (COMPLETED, 'Completed')
]


# Offer Status Choices
OFFER_STATUS_PENDING = 'pending'
OFFER_STATUS_ACCEPTED = 'accepted'
OFFER_STATUS_REJECTED = 'rejected'
OFFER_STATUS_EXPIRED = 'expired'

OFFER_STATUS_CHOICES = [
    (OFFER_STATUS_PENDING, 'Pending'),
    (OFFER_STATUS_ACCEPTED, 'Accepted'),
    (OFFER_STATUS_REJECTED, 'Rejected'),
    (OFFER_STATUS_EXPIRED, 'Expired'),
]
