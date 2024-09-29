import requests
from bs4 import BeautifulSoup
import re
import os
import time


def clean_filename(filename):
    # Remove invalid characters and replace spaces with underscores
    return re.sub(r"[^\w\-_\. ]", "", filename).replace(" ", "_")


def extract_content(url, output_filename):
    try:
        # Fetch the webpage content
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        html_content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the main content (you may need to adjust this based on the webpage structure)
        main_content = soup.find("main") or soup.find(
            "body"
        )  # Fallback to body if main not found

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

            # Write the extracted text to a file
            with open(output_filename, "w", encoding="utf-8") as file:
                file.write(text)

            print(f"Content has been extracted and saved to '{output_filename}'")
            return True
        else:
            print(f"Could not find the main content of the webpage: {url}")
            return False
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return False


# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# List of URLs and their corresponding names
url_list = [
    (
        "Cooper, E. (2022)",
        "https://www.conservancy.co.uk/coastal-change-footpath-3059/",
    ),
    (
        "Department for Environment, Food & Rural Affairs (2018)",
        "https://www.gov.uk/government/publications/25-year-environment-plan",
    ),
    (
        "Department for Environment, Food & Rural Affairs and Natural England (2020)",
        "https://www.gov.uk/government/publications/nature-recovery-network",
    ),
    (
        "Department for Environment, Food & Rural Affairs and Rural Payments Agency (2024)",
        "https://www.gov.uk/find-funding-for-land-or-farms/bfs1-12m-to-24m-watercourse-buffer-strip-on-cultivated-land",
    ),
    (
        "Department for Levelling Up, Housing & Communities (2023)",
        "https://www.gov.uk/government/statistics/english-housing-survey-2021-to-2022-second-homes-fact-sheet/english-housing-survey-2021-to-2022-second-homes-fact-sheet",
    ),
    (
        "Department of Energy (2023)",
        "https://www.energy.gov/femp/net-zero-water-building-strategies",
    ),
    (
        "Department of the Environment (2023)",
        "https://www.ofwat.gov.uk/wp-content/uploads/2017/03/Portsmouth-Consolidated-Appointment.pdf",
    ),
    (
        "Dunn, K. and Castle, V. (2024)",
        "https://www.bbc.co.uk/news/articles/c514jxe8782o",
    ),
    (
        "Environment Agency (2009a)",
        "https://www.gov.uk/government/publications/delivering-water-neutrality-measures-and-funding-strategies",
    ),
    (
        "Environment Agency (2009b)",
        "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/291675/scho1009bqzr-e-e.pdf",
    ),
    (
        "Environment Agency (2018)",
        "https://www.legislation.gov.uk/uksi/2017/407/contents/made",
    ),
    (
        "Environment Agency (2020a)",
        "https://www.gov.uk/government/publications/environment-agency-strategy-for-safe-and-sustainable-sludge-use/environment-agency-strategy-for-safe-and-sustainable-sludge-use",
    ),
    (
        "Environment Agency (2020b)",
        "https://www.gov.uk/government/publications/meeting-our-future-water-needs-a-national-framework-for-water-resources",
    ),
    (
        "Environment Agency (2021a)",
        "https://www.gov.uk/government/news/lack-of-water-presents-existential-threat-says-environment-agency-chief",
    ),
    (
        "Environment Agency (2021b)",
        "https://www.gov.uk/government/publications/mine-waters-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2021c)",
        "https://www.gov.uk/government/publications/nitrates-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2021d)",
        "https://www.gov.uk/government/publications/physical-modifications-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2021e)",
        "https://www.gov.uk/government/publications/pollution-from-water-industry-wastewater-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2021f)",
        "https://www.gov.uk/government/publications/towns-cities-and-transport-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2021g)",
        "https://www.gov.uk/government/publications/water-levels-and-flows-challenges-for-the-water-environment",
    ),
    (
        "Environment Agency (2022a)",
        "https://www.gov.uk/government/publications/river-basin-management-plans-updated-2022-challenges-for-the-water-environment/river-basin-management-plans-updated-2022-challenges-for-the-water-environment#contents",
    ),
    (
        "Environment Agency (2022b)",
        "https://www.gov.uk/government/publications/river-basin-management-plans-updated-2022-challenges-for-the-water-environment/river-basin-management-plans-updated-2022-challenges-for-the-water-environment#pollution-from-agriculture-and-rural-areas",
    ),
    (
        "Environment Agency and Department for Environment, Food & Rural Affairs (2022)",
        "https://www.gov.uk/guidance/surface-water-pollution-risk-assessment-for-your-environmental-permit",
    ),
    (
        "Environment Agency and Department for Environment, Food & Rural Affairs (2024)",
        "https://environment.data.gov.uk/water-quality/view/landing",
    ),
    ("Faulkner, D. (2022)", "https://www.bbc.co.uk/news/uk-62303330"),
    (
        "Global Designing Cities Initiative (2016)",
        "https://globaldesigningcities.org/publication/global-street-design-guide/utilities-and-infrastructure/green-infrastructure-stormwater-management/",
    ),
    ("Gupta, T. (2024)", "https://www.bbc.co.uk/news/articles/c51yn1408v7o"),
    (
        "Highways England (2016)",
        "https://www.gov.uk/government/consultations/a27-chichester-bypass-improvement-scheme",
    ),
    (
        "International Union for Conservation of Nature (2023)",
        "https://iucn.org/story/202305/embracing-biodiversity-paving-way-nature-inclusive-cities",
    ),
    (
        "Joint Nature Conservation Committee (2020)",
        "https://jncc.gov.uk/our-work/ramsar-sites/",
    ),
    (
        "Kenward, L. and Wolski, S. (2024)",
        "https://www.bbc.co.uk/news/articles/crgzpmp5yp5o",
    ),
    (
        "Kirby, D. (2023)",
        "https://www.gov.uk/government/publications/environmental-impact-assessment-screening-report-for-chichester-by-the-sea",
    ),
    (
        "NERC (2016)",
        "https://nercscience.org/publications/decision-making-under-deep-uncertainty/",
    ),
    ("Portsmouth Water (2024)", "https://portsmouthwater.co.uk/"),
    (
        "Rivers Trust (2023)",
        "https://www.theriverstrust.org/chichester-harbour-water-framework-directive-investigations",
    ),
    (
        "Royal Town Planning Institute (2024)",
        "https://www.rtpi.org.uk/blog/2023/august/enhancing-water-neutrality-and-climate-resilience-within-new-housing-developments-chichester-district-council/",
    ),
    (
        "Sussex IFCA (2018)",
        "https://www.gov.uk/government/publications/chichester-harbour-non-intervention-coastal-management-study",
    ),
    (
        "Sussex Wildlife Trust (2024)",
        "https://sussexwildlifetrust.org.uk/what-we-do/living-landscapes",
    ),
    (
        "The Ramblers (2023)",
        "https://www.ramblers.org.uk/get-involved/campaign-with-us/coastal-access/coastal-path",
    ),
]

# Checkpoint file
checkpoint_file = os.path.join(script_dir, "checkpoint.txt")

# Process each URL
for name, url in url_list:
    if url:  # Only process if URL is not empty
        # Create a filename based on the name
        filename = clean_filename(
            f"{name.split(',')[0].lower()}_{name.split('(')[1][:4]}.txt"
        )
        output_file = os.path.join(script_dir, filename)

        # Extract content and save to file
        success = extract_content(url, output_file)

        if not success:
            # Log the skipped URL in the checkpoint file
            with open(checkpoint_file, "a", encoding="utf-8") as cf:
                cf.write(f"Skipped: {name} - {url}\n")

        # Add a small delay to avoid overwhelming the servers
        time.sleep(2)
    else:
        print(f"Skipping {name} due to missing URL")
        with open(checkpoint_file, "a", encoding="utf-8") as cf:
            cf.write(f"Skipped (No URL): {name}\n")

print("All URLs have been processed.")
print(f"Check {checkpoint_file} for a list of skipped URLs.")
