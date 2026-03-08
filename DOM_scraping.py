import requests
from bs4 import BeautifulSoup
import base64
import os
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def getdata(url):
    r = requests.get(url)
    return r.text

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to the URL
    url = "https://egypt.blsspainglobal.com/Global/CaptchaPublic/GenerateCaptcha?data=4CDiA9odF2%2b%2bsWCkAU8htqZkgDyUa5SR6waINtJfg1ThGb6rPIIpxNjefP9UkAaSp%2fGsNNuJJi5Zt1nbVACkDRusgqfb418%2bScFkcoa1F0I%3d"
    driver.get(url)
    
    # Wait for images to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "img"))
    )
    
    # Get page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Create images folder if it doesn't exist
    os.makedirs('images', exist_ok=True)
    
    # 1. SCRAPE ALL IMAGES AND SAVE TO allimages.json
    all_images = soup.find_all("img")
    all_images_data = []
    
    for i, image in enumerate(all_images):
        src = str(image.get('src', ''))
        alt = str(image.get('alt', ''))
        
        if src.startswith('data:image/'):
            try:
                header, encoded = src.split(',', 1)
                all_images_data.append({
                    'index': i,
                    'alt': alt,
                    'src': src,
                    'type': header.split(';')[0].replace('data:', '')
                })
            except Exception as e:
                print(f"Error processing image {i}: {e}")
    
    # Save all images to JSON
    with open('allimages.json', 'w', encoding='utf-8') as f:
        json.dump(all_images_data, f, indent=2)
    print(f"Saved {len(all_images_data)} images to allimages.json")
    
    # 2. SCRAPE ONLY VISIBLE IMAGES (9 visible captcha boxes)
    visible_images_data = []
    
    # Find the captcha container (the grid div)
    try:
        captcha_container = driver.find_element(By.CSS_SELECTOR, "div[class*='captcha']")
    except:
        captcha_container = None
    
    # Get the first 9 captcha images visible in the grid
    captcha_image_elements = driver.find_elements(By.CSS_SELECTOR, "img.captcha-img")
    
    # Limit to first 9 visible images
    visible_count = 0
    for i, element in enumerate(captcha_image_elements):
        if visible_count >= 9:
            break
            
        try:
            # Check if element is visible
            if element.is_displayed():
                # Get computed styles
                computed_display = driver.execute_script("return window.getComputedStyle(arguments[0]).display;", element)
                computed_visibility = driver.execute_script("return window.getComputedStyle(arguments[0]).visibility;", element)
                computed_opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity;", element)
                
                # Check if element is truly visible
                if computed_display != 'none' and computed_visibility != 'hidden' and float(computed_opacity) > 0:
                    size = element.size
                    
                    # Check if element has valid size 
                    if size['width'] > 0 and size['height'] > 0:
                        src = element.get_attribute('src')
                        alt = element.get_attribute('alt')
                        
                        if src and src.startswith('data:image/'):
                            header, encoded = src.split(',', 1)
                            visible_images_data.append({
                                'index': visible_count,
                                'alt': alt,
                                'src': src,
                                'type': header.split(';')[0].replace('data:', '')
                            })
                            
                            # Save individual visible images to the images folder
                            data = base64.b64decode(encoded)
                            with open(f'images/captcha_visible_{visible_count}.png', 'wb') as f:
                                f.write(data)
                            print(f"Saved images/captcha_visible_{visible_count}.png")
                            visible_count += 1
        except Exception as e:
            print(f"Error processing image {i}: {e}")
    
    # Save visible images to JSON (only the 9 visible ones)
    with open('visible_images_only.json', 'w', encoding='utf-8') as f:
        json.dump(visible_images_data, f, indent=2)
    print(f"\nSaved {len(visible_images_data)} VISIBLE images to visible_images_only.json")
    
    # 3. SCRAPE VISIBLE TEXT INSTRUCTIONS
    text_data = {
        'page_title': soup.title.string if soup.title else 'No title',
        'all_text': [],
        'visible_instructions': []
    }
    
    # Extract all text
    for text in soup.stripped_strings:
        if text.strip():
            text_data['all_text'].append(text.strip())
    
    # Look for instruction-related text (common patterns)
    for text in text_data['all_text']:
        if any(keyword in text.lower() for keyword in ['select', 'click', 'please', 'box', 'number', 'image']):
            text_data['visible_instructions'].append(text)
    
    # Save text data to JSON
    with open('visible_text_instructions.json', 'w', encoding='utf-8') as f:
        json.dump(text_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtracted text:")
    print(f"Total text elements: {len(text_data['all_text'])}")
    print(f"Visible instructions found: {len(text_data['visible_instructions'])}")
    if text_data['visible_instructions']:
        print("\nInstructions:")
        for instruction in text_data['visible_instructions'][:5]:  # Show first 5
            print(f"  - {instruction}")
    
    print("\nAll files saved successfully!")
    
    # Wait before closing the browser
    print("\nBrowser will close in 5 seconds...")
    time.sleep(5)

finally:
    driver.quit()
