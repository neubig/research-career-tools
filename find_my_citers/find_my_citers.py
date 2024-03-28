import argparse
from collections import defaultdict, Counter
import csv
import matplotlib.pyplot as plt
from requests import Session
import s2

s2_api_key: str | None = None


def get_author_name(author_id: str) -> str:
    """Fetch the name of the author given the author ID."""
    author_details = s2.api.get_author(authorId=author_id, session=session)
    return author_details.name.replace(" ", "_")


def get_author_papers(author_id: str) -> list[dict]:
    """Fetch papers for a given author ID from Semantic Scholar using PyS2."""
    author_papers = s2.api.get_author(authorId=author_id, session=session).papers
    return [{"title": paper.title, "paperId": paper.paperId} for paper in author_papers]


def get_citations(paper_id: str) -> list[dict]:
    """Fetch citations for a given paper ID from Semantic Scholar using PyS2."""
    paper_details = s2.api.get_paper(paperId=paper_id, session=session)
    return [
        {"title": citation.title, "paperId": citation.paperId, "year": citation.year}
        for citation in paper_details.citations
    ]


def get_paper_authors(paper_id: str) -> list[dict]:
    """Fetch authors for a given paper ID from Semantic Scholar using PyS2."""
    paper_details = s2.api.get_paper(paperId=paper_id, session=session)
    return [
        {"name": author.name, "authorId": author.authorId}
        for author in paper_details.authors
    ]


def find_my_citers(author_id: str) -> list[tuple[str, int]]:
    your_paper_ids = get_author_papers(author_id)
    citation_counts = defaultdict(int)
    citation_years = []
    total_papers = len(your_paper_ids)
    processed_papers = 0

    for paper in your_paper_ids:
        citations = get_citations(paper["paperId"])
        print(f"Processing paper {paper['title']}")
        for citation in citations:
            print(f"Processing citation {citation['title']}")
            if "paperId" in citation:
                authors = get_paper_authors(citation["paperId"])
                for author in authors:
                    author_name = author.get("name")
                    citation_counts[author_name] += 1
                citation_years.append(citation["year"])

        processed_papers += 1
        print(f"Processed paper {processed_papers} of {total_papers}")

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
    s2_api_key = args.s2_api_key
    session = Session()
    if s2_api_key:
        session.headers.update({"x-api-key": s2_api_key})

    if args.author_id is None:
        author_id = input("Enter the author ID: ")
    else:
        author_id = args.author_id

    author_name = get_author_name(author_id)
    sorted_citation_counts, citation_years = find_my_citers(author_id)
    csv_filename = export_citation_data(sorted_citation_counts, author_name)
    plot_filename = plot_citation_trends(citation_years, author_name)
