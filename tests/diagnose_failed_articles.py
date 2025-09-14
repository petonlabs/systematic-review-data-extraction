#!/usr/bin/env python3
"""
Diagnostic tool to analyze failed articles and identify patterns or issues.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient
from src.progress_tracker import ProgressTracker


async def diagnose_failed_articles():
    """Analyze failed articles to understand why they're failing."""
    print("🔍 Diagnosing Failed Articles")
    print("=" * 50)
    
    try:
        # Initialize components
        config = Config()
        progress_tracker = ProgressTracker(config.tracking_config)
        sheets_client = SheetsClient(config.sheets_config)
        
        # Get progress summary to identify failed articles
        progress = progress_tracker.get_progress_summary()
        print(f"📊 Overall Stats:")
        print(f"   Total articles: {progress['total_articles']}")
        print(f"   Completed: {progress['status_counts'].get('completed', 0)}")
        print(f"   Failed: {progress['status_counts'].get('failed', 0)}")
        print(f"   Success rate: {progress['completed_percentage']:.1f}%")
        
        # Get all failed articles
        failed_articles = progress_tracker.get_failed_articles()
        print(f"\n❌ Failed Articles ({len(failed_articles)}):")
        print("=" * 50)
        
        # Get all articles from sheets to cross-reference
        all_articles = await sheets_client.get_articles()
        articles_by_id = {str(i+1): article for i, article in enumerate(all_articles)}
        
        # Analyze each failed article
        failure_patterns = {
            'no_doi': 0,
            'invalid_url': 0,
            'no_abstract': 0,
            'short_title': 0,
            'old_articles': 0,
            'non_english': 0,
            'conference_abstracts': 0
        }
        
        print(f"{'ID':<4} {'Year':<6} {'Title':<50} {'DOI/URL':<30} {'Issue'}")
        print("-" * 120)
        
        for failed in failed_articles:
            article_id = failed['id']
            if article_id in articles_by_id:
                article = articles_by_id[article_id]
                
                # Extract key information
                title = article.get('title', '')[:47] + '...' if len(article.get('title', '')) > 50 else article.get('title', 'No title')
                year = article.get('publication_year', article.get('date', 'Unknown'))
                doi = article.get('doi', 'No DOI')
                url = article.get('url', 'No URL')
                abstract = article.get('abstract_note', '')
                
                # Diagnose potential issues
                issues = []
                
                # Check for missing or problematic DOI/URL
                if not doi or doi == 'No DOI':
                    if not url or url == 'No URL' or 'pubmed' not in url.lower():
                        issues.append('No valid DOI/URL')
                        failure_patterns['invalid_url'] += 1
                    else:
                        failure_patterns['no_doi'] += 1
                
                # Check abstract length
                if len(abstract) < 50:
                    issues.append('Short/no abstract')
                    failure_patterns['no_abstract'] += 1
                
                # Check title length
                if len(title) < 20:
                    issues.append('Short title')
                    failure_patterns['short_title'] += 1
                
                # Check publication year
                try:
                    pub_year = int(year) if str(year).isdigit() else 0
                    if pub_year < 2010:
                        issues.append('Old article')
                        failure_patterns['old_articles'] += 1
                except:
                    pass
                
                # Check if it's a conference abstract
                pub_title = article.get('publication_title', '').lower()
                if any(term in pub_title for term in ['conference', 'abstract', 'meeting', 'symposium']):
                    issues.append('Conference abstract')
                    failure_patterns['conference_abstracts'] += 1
                
                # Display the article info
                issue_text = ', '.join(issues) if issues else failed.get('error_message', 'Unknown error')
                doi_display = doi[:27] + '...' if len(doi) > 30 else doi
                
                print(f"{article_id:<4} {year:<6} {title:<50} {doi_display:<30} {issue_text}")
                
                # Show detailed info for first few failures
                if int(article_id) <= 36 and int(article_id) >= 32:  # Last few that failed
                    print(f"    📄 Full Title: {article.get('title', 'N/A')}")
                    print(f"    🔗 DOI: {doi}")
                    print(f"    🌐 URL: {url}")
                    print(f"    📝 Abstract Length: {len(abstract)} chars")
                    print(f"    📰 Publication: {article.get('publication_title', 'N/A')}")
                    print(f"    🏷️  Item Type: {article.get('item_type', 'N/A')}")
                    print()
        
        # Summary of failure patterns
        print("\n📈 Failure Pattern Analysis:")
        print("=" * 50)
        for pattern, count in failure_patterns.items():
            if count > 0:
                percentage = (count / len(failed_articles)) * 100
                print(f"   {pattern.replace('_', ' ').title():<20}: {count:>3} articles ({percentage:.1f}%)")
        
        # Recommendations
        print("\n💡 Recommendations:")
        print("=" * 50)
        if failure_patterns['no_doi'] > 0 or failure_patterns['invalid_url'] > 0:
            print("   1. 🔗 Implement alternative article fetching methods")
            print("      - Try CrossRef API for DOI resolution")
            print("      - Add ArXiv support for preprints")
            print("      - Improve URL parsing and validation")
        
        if failure_patterns['no_abstract'] > 0:
            print("   2. 📝 Enhanced metadata extraction")
            print("      - Extract text from title + keywords if no abstract")
            print("      - Use Google Scholar API as fallback")
        
        if failure_patterns['conference_abstracts'] > 0:
            print("   3. 📊 Conference abstract handling")
            print("      - Special processing for conference abstracts")
            print("      - Different extraction strategy for limited content")
        
        print("\n✅ Diagnostic complete!")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose_failed_articles())
