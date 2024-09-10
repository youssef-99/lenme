from apps.users.models.user import User


class Borrower(User):
    class Meta:
        proxy = True
        verbose_name = 'Borrower'
        verbose_name_plural = 'Borrowers'
