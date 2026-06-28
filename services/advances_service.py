import logging
from datetime import datetime

from translation_manager import TranslationManager
import pandas as pd

from utils.file_utils import load_xlsx, save_xlsx
from utils.storage import ADVANCES_FILE
from utils.time_utils import now_date_str

logger = logging.getLogger(__name__)
translator = TranslationManager.instance()

# Define columns for advances data
COLUMNS = ["UID", "Employee Name", "Amount", "Date", "Note", "Month", "Year"]


def _load_df() -> pd.DataFrame:
    """Load advances data from Excel file."""
    return load_xlsx(ADVANCES_FILE, COLUMNS)


def _save_df(df: pd.DataFrame):
    """Save advances data to Excel file."""
    save_xlsx(ADVANCES_FILE, df)


def get_all_advances() -> pd.DataFrame:
    """Get all advance records."""
    df = _load_df()
    logger.debug("Loaded %d advance records", len(df))
    return df


def add_advance(uid: str, employee_name: str, amount: float, note: str = "") -> tuple[bool, str]:
    """
    Add a new advance record for an employee.
    
    Args:
        uid: Employee UID
        employee_name: Employee full name
        amount: Advance amount
        note: Optional note
        
    Returns:
        Tuple of (success, message)
    """
    try:
        if amount <= 0:
            return False, translator.t("advances.validation.amount_positive")

        df = _load_df()
        
        # Get current date and extract month/year
        date_str = now_date_str()
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.strftime("%B")  # Full month name
        year = date_obj.strftime("%Y")
        
        # Clean UID: remove duplicates and extra spaces
        uid_parts = uid.split()
        uid_clean = uid_parts[0] if uid_parts else uid
        
        # Create new record
        new_record = pd.DataFrame([[uid_clean, employee_name, str(amount), date_str, note, month, year]], columns=COLUMNS)
        
        # Append to existing data
        df = pd.concat([df, new_record], ignore_index=True)
        
        # Save the updated dataframe
        _save_df(df)
        
        logger.info("Advance added for %s (%s): %s", employee_name, uid_clean, amount)
        return True, translator.t(
            "advances.success.recorded",
            amount=f"{amount:.2f}",
            employee_name=employee_name,
        )
        
    except Exception as e:
        logger.error("Error adding advance: %s", str(e))
        return False, translator.t("common.error_occurred", error=str(e))


def delete_advance(index: int) -> tuple[bool, str]:
    """
    Delete an advance record by index.
    
    Args:
        index: Row index to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        df = _load_df()
        
        if index < 0 or index >= len(df):
            return False, translator.t("advances.validation.invalid_index")
        
        employee_name = df.iloc[index]["Employee Name"]
        amount = df.iloc[index]["Amount"]
        
        # Drop the row
        df = df.drop(index)
        df = df.reset_index(drop=True)
        
        # Save the updated dataframe
        _save_df(df)
        
        logger.info("Advance deleted for %s: %s", employee_name, amount)
        return True, translator.t("advances.success.deleted")
        
    except Exception as e:
        logger.error("Error deleting advance: %s", str(e))
        return False, translator.t("common.error_occurred", error=str(e))
