# CSRankings Recent Additions Tracker

This script analyzes the CSRankings database to track recent additions to university faculty members, including their publication counts and research areas.

## Description

The script processes the CSRankings database to extract:

- Faculty member names and affiliations
- When they were added to the database
- Their research areas
- Publication counts

## Prerequisites

- Python 3.6+
- Git

## Installation

First, clone the CSRankings repository (required for data):

```bash
git clone https://github.com/emeryberger/CSrankings.git
```

Second, install required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

First, make sure the CSRankings repository is in the same directory as the script then run it:

```bash
python find_recent_additions.py
```

The script will generate a `faculty_info.csv` file containing:

- Name
- Affiliation
- Research areas
- Date added to CSRankings
- Publication count

## Output Format

The output CSV file contains the following columns:

- `name`: Faculty member's name
- `affiliation`: University affiliation
- `areas`: Research areas
- `added_date`: Date when added to CSRankings
- `publication_count`: Number of publications

## Performance

The script uses multiprocessing to parallelize faculty data processing, utilizing all available CPU cores for improved performance.

## Dependencies

- `csv`: For CSV file handling
- `multiprocessing`: For parallel processing
- `subprocess`: For Git operations
- `tqdm`: For progress bars

## Notes

- The script requires the CSRankings repository to be up-to-date for accurate addition dates
- Git blame is used to determine when entries were added to the database
