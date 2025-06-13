import os
import pymupdf
import pytesseract
import shutil
import time
import requests
import urllib3
from pdf2image import convert_from_path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure necessary folders exist
os.makedirs("./data", exist_ok=True)
os.makedirs("./downloads", exist_ok=True)
os.makedirs("./extracted", exist_ok=True)

file_path = "./data/dataset.txt"

# Read existing entries to avoid duplicates
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        existing_data = f.readlines()
else:
    existing_data = []

# Set up Chrome options for automatic downloads
options = webdriver.ChromeOptions()
prefs = {"download.default_directory": os.path.abspath("./downloads")}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.get("https://iost.tu.edu.np/notices")

# Find "Exam Result" notices
a_tags = driver.find_elements(By.XPATH, "//ul//div[@class='detail']/a[./h5[contains(text(), 'Exam Result')]]")

new_entries = []
notice_details = []  # Store (title, link) pairs

for a in a_tags:
    href = a.get_attribute("href")
    h5_title = a.find_element(By.TAG_NAME, 'h5').text.strip().replace("/", "-")  # Replace invalid filename characters
    entry = f"Title: {h5_title}, Link: {href}\n"
    
    if entry not in existing_data:
        new_entries.append(entry)
    
    notice_details.append((h5_title, href))  # Store title and link

# Append only new entries
if new_entries:
    with open(file_path, "a", encoding="utf-8") as f:
        f.writelines(new_entries)

# Process each link
for h5_title, link1 in notice_details:
    try:
        pdf_filename = f"./downloads/{h5_title}.pdf"  # Save as h5_title.pdf
        
        # Check if the file already exists before downloading
        if os.path.exists(pdf_filename):
            print(f"🔄 Skipping (already exists): {pdf_filename}")
            continue  # Skip downloading if file exists

        driver.get(link1)
        
        # Wait for the download link to appear
        a_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[@class='text-center']//a"))
        )
        pdf_url = a_tag.get_attribute('href')

        if pdf_url.endswith(".pdf"):  # Check if it's a PDF link
            print(f"📥 Downloading PDF: {pdf_url}")
            
            # Download using requests (Disable SSL verification)
            response = requests.get(pdf_url, stream=True, verify=False)
            if response.status_code == 200:
                with open(pdf_filename, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=1024):
                        pdf_file.write(chunk)
                print(f"✅ Downloaded successfully: {pdf_filename}")
            else:
                print(f"❌ Failed to download PDF: {pdf_url} (Status Code: {response.status_code})")

    except Exception as e:
        print(f"⚠ Error processing {link1}: {e}")
time.sleep(10)
# Close the browser
driver.quit()

path = "./downloads"
for file_name in os.listdir(path):
    file_path = os.path.join(path,file_name)
    doc = pymupdf.open(file_path)
    print(file_name)
    with open(f"./extracted/{file_name}.txt","w",encoding="utf-8") as data:
            images = convert_from_path(file_path)
            
            # Extract text from each image using pytesseract
            for image in images:
                text = pytesseract.image_to_string(image, lang="eng")  # Extract text using OCR
                data.write(text)
                data.write("\n")  # Add a newline after each image

    print(f"Extracted text saved to: ./extracted/{path}")

shutil.rmtree("./data")
shutil.rmtree("./downloads")
