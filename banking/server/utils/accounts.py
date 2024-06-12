import secrets

_BANK_CODE = "26277228"

def generate_iban(user_id: str, country_code: str = "DE", bank_code: str = _BANK_CODE) -> str:
    """
    Generate a mock IBAN number for a user.

    Args:
        user_id (str): Unique identifier for the user.
        country_code (str): The ISO country code (2 letters). Default is 'DE' for Germany.
        bank_code (str): The bank code (usually a fixed-length string). Default is '12345678'.

    Returns:
        str: The generated IBAN number.
    """

    # Pad the user-specific part to ensure consistent length (e.g., 10 digits)
    user_account_number = user_id.zfill(10)

    # Rearrange to compute checksum
    rearranged_iban = f"{bank_code}{user_account_number}{country_code}00"

    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric_iban = ''.join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged_iban)

    # Calculate the checksum (modulo 97)
    checksum = 98 - (int(numeric_iban) % 97)

    # Create the final IBAN with the calculated checksum
    iban = f"{country_code}{str(checksum).zfill(2)}{bank_code}{user_account_number}"

    return iban


def has_consecutive_repeats(number: int) -> bool:
    """Check if a number has consecutively repeating digits."""
    num_str = str(number)
    return any(num_str[i] == num_str[i + 1] for i in range(len(num_str) - 1))

def generate_unique_ten_digit_number() -> int:
    """Generate a ten-digit number without consecutively repeating digits."""
    while True:
        number = secrets.randbelow(10**10 - 10**9) + 10**9
        if not has_consecutive_repeats(number):
            return number

def generate_user_account_number()->str:
    """ This naive function generates an account number for a user,
       for a real production use case it will be ideal to have indexes
       containing a number of already generated account numbers and 
       already used ones being removed from the index and poping 
       the first item from the index to maintain consistency
       a cloud function or cron tasks with celery, apache airflow
       would suffice for this

    Returns:
        str: user account number
    """
    return str(generate_unique_ten_digit_number())