import os
import time
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =========================
# CONFIG
# =========================
url = "https://search.mlslistings.com/Matrix/Public/PhotoPopup.aspx?tid=9&mtid=1&L=1&key=2941554150&n=81&i=0&View=Y"

parsed_url = urlparse(url)
params = parse_qs(parsed_url.query)

TOTAL_IMAGES = int(params.get("n", [0])[0])
current_index = int(params.get("i", [1])[0])  # start from current
listing_key = params.get("key", [""])[0]

BASE_URL = "https://search.mlslistings.com/Matrix/Public/PhotoPopup.aspx"

SAVE_DIR = "images"
WAIT_TIME = 15

LOGIN_URL = "https://mlslpro.b2clogin.com/mlslpro.onmicrosoft.com/oauth2/v2.0/authorize?p=B2C_1_SocialLocalSignInNewPro&client_id=c43dcffb-386e-4173-9221-d468e386b2d8&nonce=defaultNonce&redirect_uri=https%3A%2F%2Fconnect.mlslistings.com%2Fazureadloginresponder.ashx&scope=openid&response_type=id_token&prompt=login&response_mode=query"

USERNAME = "Your User Name"
PASSWORD = "Your MLSlisting Password"

# =========================
# SETUP
# =========================
os.makedirs(SAVE_DIR, exist_ok=True)

options = Options()
options.add_argument("--start-maximized")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, WAIT_TIME)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# =========================
# LOGIN
# =========================
def login():
    log("🔐 Logging in...")
    driver.get(LOGIN_URL)

    username_input = wait.until(EC.presence_of_element_located((By.ID, "UserId")))
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))

    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    driver.find_element(By.ID, "next").click()

    wait.until(lambda d: "login" not in d.current_url.lower())
    log("✅ Logged in!")

# =========================
# BUILD URL
# =========================
def build_url(i):
    return (
        f"{BASE_URL}?tid=9&mtid=1&L=1"
        f"&key={listing_key}&n={TOTAL_IMAGES}&i={i}&View=Y"
    )

# =========================
# DOWNLOAD LOOP
# =========================
login()

previous_src = None

for i in range(current_index, TOTAL_IMAGES + 1):
    page_url = build_url(i)
    log(f"📸 Opening image {i}/{TOTAL_IMAGES}")

    try:
        driver.get(page_url)

        # Wait for image
        img = wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))

        # Wait until src changes (CRITICAL FIX)
        wait.until(lambda d: img.get_attribute("src") != previous_src)

        img_src = img.get_attribute("src")
        previous_src = img_src

        # Download via requests (better quality than screenshot)
        response = requests.get(img_src, stream=True)

        file_path = os.path.join(SAVE_DIR, f"img_{i:03}.jpg")

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        log(f"✅ Saved img_{i:03}.jpg")

    except Exception as e:
        log(f"❌ Failed at {i}: {e}")
        time.sleep(2)

# =========================
# CLEANUP
# =========================
driver.quit()
log("🎉 Done!")
