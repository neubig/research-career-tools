import csv
import subprocess
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
import re
import asyncio
from asyncio import Queue

def load_git_history():
    git_history_cache = {}
    # Get git blame information
    cmd = ['git', 'blame', '--date=iso', 'csrankings.csv']
    blame_output = subprocess.check_output(cmd, cwd='CSrankings', text=True)
    
    # Regex pattern to match the date format in git blame output
    date_pattern = r'\((.*?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+[+-]\d{4})'
    
    for line in blame_output.split('\n'):
        if not line:
            continue
        match = re.search(date_pattern, line)
        if match and len(line.split(')')) > 1:
            date_str = match.group(2)
            fields = line.split(')')[-1].strip().split(',')
            if len(fields) >= 1:
                name = fields[0].strip()
                git_history_cache[name] = date_str
    return git_history_cache


def read_homepage_data():
    homepage_data = {}
    with open('CSrankings/homepage-validated.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                homepage_data[row[0]] = row[1]
    return homepage_data

def read_author_info():
    pub_counts = defaultdict(int)
    author_conferences = defaultdict(set)
    with open('CSrankings/generated-author-info.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 4:
                author_name = row[0].strip()
                conference = row[2].strip()
                try:
                    count = float(row[3])
                    pub_counts[author_name] += count
                    author_conferences[author_name].add(conference)
                except ValueError:
                    continue
    return pub_counts, author_conferences

def read_country_info():
    country_data = {}
    with open('CSrankings/country-info.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                institution = row[0].strip()
                region = row[1].strip()
                country = row[2].strip()
                country_data[institution] = f"{region}-{country}"
    return country_data

async def process_faculty_member(name, affiliation, homepage, homepage_data, pub_counts, conferences, git_history, country_data):
    # Get the last modified date using git log
    added_date = git_history.get(name, '')
    
    # Get publication count and conferences
    pub_count = pub_counts.get(name, 0)
    conf_list = ','.join(sorted(conferences.get(name, set())))
    
    # Get affiliation location
    affiliation_location = country_data.get(affiliation, 'us-us')
    
    return {
        'name': name,
        'affiliation': affiliation,
        'affiliation_location': affiliation_location,
        'added_date': added_date,
        'publication_count': pub_count,
        'conferences': conf_list
    }

async def process_faculty_files():
    faculty_data = []
    homepage_data = read_homepage_data()
    pub_counts, author_conferences = read_author_info()
    country_data = read_country_info()
    
    print("Loading git history...")
    git_history = load_git_history()
    
    # Process the combined csrankings.csv file
    file_path = 'CSrankings/csrankings.csv'
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        rows = list(reader)
    
    # Create tasks for async processing
    tasks = []
    for row in rows:
        if len(row) >= 3:
            name = row[0].strip()
            affiliation = row[1].strip()
            homepage = row[2].strip()
            tasks.append(process_faculty_member(name, affiliation, homepage, homepage_data, 
                                             pub_counts, author_conferences, git_history, country_data))
    
    print(f"Processing {len(tasks)} faculty members...")
    
    # Process faculty members concurrently
    faculty_data = await asyncio.gather(*tasks)
    
    return faculty_data

def write_output(faculty_data):
    with open('faculty_info.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'affiliation', 'affiliation_location', 
                                             'added_date', 'publication_count', 'conferences'])
        writer.writeheader()
        writer.writerows(faculty_data)

async def main():
    faculty_data = await process_faculty_files()
    write_output(faculty_data)
    print(f"Processed {len(faculty_data)} faculty entries")

if __name__ == '__main__':
    asyncio.run(main())
