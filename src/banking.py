import logging


class InsufficientFundsError(Exception):
	def __init__(self, message: str, amount: float) -> None:
		super().__init__(message)
		self.amount = amount


def configure_logging() -> None:
	"""Configure application logging with timestamps and severity levels."""
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s - %(levelname)s - %(message)s",
	)


logger = logging.getLogger(__name__)
