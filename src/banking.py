from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import ClassVar


class InsufficientFundsError(Exception):
	def __init__(self, message: str, amount: float) -> None:
		super().__init__(message)
		self.amount = amount


class BankAccount:
	"""A bank account whose balance can only change through account operations."""

	_bank_name: ClassVar[str] = "Python Community Bank"
	_next_account_number: ClassVar[int] = 100000

	def __init__(
		self,
		account_number: str,
		currency: str = "USD",
		_account_type: str = "checking",
		initial_balance: Decimal | int | float | str = 0.0,
	) -> None:
		if not isinstance(account_number, str) or not account_number.strip():
			raise ValueError("Account number cannot be empty")
		self._account_number = account_number.strip()
		self._currency = currency
		self._account_type = _account_type
		self.balance = initial_balance

	@property
	def account_number(self) -> str:
		return self._account_number

	@property
	def currency(self) -> str:
		return self._currency

	@property
	def account_type(self) -> str:
		return self._account_type

	@property
	def balance(self) -> Decimal:
		return self.__balance

	@balance.setter
	def balance(self, amount: Decimal | int | float | str) -> None:
		try:
			validated_amount = Decimal(str(amount))
		except (InvalidOperation, ValueError):
			raise ValueError("Balance must be a valid number") from None
		if validated_amount < 0:
			logger.error("Rejected negative balance: %s", amount)
			raise ValueError("Balance cannot be negative")
		self.__balance = self.validate_amount(validated_amount, allow_zero=True)

	def deposit(self, amount: Decimal | int | float | str) -> Decimal:
		validated_amount = self._validate_transaction_amount(amount)
		self.balance = self.__balance + validated_amount
		logger.info("Deposit completed; updated balance: %s", self.__balance)
		return self.balance

	def withdraw(self, amount: Decimal | int | float | str) -> Decimal:
		validated_amount = self._validate_transaction_amount(amount)
		if validated_amount > self.__balance:
			logger.error(
				"Withdrawal of %s exceeds current balance of %s",
				validated_amount,
				self.__balance,
			)
			raise InsufficientFundsError(
				f"Cannot withdraw {validated_amount}; balance is {self.__balance}",
				float(validated_amount),
			)
		if self._account_type == "savings" and (
			self.__balance - validated_amount < Decimal("100.00")
		):
			logger.error("Savings accounts must retain a minimum balance of 100.00")
			raise ValueError("Savings accounts must retain a minimum balance of 100.00")
		self.balance = self.__balance - validated_amount
		logger.info("Withdrawal completed; updated balance: %s", self.__balance)
		return self.balance

	def convert_currency(
		self, target_currency: str, exchange_rate: Decimal | int | float | str
	) -> None:
		try:
			validated_rate = Decimal(str(exchange_rate))
		except (InvalidOperation, ValueError):
			logger.error("Invalid exchange rate: %s", exchange_rate)
			raise ValueError("Exchange rate must be a positive number") from None
		if not validated_rate.is_finite() or validated_rate <= 0:
			logger.error("Exchange rate must be positive: %s", exchange_rate)
			raise ValueError("Exchange rate must be greater than zero")
		converted_balance = (self.__balance * validated_rate).quantize(
			Decimal("0.01")
		)
		print(f"Balance in {target_currency}: {converted_balance:.2f}")

	def transfer_to(
		self, recipient: BankAccount, amount: Decimal | int | float | str
	) -> None:
		if not isinstance(recipient, BankAccount):
			raise TypeError("Recipient must be a BankAccount")
		validated_amount = self.validate_amount(amount)
		self.withdraw(validated_amount)
		recipient.deposit(validated_amount)

	@classmethod
	def create_savings(
		cls,
		account_number: str,
		currency: str = "USD",
		_account_type: str = "savings",
		initial_balance: Decimal | int | float | str = 0.0,
	) -> BankAccount:
		validated_balance = cls.validate_amount(initial_balance, allow_zero=True)
		if _account_type == "savings" and validated_balance < Decimal("100.00"):
			raise ValueError("Savings accounts require an initial balance of at least 100.00")
		return cls(account_number, currency, _account_type, validated_balance)

	@classmethod
	def from_string(cls, account_data: str) -> BankAccount:
		"""Create an account from ``account_number,currency,type,balance``."""
		parts = [part.strip() for part in account_data.split(",")]
		if len(parts) != 4:
			raise ValueError("Account data must contain number, currency, type, and balance")
		return cls(parts[0], parts[1], parts[2], parts[3])

	@classmethod
	def _generate_account_number(cls) -> str:
		account_number = str(cls._next_account_number)
		cls._next_account_number += 1
		return account_number

	@staticmethod
	def _validate_transaction_amount(
		amount: Decimal | int | float | str,
	) -> Decimal:
		try:
			validated_amount = Decimal(str(amount))
		except (InvalidOperation, ValueError):
			logger.error("Invalid transaction amount: %s", amount)
			raise ValueError("Amount must be a valid number") from None
		if not validated_amount.is_finite() or validated_amount < 0:
			logger.error("Transaction amount must be non-negative: %s", amount)
			raise ValueError("Amount must be non-negative")
		return validated_amount.quantize(Decimal("0.01"))

	@staticmethod
	def validate_amount(
		amount: Decimal | int | float | str, *, allow_zero: bool = False
	) -> Decimal:
		try:
			validated_amount = Decimal(str(amount))
		except (InvalidOperation, ValueError):
			raise ValueError("Amount must be a valid number") from None
		if not validated_amount.is_finite():
			raise ValueError("Amount must be finite")
		if validated_amount < 0 or (validated_amount == 0 and not allow_zero):
			raise ValueError("Amount must be greater than zero")
		return validated_amount.quantize(Decimal("0.01"))


class Customer:
	"""A customer that owns a privately managed collection of bank accounts."""

	user_count: ClassVar[int] = 0

	def __init__(self, name: str, birth_date: date | str) -> None:
		if not isinstance(name, str) or not name.strip():
			raise ValueError("Customer name cannot be empty")
		self.__name = name.strip()
		self.__birth_date = self.validate_birth_date(birth_date)
		self._user_id = self._generate_user_id()
		self.__accounts: list[BankAccount] = []

	@property
	def user_id(self) -> int:
		return self._user_id

	@property
	def name(self) -> str:
		return self.__name

	@property
	def birth_date(self) -> date:
		return self.__birth_date

	@property
	def accounts(self) -> tuple[BankAccount, ...]:
		return tuple(self.__accounts)

	def add_account(self, account: BankAccount) -> None:
		if not isinstance(account, BankAccount):
			raise TypeError("Customer accounts must be BankAccount instances")
		if not self.is_valid_account_number(account.account_number):
			logger.error("Invalid account number: %s", account.account_number)
			return
		if any(existing.account_number == account.account_number for existing in self.__accounts):
			raise ValueError("Customer already owns this account")
		self.__accounts.append(account)

	def get_total_balance(self) -> Decimal:
		total_balance = Decimal("0.00")
		for account in self.__accounts:
			total_balance += account.balance
		return total_balance

	def transfer(
		self,
		source_account: BankAccount,
		target_account: BankAccount,
		amount: Decimal | int | float | str,
	) -> None:
		if not isinstance(source_account, BankAccount) or not isinstance(
			target_account, BankAccount
		):
			logger.error("Transfer accounts must be BankAccount instances")
			raise TypeError("Transfer accounts must be BankAccount instances")
		if source_account not in self.__accounts or target_account not in self.__accounts:
			logger.error("Transfer accounts must belong to this customer")
			raise ValueError("Transfer accounts must belong to this customer")
		try:
			source_account.withdraw(amount)
			target_account.deposit(amount)
		except (InsufficientFundsError, ValueError):
			logger.error(
				"Transfer of %s from %s to %s was rejected",
				amount,
				source_account.account_number,
				target_account.account_number,
			)
			raise

	def remove_account(self, account_number: str) -> BankAccount:
		for index, account in enumerate(self.__accounts):
			if account.account_number == account_number:
				return self.__accounts.pop(index)
		raise ValueError("Customer does not own this account")

	@classmethod
	def from_string(cls, customer_data: str) -> Customer:
		"""Create a customer from ``name,birth_date``."""
		parts = [part.strip() for part in customer_data.split(",", maxsplit=1)]
		if len(parts) != 2:
			raise ValueError("Customer data must contain a name and birth date")
		return cls(parts[0], parts[1])

	@staticmethod
	def _generate_user_id() -> int:
		Customer.user_count += 1
		return Customer.user_count

	@staticmethod
	def is_valid_account_number(account_number: str) -> bool:
		return isinstance(account_number, str) and bool(account_number.strip())

	@staticmethod
	def validate_birth_date(birth_date: date | str) -> date:
		if isinstance(birth_date, str):
			try:
				validated_date = date.fromisoformat(birth_date)
			except ValueError:
				raise ValueError("Birth date must be a valid YYYY-MM-DD date") from None
		elif isinstance(birth_date, datetime):
			validated_date = birth_date.date()
		elif isinstance(birth_date, date):
			validated_date = birth_date
		else:
			raise TypeError("Birth date must be a date or ISO date string")

		today = date.today()
		age = today.year - validated_date.year - (
			(today.month, today.day) < (validated_date.month, validated_date.day)
		)
		if age < 18:
			raise ValueError("Customer must be at least 18 years old")
		return validated_date


def configure_logging() -> None:
	"""Configure application logging with timestamps and severity levels."""
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s - %(levelname)s - %(message)s",
	)


logger = logging.getLogger(__name__)
