# %%
import requests
import time
import tqdm
import argparse
from collections import defaultdict

s2_api_key: str | None = None


def rate_limited_get(url: str) -> requests.Response:
    global s2_api_key
    headers = {"x-api-key": s2_api_key} if s2_api_key else {}
    response = requests.get(url, headers=headers)
    retries = 0
    while response.status_code == 429 and retries < 3:
        # If we are being rate-limited, wait for a bit and try again
        print(f"Rate limited, waiting {response.headers.get('Retry-After', 3)} seconds")
        retry_after = int(response.headers.get("Retry-After", 3))
        time.sleep(retry_after)
        response = requests.get(url, headers=headers)
        retries += 1
    return response


# Function to get an author's papers from Semantic Scholar
def get_author_papers(author_id: str) -> list[dict]:
    """Fetch papers for a given author ID from Semantic Scholar."""
    papers = []
    url = (
        f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
        "/papers?fields=title,authors,paperId&limit=100"
    )
    response = rate_limited_get(url)
    if response.status_code == 200:
        data = response.json()
        papers.extend(data.get("data", []))
    else:
        print(f"Error fetching papers for author ID {author_id}")
    return papers


def get_citations(paper_id: str) -> list[dict]:
    """Fetch citations for a given paper ID from Semantic Scholar."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=citations"
    response = rate_limited_get(url)
    if response.status_code == 200:
        return response.json().get("citations", [])
    else:
        print(f"Error fetching citations for paper {paper_id}")
        return []


def get_paper_authors(paper_id: str) -> list[dict]:
    """Fetch authors for a given paper ID from Semantic Scholar."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=authors"
    response = rate_limited_get(url)
    authors_list = []
    if response.status_code == 200:
        paper_data = response.json()
        authors = paper_data.get("authors", [])
        for author in authors:
            # Extracting each author's name and author ID
            authors_list.append(
                {"name": author.get("name"), "authorId": author.get("authorId")}
            )
    else:
        print(f"Error fetching authors for paper {paper_id}")
    return authors_list


def find_my_citers(author_id: str) -> list[tuple[str, int]]:

    # Get papers for the author
    your_paper_ids = get_author_papers(author_id)
    citation_counts = defaultdict(int)
    paper_ids_only = [x["paperId"] for x in your_paper_ids]
    for paper_id in tqdm.tqdm(paper_ids_only, desc="Processing papers"):
        citations = get_citations(paper_id)
        for citation in tqdm.tqdm(citations, desc="Processing citations", leave=False):
            authors = get_paper_authors(citation["paperId"])
            for author in authors:
                author_name = author.get("name")
                citation_counts[author_name] += 1

    # Sort authors by citation count
    sorted_citation_counts = sorted(
        citation_counts.items(), key=lambda item: item[1], reverse=True
    )

    return sorted_citation_counts


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Find authors who have cited your work the most"
    )
    parser.add_argument("--author_id", help="The author ID to search for")
    parser.add_argument(
        "--s2_api_key",
        type=str,
        default=None,
        help="An API key for semantic scholar if you have one.",
    )
    args = parser.parse_args()

    s2_api_key = args.s2_api_key
    sorted_citation_counts = find_my_citers(args.author_id)

    # Print out the authors who cited your work the most
    for author, count in sorted_citation_counts:
        print(f"{author}: {count} citations")
