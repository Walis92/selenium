from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import imaplib
import email
import re
import os

# --- CONFIGURACIÓN ---
MYCASE_EMAIL = "dagarcia@mendozafirm.com"
MYCASE_PASSWORD = "Left4dead2"
OUTLOOK_EMAIL = "dagarcia@mendozafirm.com"
OUTLOOK_PASSWORD = os.environ.get("OUTLOOK_PASSWORD")
IMAP_SERVER = "outlook.office365.com"
IMAP_FOLDER = "INBOX"
# ----------------------

app = Flask(__name__)
driver = None

def iniciar_sesion():
    global driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.mycase.com/login/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login_session_email")))

    driver.find_element(By.ID, "login_session_email").send_keys(MYCASE_EMAIL)
    driver.find_element(By.ID, "login_session_password").send_keys(MYCASE_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email-tfa-code")))
        print("🔐 Código 2FA requerido. Obteniendo de Outlook...")
        codigo = obtener_codigo_2fa()
        driver.find_element(By.ID, "email-tfa-code").send_keys(codigo)
        checkbox = driver.find_element(By.ID, "checkbox-boolean-input-0")
        driver.execute_script("arguments[0].click();", checkbox)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    except:
        print("No se solicitó código 2FA")

    WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))
    print("✅ Login exitoso.")

def obtener_codigo_2fa():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
    mail.select(IMAP_FOLDER)

    result, data = mail.search(None, 'UNSEEN')
    ids = data[0].split()
    for email_id in reversed(ids):
        result, msg_data = mail.fetch(email_id, '(RFC822)')
        raw_email = msg_data[0][1]
        message = email.message_from_bytes(raw_email)

        if "MyCase" in message["Subject"]:
            body = ""
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode()
            else:
                body = message.get_payload(decode=True).decode()

            match = re.search(r'Your verification code is[:\s]+(\d{6})', body)
            if match:
                return match.group(1)
    return ""

@app.route("/crear-nota", methods=["POST"])
def crear_nota():
    global driver
    data = request.get_json()
    cliente_id = data.get("ID")
    nota_texto = data.get("NOTA")
    subject_text = data.get("SUBJECT", "Auto Note")

    if not cliente_id or not nota_texto:
        return jsonify({"error": "Faltan ID o NOTA"}), 400

    try:
        driver.get(f"https://the-mendoza-law-firm.mycase.com/court_cases/{cliente_id}/notes")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Add a Note"))
        ).click()

        # Esperar a que aparezca el popup
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "subject"))
        ).send_keys(subject_text)

        # Esperar y escribir en el div editable
        rich_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ck-content[contenteditable='true']"))
        )
        driver.execute_script("arguments[0].innerHTML = `<p>{}</p>`;".format(nota_texto.replace("'", "\'").replace('"', '\"')), rich_text)

        # Guardar
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-cta-primary[type='submit']").click()
        time.sleep(2)

        return jsonify({"status": "Nota creada con éxito", "cliente_id": cliente_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    iniciar_sesion()
    app.run(host="0.0.0.0", port=5000)

