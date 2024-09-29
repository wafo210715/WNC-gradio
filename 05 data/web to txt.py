import requests
from bs4 import BeautifulSoup
import re
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# The URL from the file
# url = "https://ww3.rics.org/uk/en/modus/built-environment/homes-and-communities/ghost-town-effect-of-second-homes-on-communities.html"
# url = "https://www.chichester.gov.uk/nutrientneutrality"
# url = "https://www.chichester.gov.uk/managingwaterquality"
# url = "https://chichester.oc2.uk/document/54/1363#d1363"
# url = "https://chichester.oc2.uk/document/54/1366#d1366"
# url = "https://chichester.oc2.uk/document/54/1372#d1372"
# url = "https://chichester.oc2.uk/document/54/1375#d1375"
# url = "https://chichester.oc2.uk/document/54/1386#d1386"
# url = "https://chichester.oc2.uk/document/54/1393#d1393"
# url = "https://chichester.oc2.uk/document/54/1394#d1394"
# url = "https://www.chichester.gov.uk/counciltaxsecondhomes"
# url = "https://www.conservancy.co.uk/about-chichester-harbour/habitats/native-oysters/"
# url = "https://www.conservancy.co.uk/about-chichester-harbour/why-ch-special/"
# url = "https://www.conservancy.co.uk/nature-recovery/projects/saltmarsh-restoration-trial-project-west-itchenor/"
# url = "https://www.conservancy.co.uk/coastal-change-footpath-3059/"
url = "https://www.energy.gov/femp/net-zero-water-building-strategies"
# Fetch the webpage content
response = requests.get(url)
html_content = response.text

# Parse the HTML content
soup = BeautifulSoup(html_content, "html.parser")

# Extract the main content (you may need to adjust this based on the webpage structure)
main_content = soup.find("main")  # Assuming the main content is within a <main> tag

# Extract text from the main content
if main_content:
    # Remove script and style elements
    for script in main_content(["script", "style"]):
        script.decompose()

    # Get text and remove extra whitespace
    text = " ".join(main_content.stripped_strings)

    # Remove special characters and extra spaces
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Create the full path for the output file
    output_file = os.path.join(script_dir, "net-zero-water-building-strategies.txt")

    # Write the extracted text to a file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"Content has been extracted and saved to '{output_file}'")
else:
    print("Could not find the main content of the webpage")
