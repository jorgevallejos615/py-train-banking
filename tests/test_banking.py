from datetime import date
from decimal import Decimal

import pytest

import main
from src.banking import BankAccount, Customer, InsufficientFundsError


@pytest.fixture(autouse=True)
def reset_customer_state():
    Customer.user_count = 0
    main.customers.clear()
    yield
    main.customers.clear()


def test_bank_account_properties_and_balance_setter(caplog):
    account = BankAccount("ACC-001", "EUR", "checking", "25.50")

    assert account.account_number == "ACC-001"
    assert account.currency == "EUR"
    assert account.account_type == "checking"
    assert account.balance == Decimal("25.50")

    with caplog.at_level("ERROR"), pytest.raises(ValueError, match="negative"):
        account.balance = -1

    assert "Rejected negative balance" in caplog.text


def test_deposit_and_withdraw_log_updated_balances(caplog):
    account = BankAccount("ACC-001", initial_balance=100)

    with caplog.at_level("INFO"):
        assert account.deposit("25.50") == Decimal("125.50")
        assert account.withdraw("20.50") == Decimal("105.00")

    assert "Deposit completed; updated balance: 125.50" in caplog.text
    assert "Withdrawal completed; updated balance: 105.00" in caplog.text


def test_negative_transaction_amount_logs_error(caplog):
    account = BankAccount("ACC-001")

    with caplog.at_level("ERROR"), pytest.raises(ValueError, match="non-negative"):
        account.deposit(-1)
    with caplog.at_level("ERROR"), pytest.raises(ValueError, match="non-negative"):
        account.withdraw(-1)

    assert caplog.text.count("Transaction amount must be non-negative") == 2


def test_withdrawal_rejects_overdraft_and_savings_reserve(caplog):
    checking = BankAccount("CHECKING", initial_balance=10)
    with caplog.at_level("ERROR"), pytest.raises(InsufficientFundsError) as error:
        checking.withdraw(11)
    assert error.value.amount == 11.0
    assert "exceeds current balance" in caplog.text

    savings = BankAccount("SAVINGS", _account_type="savings", initial_balance=150)
    with pytest.raises(ValueError, match="minimum balance"):
        savings.withdraw(51)
    assert savings.balance == Decimal("150.00")


def test_savings_factory_and_from_string():
    savings = BankAccount.create_savings("SAVE-001", "EUR", initial_balance=100)
    parsed = BankAccount.from_string("CHECK-001,USD,checking,25.50")

    assert savings.account_type == "savings"
    assert savings.balance == Decimal("100.00")
    assert parsed.account_number == "CHECK-001"
    assert parsed.balance == Decimal("25.50")
    with pytest.raises(ValueError, match="at least 100"):
        BankAccount.create_savings("SAVE-002", initial_balance=99.99)


def test_convert_currency_prints_converted_balance(capsys):
    account = BankAccount("ACC-001", initial_balance=100)

    account.convert_currency("EUR", "0.92")

    assert capsys.readouterr().out == "Balance in EUR: 92.00\n"
    assert account.balance == Decimal("100.00")


def test_convert_currency_rejects_non_positive_rate(caplog):
    account = BankAccount("ACC-001", initial_balance=100)

    with caplog.at_level("ERROR"), pytest.raises(ValueError, match="greater than zero"):
        account.convert_currency("EUR", 0)

    assert "Exchange rate must be positive" in caplog.text


def test_bank_account_transfer_to():
    source = BankAccount("SOURCE", initial_balance=100)
    target = BankAccount("TARGET")

    source.transfer_to(target, 35)

    assert source.balance == Decimal("65.00")
    assert target.balance == Decimal("35.00")


def test_customer_constructor_ids_accounts_and_factory():
    first = Customer("Ada Lovelace", "2000-01-01")
    second = Customer.from_string("Grace Hopper,2001-01-01")

    assert first.name == "Ada Lovelace"
    assert first.birth_date == date(2000, 1, 1)
    assert first.user_id == 1
    assert second.user_id == 2
    assert first.accounts == ()
    assert Customer.is_valid_account_number("ACC-001")
    assert not Customer.is_valid_account_number("")


def test_customer_rejects_underage_customer():
    with pytest.raises(ValueError, match="at least 18"):
        Customer("Minor", date(2010, 1, 1))


def test_customer_add_remove_accounts_and_total_balance(caplog):
    customer = Customer("Ada", "2000-01-01")
    first = BankAccount("ACC-001", initial_balance=25)
    second = BankAccount("ACC-002", initial_balance=74.50)
    customer.add_account(first)
    customer.add_account(second)

    assert customer.accounts == (first, second)
    assert customer.get_total_balance() == Decimal("99.50")
    assert customer.remove_account("ACC-001") is first
    assert customer.accounts == (second,)

    invalid = BankAccount("ACC-003")
    invalid._account_number = ""
    with caplog.at_level("ERROR"):
        customer.add_account(invalid)
    assert customer.accounts == (second,)
    assert "Invalid account number" in caplog.text


def test_customer_transfer_enforces_ownership_and_account_rules(caplog):
    customer = Customer("Ada", "2000-01-01")
    source = BankAccount("SOURCE", initial_balance=150)
    target = BankAccount("TARGET")
    customer.add_account(source)
    customer.add_account(target)

    customer.transfer(source, target, 50)
    assert source.balance == Decimal("100.00")
    assert target.balance == Decimal("50.00")

    external = BankAccount("EXTERNAL")
    with (
        caplog.at_level("ERROR"),
        pytest.raises(ValueError, match="belong to this customer"),
    ):
        customer.transfer(source, external, 10)
    assert "Transfer accounts must belong" in caplog.text


def test_menu_adds_customer_account_and_deposits(monkeypatch, capsys):
    responses = iter(
        [
            "1",
            "Ada Lovelace",
            "2000-01-01",
            "2",
            "1",
            "ACC-001",
            "USD",
            "checking",
            "50",
            "3",
            "1",
            "deposit",
            "ACC-001",
            "25",
            "4",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))

    main.menu()

    assert main.customers[0].accounts[0].balance == Decimal("75.00")
    assert "Goodbye." in capsys.readouterr().out
