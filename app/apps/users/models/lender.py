from ..models.user import User


class Lender(User):
    class Meta:
        proxy = True
        verbose_name = 'Lender'
        verbose_name_plural = 'Lenders'
