from flask import Flask, request, jsonify
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

app = Flask(__name__)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Run in headless mode
chrome_options.page_load_strategy = 'eager'
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_experimental_option("detach", True)  # Optional: Keep Chrome open if not headless
# user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
# chrome_options.add_argument(f"user-agent={user_agent}")

def scrape_leetcode_profile(url):
    # Initialize the WebDriver using WebDriver Manager
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)

    # Wait for the page to load completely
    # time.sleep(4)

    # Initialize a dictionary to store all profile data
    profile_data = {}

    try:
        # Extract Image URL
        image_element = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[1]/div[1]/div[1]/img')
        img_src = image_element.get_attribute('src')
        profile_data['image_url'] = img_src

        # Extract Name
        name_element = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div')
        name = name_element.text
        profile_data['name'] = name

        # Extract questions solved
        Questions_solved_div_number = len(driver.find_elements(By.XPATH, '/html/body/div[1]/div[1]/div[4]/div/div[2]/div')) - 2
        easy_solved = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[1]/div/div/div[2]/div[1]/div[2]').text
        medium_solved = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[1]/div/div/div[2]/div[2]/div[2]').text
        hard_solved = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[1]/div/div/div[2]/div[3]/div[2]').text

        profile_data['questions_solved'] = {
            'easy': easy_solved,
            'medium': medium_solved,
            'hard': hard_solved
        }

        # Extract Languages Expertise
        languages_used = {}
        i = 1
        while True:
            try:
                language = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[6]/div[{i}]/div[1]/span').text
                problems_solved = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[6]/div[{i}]/div[2]/span[1]').text
                languages_used[language] = problems_solved
                i += 1
            except NoSuchElementException:
                break
        profile_data['languages_used'] = languages_used

        # Extract Skills
        skills_data = {}
        for i in range(1, 4):
            skill_level = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[8]/div[2]/div[{i}]/div[1]').text
            skill_info = {}
            j = 1
            while True:
                try:
                    skill = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[8]/div[2]/div[{i}]/div[2]/div[{j}]/a/span').text
                    level = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[1]/div/div[8]/div[2]/div[{i}]/div[2]/div[{j}]/span').text.strip("x")
                    skill_info[skill] = level
                    j += 1
                except NoSuchElementException:
                    break
            skills_data[skill_level] = skill_info
        profile_data['skills'] = skills_data

        # Extract Badges
        total_badges = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[2]/div/div/div[1]/div/div[2]').text
        profile_data['badges'] = {
            'total_badges': total_badges
        }

        if int(total_badges) != 0:
            top_badges = {}
            i = 0
            while True:
                i += 1
                try:
                    badge_name = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[2]/div/div/div[2]/div[{i}]/img').get_attribute('alt')
                    badge_logo_url = driver.find_element(By.XPATH, f'/html/body/div[1]/div[1]/div[4]/div/div[2]/div[{Questions_solved_div_number}]/div[2]/div/div/div[2]/div[{i}]/img').get_attribute('src')
                    top_badges[badge_name] = badge_logo_url
                except NoSuchElementException:
                    break
            profile_data['badges']['top_badges'] = top_badges

    except Exception as e:
        # Handle exceptions and close the driver
        driver.quit()
        raise e

    # Close the driver
    driver.quit()

    # Return the profile data as a JSON object
    return profile_data

@app.route('/scrape', methods=['GET'])
def scrape_profile():
    # Get URL from the request arguments
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        profile_data = scrape_leetcode_profile(url)
        return jsonify(profile_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
