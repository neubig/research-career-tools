# Find My Citers

by [Graham Neubig](http://www.phontron.com)

This is a script that helps find people who have cited your papers, which can be useful to find recommendation letter writers for job or visa applications.

It is based on the [Semantic Scholar API](https://api.semanticscholar.org/api-docs/).

## Usage

Find your semantic scholar profile, and copy-paste the number from the URL. For example, if the URL is `https://www.semanticscholar.org/author/Graham-Neubig/1700325` then the number is `1700325`.

```bash
python find_my_citers.py --author_id AUTHOR_ID
```

Optionally, if you have a semantic scholar API key, you can add it to make the process go faster.

```bash
python find_my_citers.py --author_id AUTHOR_ID --s2_api_key API_KEY
```
