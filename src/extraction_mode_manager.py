"""
Extraction mode manager to handle selection between web-based and PDF-based extraction methods.
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from .config import Config


class ExtractionMethod(Enum):
    """Available extraction methods."""
    WEB_BASED = "web_based"
    PDF_BASED = "pdf_based"


@dataclass
class ExtractionState:
    """State information for extraction process."""
    method: ExtractionMethod
    last_used: str  # ISO timestamp
    pdf_storage_enabled: bool = False
    resume_from_article_id: Optional[str] = None
    total_articles_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    notes: str = ""


class ExtractionModeManager:
    """Manage extraction method selection and state persistence."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_file = Path("extraction_state.json")
        self._current_state: Optional[ExtractionState] = None
    
    def load_state(self) -> Optional[ExtractionState]:
        """Load extraction state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Convert method string back to enum
                method = ExtractionMethod(data['method'])
                
                state = ExtractionState(
                    method=method,
                    last_used=data['last_used'],
                    pdf_storage_enabled=data.get('pdf_storage_enabled', False),
                    resume_from_article_id=data.get('resume_from_article_id'),
                    total_articles_processed=data.get('total_articles_processed', 0),
                    successful_extractions=data.get('successful_extractions', 0),
                    failed_extractions=data.get('failed_extractions', 0),
                    notes=data.get('notes', '')
                )
                
                self._current_state = state
                self.logger.info(f"Loaded extraction state: {state.method.value}")
                return state
            
        except Exception as e:
            self.logger.error(f"Error loading extraction state: {e}")
        
        return None
    
    def save_state(self, state: ExtractionState) -> bool:
        """Save extraction state to file."""
        try:
            # Convert enum to string for JSON serialization
            state_dict = asdict(state)
            state_dict['method'] = state.method.value
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
            
            self._current_state = state
            self.logger.info(f"Saved extraction state: {state.method.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving extraction state: {e}")
            return False
    
    def get_current_method(self) -> Optional[ExtractionMethod]:
        """Get the currently configured extraction method."""
        state = self.load_state()
        return state.method if state else None
    
    def set_method(
        self, 
        method: ExtractionMethod, 
        pdf_storage_enabled: bool = False,
        notes: str = ""
    ) -> bool:
        """Set the extraction method and save state."""
        from datetime import datetime, timezone
        
        try:
            state = ExtractionState(
                method=method,
                last_used=datetime.now(timezone.utc).isoformat(),
                pdf_storage_enabled=pdf_storage_enabled,
                notes=notes
            )
            
            return self.save_state(state)
            
        except Exception as e:
            self.logger.error(f"Error setting extraction method: {e}")
            return False
    
    def update_progress(
        self, 
        total_processed: int = 0,
        successful: int = 0, 
        failed: int = 0,
        resume_from: Optional[str] = None
    ) -> bool:
        """Update progress information in the current state."""
        try:
            current_state = self.load_state()
            if not current_state:
                self.logger.warning("No current state found, cannot update progress")
                return False
            
            # Update progress counters
            if total_processed > 0:
                current_state.total_articles_processed = total_processed
            if successful > 0:
                current_state.successful_extractions = successful
            if failed > 0:
                current_state.failed_extractions = failed
            if resume_from:
                current_state.resume_from_article_id = resume_from
            
            # Update timestamp
            from datetime import datetime, timezone
            current_state.last_used = datetime.now(timezone.utc).isoformat()
            
            return self.save_state(current_state)
            
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
            return False
    
    def choose_method_interactively(self) -> Optional[ExtractionMethod]:
        """Interactive method selection (for CLI usage)."""
        print("\n" + "="*60)
        print("EXTRACTION METHOD SELECTION")
        print("="*60)
        
        print("\nAvailable extraction methods:")
        print("1. Web-based extraction (current method)")
        print("   - Fetches articles directly from web sources")
        print("   - Uses DOI resolution, Unpaywall, CrossRef, etc.")
        print("   - Faster for articles with accessible full text")
        
        print("\n2. PDF-based extraction (new method)")
        print("   - Downloads and stores PDFs in Cloudflare R2")
        print("   - Extracts text from PDFs locally")
        print("   - Better for systematic archiving and offline processing")
        print("   - Requires Cloudflare R2 configuration")
        
        print("\nCurrent state:")
        current_state = self.load_state()
        if current_state:
            print(f"   Last method used: {current_state.method.value}")
            print(f"   Last used: {current_state.last_used}")
            if current_state.total_articles_processed > 0:
                success_rate = (current_state.successful_extractions / 
                              current_state.total_articles_processed * 100)
                print(f"   Progress: {current_state.total_articles_processed} processed, "
                      f"{success_rate:.1f}% success rate")
        else:
            print("   No previous extraction state found")
        
        while True:
            try:
                choice = input("\nSelect method (1 for web-based, 2 for PDF-based, Enter for default): ").strip()
                
                if choice == "" or choice == "1":
                    method = ExtractionMethod.WEB_BASED
                    pdf_storage = False
                    break
                elif choice == "2":
                    method = ExtractionMethod.PDF_BASED
                    
                    # Ask about PDF storage
                    storage_choice = input("Enable PDF storage in Cloudflare R2? (y/N): ").strip().lower()
                    pdf_storage = storage_choice in ['y', 'yes']
                    
                    if pdf_storage:
                        # Validate R2 configuration
                        if not self._validate_r2_config():
                            print("❌ Cloudflare R2 is not properly configured.")
                            print("Please check your .env file for R2 credentials.")
                            continue
                    break
                else:
                    print("Please enter 1 or 2, or press Enter for default.")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None
        
        # Save the choice
        notes = f"Method selected interactively on {current_state.last_used if current_state else 'first run'}"
        if self.set_method(method, pdf_storage, notes):
            print(f"\n✅ Selected method: {method.value}")
            if pdf_storage:
                print("✅ PDF storage enabled")
            return method
        else:
            print("\n❌ Failed to save method selection")
            return None
    
    def _validate_r2_config(self) -> bool:
        """Validate Cloudflare R2 configuration."""
        try:
            r2_config = getattr(self.config, 'r2_config', None)
            if not r2_config:
                return False
            
            required_fields = ['endpoint_url', 'access_key_id', 'secret_access_key', 'bucket_name']
            for field in required_fields:
                if not getattr(r2_config, field, None):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating R2 config: {e}")
            return False
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current extraction progress."""
        state = self.load_state()
        
        if not state:
            return {
                'method': 'none',
                'total_processed': 0,
                'success_rate': 0.0,
                'status': 'not_started'
            }
        
        success_rate = 0.0
        if state.total_articles_processed > 0:
            success_rate = (state.successful_extractions / state.total_articles_processed) * 100
        
        return {
            'method': state.method.value,
            'last_used': state.last_used,
            'total_processed': state.total_articles_processed,
            'successful': state.successful_extractions,
            'failed': state.failed_extractions,
            'success_rate': success_rate,
            'pdf_storage_enabled': state.pdf_storage_enabled,
            'resume_from': state.resume_from_article_id,
            'notes': state.notes,
            'status': 'in_progress' if state.resume_from_article_id else 'completed'
        }
    
    def reset_state(self) -> bool:
        """Reset extraction state (useful for starting over)."""
        try:
            import time
            
            if self.state_file.exists():
                backup_name = f"extraction_state_backup_{int(time.time())}.json"
                self.state_file.rename(backup_name)
                self.logger.info(f"Backed up state to {backup_name}")
            
            self._current_state = None
            self.logger.info("Extraction state reset")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting state: {e}")
            return False
    
    def is_pdf_method_available(self) -> bool:
        """Check if PDF-based extraction is available and configured."""
        try:
            # Check if required dependencies are available
            from .pdf_processor import PdfProcessor
            from .cloudflare_r2 import CloudflareR2Storage
            
            # Check configuration
            return self._validate_r2_config()
            
        except ImportError as e:
            self.logger.warning(f"PDF method dependencies not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking PDF method availability: {e}")
            return False