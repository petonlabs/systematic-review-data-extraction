"""
Google Sheets client for systematic review data extraction.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import SheetsConfig


class SheetsClient:
    """Client for interacting with Google Sheets API."""
    
    def __init__(self, config: SheetsConfig):
        self.config = config
        self.service = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Sheet names as they EXACTLY appear in Google Sheets (from test_setup.py)
        self.sheet_names = {
            'articles': 'articles',
            'study_characteristics': 'Study Characteristics',
            'population_characteristics': 'Population Characteristics', 
            'interventions': 'Interventions & Comparators',
            'primary_outcomes': 'Primary Outcomes (SSI Epidemiology & AMR)',
            'secondary_outcomes': 'Secondary Outcomes (Clinical & Economic Impact)',
            'drivers': 'Drivers, Innovations & Policy Context'
        }
        
        # Safe sheet name mappings for API calls - use exact names from Google Sheets  
        self.safe_sheet_names = {
            'study_characteristics': 'Study Characteristics',
            'population_characteristics': 'Population Characteristics', 
            'interventions': 'Interventions & Comparators',
            'primary_outcomes': 'Primary Outcomes (SSI Epidemiology & AMR)',
            'secondary_outcomes': 'Secondary Outcomes (Clinical & Economic Impact)',
            'drivers': 'Drivers, Innovations & Policy Context'
        }
    
    def _get_safe_sheet_name(self, sheet_name: str) -> str:
        """Convert sheet name to Google Sheets API safe format using exact names."""
        # Use exact sheet names as they appear in Google Sheets
        exact_mappings = {
            'Study Characteristics': 'Study Characteristics',
            'Population Characteristics': 'Population Characteristics',
            'Interventions & Comparators': 'Interventions & Comparators',
            'Primary Outcomes (SSI Epidemiology & AMR)': 'Primary Outcomes (SSI Epidemiology & AMR)',
            'Secondary Outcomes (Clinical & Economic Impact)': 'Secondary Outcomes (Clinical & Economic Impact)',
            'Drivers, Innovations & Policy Context': 'Drivers, Innovations & Policy Context'
        }
        
        # Return exact name if found
        if sheet_name in exact_mappings:
            return exact_mappings[sheet_name]
        
        # For any other sheet names, return as-is (no quotes needed for most cases)
        return sheet_name
        
    async def authenticate(self) -> bool:
        """Authenticate with Google Sheets API using OAuth or Service Account."""
        creds = None
        
        # First try service account authentication
        service_account_path = Path("service-account.json")
        if service_account_path.exists():
            try:
                creds = ServiceAccountCredentials.from_service_account_file(
                    str(service_account_path), scopes=self.config.scopes)
                self.logger.info("Using service account authentication")
            except Exception as e:
                self.logger.warning(f"Service account auth failed: {e}")
                creds = None
        
        # Fall back to OAuth if no service account
        if not creds:
            # Check if token file exists
            token_path = Path(self.config.token_file)
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), self.config.scopes)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        self.logger.error(f"Failed to refresh credentials: {e}")
                        return False
                else:
                    credentials_path = Path(self.config.credentials_file)
                    if not credentials_path.exists():
                        self.logger.error(f"Credentials file not found: {credentials_path}")
                        self.logger.info("Please download credentials.json from Google Cloud Console")
                        self.logger.info("Or place service-account.json for service account authentication")
                        return False
                    
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(credentials_path), self.config.scopes)
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        self.logger.error(f"Authentication failed: {e}")
                        return False
                
                # Save credentials for next run
                if hasattr(creds, 'to_json'):  # OAuth credentials
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            self.logger.info("Successfully authenticated with Google Sheets API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to build service: {e}")
            return False
    
    async def get_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from the Google Sheets."""
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Sheets")
        
        try:
            # Get data from articles sheet
            sheet_range = f"{self.sheet_names['articles']}!A:Z"  # Adjust range as needed
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.spreadsheet_id,
                range=sheet_range
            ).execute()
            
            values = result.get('values', [])
            if not values:
                self.logger.warning("No data found in articles sheet")
                return []
            
            # Convert to list of dictionaries
            headers = values[0] if values else []
            articles = []
            
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                # Pad row to match header length
                while len(row) < len(headers):
                    row.append('')
                
                article = {
                    'row_number': i,
                    'id': str(i),  # Use row number as ID
                }
                
                for j, header in enumerate(headers):
                    article[header.lower().replace(' ', '_')] = row[j] if j < len(row) else ''
                
                # Only include articles with DOI, PMID, or URL
                has_doi = bool(article.get('doi', '').strip())
                has_pmid = bool(article.get('pmid', '').strip())
                has_url = bool(article.get('url', '').strip())
                
                if has_doi or has_pmid or has_url:
                    articles.append(article)
                else:
                    self.logger.warning(f"Article in row {i} has no DOI, PMID, or URL, skipping")
            
            self.logger.info(f"Found {len(articles)} articles with DOI/PMID")
            return articles
            
        except HttpError as e:
            self.logger.error(f"Google Sheets API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching articles: {e}")
            raise
    
    async def get_sheet_headers(self, sheet_name: str) -> List[str]:
        """Get headers for a specific sheet with safe name handling."""
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Sheets")
        
        try:
            # Use safe sheet name for API call
            safe_name = self._get_safe_sheet_name(sheet_name)
            range_name = f"{safe_name}!1:1"
            
            self.logger.debug(f"Requesting headers for sheet: {sheet_name} -> {range_name}")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            headers = values[0] if values else []
            
            if headers:
                self.logger.info(f"Found {len(headers)} headers for sheet {sheet_name}")
            else:
                self.logger.warning(f"No headers found for sheet {sheet_name}")
                
            return headers
            
        except HttpError as e:
            self.logger.error(f"Error getting headers for {sheet_name}: {e}")
            self.logger.warning(f"No headers found for sheet {sheet_name}")
            return []
    
    async def get_headers(self, sheet_name: str) -> List[str]:
        """Alias for get_sheet_headers for backward compatibility."""
        return await self.get_sheet_headers(sheet_name)
    
    async def update_extracted_data(self, article_id: str, extracted_data: Dict[str, Any]):
        """Update Google Sheets with extracted data using smart column mapping."""
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Sheets")
        
        updates = []
        
        for sheet_key, data in extracted_data.items():
            if sheet_key in self.sheet_names and data:
                sheet_name = self.sheet_names[sheet_key]
                
                try:
                    # Get headers for this sheet
                    headers = await self.get_sheet_headers(sheet_name)
                    if not headers:
                        self.logger.warning(f"No headers found for sheet {sheet_name}")
                        continue
                    
                    # Find the row for this article
                    row_number = int(article_id)
                    
                    # Smart column mapping - only update columns we have data for
                    column_updates = []
                    
                    for data_key, data_value in data.items():
                        if not data_value:  # Skip empty values
                            continue
                            
                        # Find matching column in sheet headers
                        matched_column = None
                        matched_index = None
                        
                        # Try exact match first
                        if data_key in headers:
                            matched_column = data_key
                            matched_index = headers.index(data_key)
                        else:
                            # Try flexible matching (case insensitive, handle underscores)
                            data_key_normalized = data_key.lower().replace('_', ' ')
                            for i, header in enumerate(headers):
                                header_normalized = header.lower()
                                if (data_key_normalized == header_normalized or 
                                    data_key_normalized in header_normalized or
                                    header_normalized in data_key_normalized):
                                    matched_column = header
                                    matched_index = i
                                    break
                        
                        if matched_column and matched_index is not None:
                            # Convert column index to Excel column letter
                            column_letter = chr(ord('A') + matched_index)
                            range_name = f"{sheet_name}!{column_letter}{row_number}"
                            
                            column_updates.append({
                                'range': range_name,
                                'values': [[str(data_value)]],
                                'majorDimension': 'ROWS'
                            })
                            
                            self.logger.debug(f"Mapped '{data_key}' -> '{matched_column}' (column {column_letter})")
                        else:
                            self.logger.warning(f"No matching column found for '{data_key}' in sheet '{sheet_name}'")
                    
                    updates.extend(column_updates)
                    self.logger.info(f"Prepared {len(column_updates)} column updates for {sheet_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error preparing update for {sheet_name}: {e}")
                    continue
        
        # Batch update all sheets
        if updates:
            try:
                body = {
                    'valueInputOption': 'RAW',
                    'data': updates
                }
                
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.config.spreadsheet_id,
                    body=body
                ).execute()
                
                self.logger.info(f"Successfully updated {len(updates)} cells across sheets for article {article_id}")
                return True
                
            except HttpError as e:
                self.logger.error(f"Error updating sheets: {e}")
                return False
        else:
            self.logger.info(f"No data to update for article {article_id}")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Google Sheets."""
        try:
            if not self.service:
                if not await self.authenticate():
                    return False
            
            # Try to get spreadsheet metadata
            metadata = self.service.spreadsheets().get(
                spreadsheetId=self.config.spreadsheet_id
            ).execute()
            
            self.logger.info(f"Successfully connected to spreadsheet: {metadata.get('properties', {}).get('title', 'Unknown')}")
            
            # List all sheets
            sheets = metadata.get('sheets', [])
            self.logger.info(f"Found {len(sheets)} sheets:")
            for sheet in sheets:
                title = sheet.get('properties', {}).get('title', 'Unknown')
                self.logger.info(f"  - {title}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
