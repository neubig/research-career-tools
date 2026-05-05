import argparse
from collections import defaultdict, Counter
import csv
import time
import matplotlib.pyplot as plt
from semanticscholar import SemanticScholar
from tenacity import RetryError
from tqdm import tqdm

sch: SemanticScholar | None = None


def get_author_name(author_id: str) -> str:
    """Fetch the name of the author given the author ID."""
    author_details = sch.get_author(author_id)
    return author_details.name.replace(" ", "_")


def get_author_papers(author_id: str) -> list[dict]:
    """Fetch papers for a given author ID from Semantic Scholar."""
    author = sch.get_author(author_id)
    return [{"title": paper.title, "paperId": paper.paperId} for paper in author.papers]


def get_citations(paper_id: str) -> list[dict]:
    """Fetch citations for a given paper ID from Semantic Scholar."""
    paper_details = sch.get_paper(paper_id)
    return [
        {
            "title": citation.title,
            "paperId": citation.paperId,
            "year": citation.year,
            "authors": citation.authors,
        }
        for citation in paper_details.citations
    ]


def process_citations(papers: list[dict], citation_counts: defaultdict, citation_years: list, desc: str = "Papers") -> list[dict]:
    """Process citations for a list of papers, returning any that failed."""
    failed = []
    for paper in (pbar := tqdm(papers, desc=desc, unit="paper")):
        pbar.set_postfix_str(f"fetching: {paper['title'][:40]}")
        try:
            citations = get_citations(paper["paperId"])
        except RetryError:
            tqdm.write(f"Rate limit exceeded for '{paper['title']}', will retry.")
            failed.append(paper)
            time.sleep(10)
            continue
        for citation in tqdm(
            citations, desc=paper["title"][:50], unit="citation", leave=False
        ):
            for author in citation["authors"]:
                author_name = (
                    author.get("name") if isinstance(author, dict) else author.name
                )
                citation_counts[author_name] += 1
            if citation["year"] is not None:
                citation_years.append(citation["year"])
        time.sleep(1)
    return failed


def find_my_citers(author_id: str) -> list[tuple[str, int]]:
    your_paper_ids = get_author_papers(author_id)
    citation_counts = defaultdict(int)
    citation_years = []

    failed = process_citations(your_paper_ids, citation_counts, citation_years)
    if failed:
        tqdm.write(f"\nRetrying {len(failed)} failed paper(s) after a cooldown...")
        time.sleep(60)
        still_failed = process_citations(failed, citation_counts, citation_years, desc="Retrying")
        if still_failed:
            tqdm.write(f"Warning: {len(still_failed)} paper(s) permanently skipped due to rate limits: "
                       + ", ".join(p["title"] for p in still_failed))

    sorted_citation_counts = sorted(
        citation_counts.items(), key=lambda item: item[1], reverse=True
    )

    return sorted_citation_counts, citation_years


def export_citation_data(sorted_citation_counts, author_name):
    """Export citation data to a CSV file named after the author."""
    filename = f"{author_name}_citation_data.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Author", "Citation Count"])
        writer.writerows(sorted_citation_counts)
    print(f"Citation data exported to {filename}")
    return filename


def plot_citation_trends(citation_years, author_name):
    """Create and save a time-series plot of citation trends over time."""
    year_counts = Counter(citation_years)
    years = sorted(year_counts.keys())
    counts = [year_counts[year] for year in years]

    plt.figure(figsize=(10, 6))
    plt.plot(years, counts, marker="o")
    plt.title(f"Citation Trends Over Time for {author_name}")
    plt.xlabel("Year")
    plt.ylabel("Number of Citations")
    plt.tight_layout()
    plot_filename = f"{author_name}_citation_trends.png"
    plt.savefig(plot_filename)
    plt.close()
    print(f"Citation trend plot saved as {plot_filename}")
    return plot_filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find authors who have cited your work the most using PyS2"
    )
    parser.add_argument(
        "--author_id",
        help=(
            "The author ID to search for. "
            "If not provided, the script will prompt for input."
        ),
        default=None,
    )
    parser.add_argument(
        "--s2_api_key",
        type=str,
        default=None,
        help="An API key for semantic scholar if you have one.",
    )

    args = parser.parse_args()
    sch = SemanticScholar(api_key=args.s2_api_key)

    if args.author_id is None:
        author_id = input("Enter the author ID: ")
    else:
        author_id = args.author_id

    author_name = get_author_name(author_id)
    sorted_citation_counts, citation_years = find_my_citers(author_id)
    csv_filename = export_citation_data(sorted_citation_counts, author_name)
    plot_filename = plot_citation_trends(citation_years, author_name)
