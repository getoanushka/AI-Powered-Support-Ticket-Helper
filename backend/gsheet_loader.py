import os
import pandas as pd
from typing import Optional
from pathlib import Path

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    _HAS_GSPREAD = True
except Exception:
    _HAS_GSPREAD = False

class GSheetLoader:
    def __init__(self, creds_json_path: Optional[str] = None, sheet_key: Optional[str] = None):
        """
        Load tickets from Google Sheets using a service account JSON key.
        If `gspread` or credentials are not available, falls back to raising an informative error.
        """
        self.creds_json_path = creds_json_path or os.getenv('GSPREAD_CREDS_JSON')
        self.sheet_key = sheet_key or os.getenv('GSPREAD_SHEET_KEY')

        if not _HAS_GSPREAD:
            raise RuntimeError('gspread or oauth2client not installed. Install gspread and oauth2client to use Google Sheets loader.')

        if not self.creds_json_path:
            raise ValueError('Service account JSON path not provided. Set GSPREAD_CREDS_JSON in .env or pass creds_json_path.')

        if not Path(self.creds_json_path).exists():
            raise FileNotFoundError(f'Service account file not found: {self.creds_json_path}')

    def _authorize(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_json_path, scopes=scope)
        client = gspread.authorize(creds)
        return client

    def load_sheet_as_df(self, worksheet_name: str = None) -> pd.DataFrame:
        client = self._authorize()
        sh = client.open_by_key(self.sheet_key)
        worksheet = sh.sheet1 if worksheet_name is None else sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df

    def save_sheet_to_csv(self, out_csv_path: str, worksheet_name: str = None):
        df = self.load_sheet_as_df(worksheet_name)
        df.to_csv(out_csv_path, index=False)
        return out_csv_path
