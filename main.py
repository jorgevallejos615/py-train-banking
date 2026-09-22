from src.banking import configure_logging, logger


def main():
    configure_logging()
    logger.info("Banking application started")
    logger.error("Example banking error")
    print("Hello from python-banking-app!")


if __name__ == "__main__":
    main()
