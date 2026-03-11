# Sample Data

This directory contains sample data for the AI Support Ticket Helper.

## Files

### tickets.csv
Contains 10 sample support tickets with:
- ticket_id: Unique identifier
- ticket_text: The actual ticket content
- category: Pre-labeled category (for validation)
- created_at: Timestamp

### kb_articles.csv
Contains 10 sample KB articles with:
- article_id: Unique identifier
- title: Article title
- content: Full article content
- category: Article category
- views: Number of views (for analytics)
- clicks: Number of clicks (for CTR calculation)

## Usage

These files are used by:
- `csv_loader.py`: Loads data into the system
- `build_index.py`: Creates embeddings and FAISS index
- `gap_analysis.py`: Analyzes performance metrics

## Customization

You can replace these files with your own data. Just maintain the same CSV structure.
