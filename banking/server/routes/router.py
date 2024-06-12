from fastapi import APIRouter

from .apis import accounts, transactions, user

router = APIRouter()
router.include_router(
    accounts.accounts, prefix="/accounts", tags=["Accounts Management"]
)
router.include_router(user.user, prefix="/users", tags=["User Management"])
router.include_router(
    transactions.transactions, prefix="/transactions", tags=["Admin User Management"]
)
