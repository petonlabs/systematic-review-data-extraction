"""
Progress tracking module for systematic review data extraction.
"""

import sqlite3
import logging
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import TrackingConfig


class ProgressTracker:
    """Track progress of data extraction process."""
    
    def __init__(self, config: TrackingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path = Path(config.database_file)
        
        # Create database
        self._init_database()
        
        self.logger.info(f"Progress tracker initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database for tracking progress."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create articles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        doi TEXT,
                        pmid TEXT,
                        status TEXT,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        full_text_source TEXT,
                        extraction_summary TEXT
                    )
                ''')
                
                # Create extraction_data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extraction_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id TEXT,
                        category TEXT,
                        field_name TEXT,
                        field_value TEXT,
                        extracted_at TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                ''')
                
                # Create processing_log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id TEXT,
                        timestamp TIMESTAMP,
                        event_type TEXT,
                        message TEXT,
                        details TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database tables created/verified")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def is_processed(self, article_id: str) -> bool:
        """Check if article has been successfully processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status FROM articles WHERE id = ?",
                    (article_id,)
                )
                
                result = cursor.fetchone()
                return result is not None and result[0] == 'completed'
                
        except Exception as e:
            self.logger.error(f"Error checking if article {article_id} is processed: {e}")
            return False
    
    def start_processing(self, article_id: str, article_metadata: Dict[str, Any]):
        """Mark article as started processing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, doi, pmid, status, started_at) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    article_metadata.get('title', ''),
                    article_metadata.get('doi', ''),
                    article_metadata.get('pmid', ''),
                    'processing',
                    datetime.now()
                ))
                
                # Log the event
                cursor.execute('''
                    INSERT INTO processing_log 
                    (article_id, timestamp, event_type, message) 
                    VALUES (?, ?, ?, ?)
                ''', (
                    article_id,
                    datetime.now(),
                    'start',
                    'Started processing article'
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error marking article {article_id} as started: {e}")
    
    def log_success(self, article_id: str, extracted_data: Dict[str, Dict[str, str]]):
        """Log successful data extraction."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update article status
                cursor.execute('''
                    UPDATE articles 
                    SET status = ?, completed_at = ?, extraction_summary = ?
                    WHERE id = ?
                ''', (
                    'completed',
                    datetime.now(),
                    json.dumps({k: len(v) for k, v in extracted_data.items()}),
                    article_id
                ))
                
                # Store extracted data
                for category, fields in extracted_data.items():
                    for field_name, field_value in fields.items():
                        cursor.execute('''
                            INSERT INTO extraction_data 
                            (article_id, category, field_name, field_value, extracted_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            article_id,
                            category,
                            field_name,
                            field_value,
                            datetime.now()
                        ))
                
                # Log the success
                cursor.execute('''
                    INSERT INTO processing_log 
                    (article_id, timestamp, event_type, message, details) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    datetime.now(),
                    'success',
                    f'Successfully extracted data for {len(extracted_data)} categories',
                    json.dumps(list(extracted_data.keys()))
                ))
                
                conn.commit()
                self.logger.info(f"Logged success for article {article_id}")
                
        except Exception as e:
            self.logger.error(f"Error logging success for article {article_id}: {e}")
    
    def log_failure(self, article_id: str, error_message: str, full_text_source: str = None):
        """Log failed data extraction."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update article status
                cursor.execute('''
                    UPDATE articles 
                    SET status = ?, error_message = ?, full_text_source = ?
                    WHERE id = ?
                ''', (
                    'failed',
                    error_message,
                    full_text_source or 'unknown',
                    article_id
                ))
                
                # If article doesn't exist, insert it
                if cursor.rowcount == 0:
                    cursor.execute('''
                        INSERT INTO articles 
                        (id, status, error_message, full_text_source, started_at) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        article_id,
                        'failed',
                        error_message,
                        full_text_source or 'unknown',
                        datetime.now()
                    ))
                
                # Log the failure
                cursor.execute('''
                    INSERT INTO processing_log 
                    (article_id, timestamp, event_type, message) 
                    VALUES (?, ?, ?, ?)
                ''', (
                    article_id,
                    datetime.now(),
                    'failure',
                    error_message
                ))
                
                conn.commit()
                self.logger.info(f"Logged failure for article {article_id}")
                
        except Exception as e:
            self.logger.error(f"Error logging failure for article {article_id}: {e}")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of processing progress."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get status counts
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM articles 
                    GROUP BY status
                ''')
                
                status_counts = dict(cursor.fetchall())
                
                # Get total articles
                cursor.execute('SELECT COUNT(*) FROM articles')
                total = cursor.fetchone()[0]
                
                # Get recent failures
                cursor.execute('''
                    SELECT id, error_message, started_at 
                    FROM articles 
                    WHERE status = 'failed'
                    ORDER BY started_at DESC 
                    LIMIT 5
                ''')
                
                recent_failures = [
                    {
                        'id': row[0],
                        'error': row[1],
                        'timestamp': row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
                return {
                    'total_articles': total,
                    'status_counts': status_counts,
                    'completed_percentage': (status_counts.get('completed', 0) / total * 100) if total > 0 else 0,
                    'recent_failures': recent_failures
                }
                
        except Exception as e:
            self.logger.error(f"Error getting progress summary: {e}")
            return {}
    
    def export_results(self, output_path: str, format: str = 'csv'):
        """Export extraction results to file."""
        try:
            output_path = Path(output_path)
            
            with sqlite3.connect(self.db_path) as conn:
                if format.lower() == 'csv':
                    self._export_to_csv(conn, output_path)
                elif format.lower() == 'json':
                    self._export_to_json(conn, output_path)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                self.logger.info(f"Results exported to {output_path}")
                
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            raise
    
    def _export_to_csv(self, conn: sqlite3.Connection, output_path: Path):
        """Export results to CSV format."""
        cursor = conn.cursor()
        
        # Get all extraction data with article metadata
        cursor.execute('''
            SELECT 
                a.id,
                a.title,
                a.doi,
                a.pmid,
                e.category,
                e.field_name,
                e.field_value,
                a.completed_at,
                a.full_text_source
            FROM articles a
            JOIN extraction_data e ON a.id = e.article_id
            WHERE a.status = 'completed'
            ORDER BY a.id, e.category, e.field_name
        ''')
        
        results = cursor.fetchall()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Article ID', 'Title', 'DOI', 'PMID',
                'Category', 'Field Name', 'Field Value',
                'Completed At', 'Full Text Source'
            ])
            
            # Write data
            for row in results:
                writer.writerow(row)
    
    def _export_to_json(self, conn: sqlite3.Connection, output_path: Path):
        """Export results to JSON format."""
        cursor = conn.cursor()
        
        # Get all articles with their extracted data
        cursor.execute('''
            SELECT 
                a.id,
                a.title,
                a.doi,
                a.pmid,
                a.status,
                a.completed_at,
                a.full_text_source,
                a.extraction_summary
            FROM articles a
            ORDER BY a.id
        ''')
        
        articles = []
        for row in cursor.fetchall():
            article_id = row[0]
            
            # Get extraction data for this article
            cursor.execute('''
                SELECT category, field_name, field_value
                FROM extraction_data
                WHERE article_id = ?
                ORDER BY category, field_name
            ''', (article_id,))
            
            extraction_data = {}
            for cat_row in cursor.fetchall():
                category, field_name, field_value = cat_row
                if category not in extraction_data:
                    extraction_data[category] = {}
                extraction_data[category][field_name] = field_value
            
            articles.append({
                'id': row[0],
                'title': row[1],
                'doi': row[2],
                'pmid': row[3],
                'status': row[4],
                'completed_at': row[5],
                'full_text_source': row[6],
                'extraction_summary': json.loads(row[7]) if row[7] else {},
                'extracted_data': extraction_data
            })
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'export_timestamp': datetime.now().isoformat(),
                'total_articles': len(articles),
                'articles': articles
            }, jsonfile, indent=2, ensure_ascii=False)
    
    def log_event(self, article_id: str, event_type: str, message: str, details: str = None):
        """Log a general event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO processing_log 
                    (article_id, timestamp, event_type, message, details) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    datetime.now(),
                    event_type,
                    message,
                    details
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging event for article {article_id}: {e}")
    
    def get_failed_articles(self) -> List[Dict[str, Any]]:
        """Get list of failed articles for retry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, doi, pmid, error_message, started_at
                    FROM articles
                    WHERE status = 'failed'
                    ORDER BY started_at DESC
                ''')
                
                return [
                    {
                        'id': row[0],
                        'title': row[1],
                        'doi': row[2],
                        'pmid': row[3],
                        'error_message': row[4],
                        'started_at': row[5]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting failed articles: {e}")
            return []
    
    def get_processed_articles(self) -> List[str]:
        """Get list of article IDs that have been successfully processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id FROM articles
                    WHERE status = 'completed'
                ''')
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting processed articles: {e}")
            return []
