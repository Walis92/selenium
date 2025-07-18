
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

@app.route("/crear-nota", methods=["POST"])
def crear_nota():
    data = request.json
    case_id = data.get("ID")
    subject = data.get("SUBJECT")
    nota = data.get("NOTA")
    tfa_code = data.get("TFA")

    if not all([case_id, subject, nota]):
        return jsonify({"error": "Faltan datos: ID, SUBJECT o NOTA"}), 400

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        print("🌐 Abriendo MyCase login...")
        driver.get("https://www.mycase.com/login/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login_session_email")))

        driver.find_element(By.ID, "login_session_email").send_keys("dagarcia@mendozafirm.com")
        driver.find_element(By.ID, "login_session_password").send_keys("Left4dead2")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(3)

        # Detectar 2FA
        try:
            code_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "email-tfa-code")))
            print("🔐 Campo de 2FA detectado. Ingresando código...")
            if tfa_code:
                code_input.send_keys(tfa_code)
                checkbox = driver.find_element(By.ID, "checkbox-boolean-input-0")
                if not checkbox.is_selected():
                    checkbox.click()
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))
                print("✅ Login completado. Llegamos al dashboard.")
            else:
                return jsonify({"error": "Código 2FA requerido pero no proporcionado en JSON"}), 401
        except:
            print("ℹ️ No se solicitó código 2FA.")

        # Ir a la sección de notas
        print(f"📄 Entrando a la sección de notas del caso {case_id}")
        notas_url = f"https://the-mendoza-law-firm.mycase.com/court_cases/{case_id}/notes"
        driver.get(notas_url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Add a Note")))
        driver.find_element(By.LINK_TEXT, "Add a Note").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "subject")))

        driver.find_element(By.ID, "subject").send_keys(subject)
        content_div = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']")
        driver.execute_script("arguments[0].innerHTML = '<p>{}</p>'".format(nota.replace("'", "\'")), content_div)
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-cta-primary[type='submit']").click()
        time.sleep(2)

        return jsonify({"success": True, "message": "Nota creada exitosamente"})

    except Exception as e:
        print("❌ Error durante la automatización:")
        print(str(e))
        try:
            driver.save_screenshot("error.png")
            print("📸 Captura de pantalla guardada como error.png")
        except:
            print("⚠️ No se pudo guardar la captura de pantalla.")
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



