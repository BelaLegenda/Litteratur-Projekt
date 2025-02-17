from webScrape import extract_metadata

# Define the article link
article_link = "https://www.dr.dk/nyheder/kultur/gamle-tweets-kan-faa-det-hele-til-vaelte-stor-oscar-favorit-men-det-kan-vaere-en"

# Get metadata
metadata = extract_metadata(article_link)

# Print results
for key, value in metadata.items():
    print(f"{key}: {value}")
