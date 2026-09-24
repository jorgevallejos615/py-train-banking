from src.banking import (
    BankAccount,
    Customer,
    InsufficientFundsError,
    configure_logging,
    logger,
)

customers: list[Customer] = []


def _find_customer(user_id: int) -> Customer:
    for customer in customers:
        if customer.user_id == user_id:
            return customer
    raise ValueError(f"No customer found for user ID {user_id}")


def _find_account(customer: Customer, account_number: str) -> BankAccount:
    for account in customer.accounts:
        if account.account_number == account_number:
            return account
    raise ValueError(f"No account found for number {account_number}")


def _add_customer() -> None:
    name = input("Customer name: ")
    birth_date = input("Birth date (YYYY-MM-DD): ")
    customer = Customer(name, birth_date)
    customers.append(customer)
    print(f"Customer created with user ID {customer.user_id}.")


def _add_account() -> None:
    user_id = int(input("Customer user ID: "))
    customer = _find_customer(user_id)
    account_number = input("Account number: ")
    currency = input("Currency [USD]: ") or "USD"
    account_type = input("Account type [checking/savings]: ") or "checking"
    initial_balance = input("Initial balance: ")
    if account_type.lower() == "savings":
        account = BankAccount.create_savings(
            account_number,
            currency,
            initial_balance=initial_balance,
        )
    else:
        account = BankAccount(account_number, currency, account_type, initial_balance)
    customer.add_account(account)
    print(f"Account {account.account_number} added to customer {customer.user_id}.")


def _perform_transaction() -> None:
    user_id = int(input("Customer user ID: "))
    customer = _find_customer(user_id)
    transaction = input("Transaction (deposit/withdraw/convert/transfer): ").lower()
    if transaction == "transfer":
        source = _find_account(customer, input("Source account number: "))
        target = _find_account(customer, input("Target account number: "))
        amount = input("Amount: ")
        customer.transfer(source, target, amount)
        print("Transfer completed.")
    elif transaction in {"deposit", "withdraw"}:
        account = _find_account(customer, input("Account number: "))
        amount = input("Amount: ")
        if transaction == "deposit":
            account.deposit(amount)
        else:
            account.withdraw(amount)
        print(f"Updated balance: {account.balance}")
    elif transaction == "convert":
        account = _find_account(customer, input("Account number: "))
        target_currency = input("Target currency: ")
        exchange_rate = input("Exchange rate: ")
        account.convert_currency(target_currency, exchange_rate)
    else:
        raise ValueError("Unknown transaction")


def menu() -> None:
    """Run the interactive customer, account, and transaction menu."""
    while True:
        print("\n1. Add customer")
        print("2. Add bank account")
        print("3. Perform transaction")
        print("4. Exit")
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                _add_customer()
            elif choice == "2":
                _add_account()
            elif choice == "3":
                _perform_transaction()
            elif choice == "4":
                print("Goodbye.")
                return
            else:
                raise ValueError("Invalid menu option")
        except (InsufficientFundsError, TypeError, ValueError) as error:
            logger.error("Menu operation failed: %s", error)
            print(f"Operation failed: {error}")


def main() -> None:
    configure_logging()
    logger.info("Banking application started")
    menu()


if __name__ == "__main__":
    configure_logging()
    menu()
