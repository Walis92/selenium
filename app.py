from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

@app.route('/crear-nota', methods=['POST'])
def crear_nota():
    data = request.get_json()
    cliente_id = data.get("ID")
    nota_texto = data.get("NOTA")

    if not cliente_id or not nota_texto:
        return jsonify({"error": "Faltan ID o NOTA"}), 400

    options = Options()
    # options.add_argument("--headless")  # Descomenta para modo oculto
    options.add_argument("--window-size=1200x900")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--user-data-dir=/tmp/chrome")  # ← solución a session conflict

    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.mycase.com/login/")
        time.sleep(2)

        # Login
        driver.find_element(By.ID, "login_session_email").send_keys("dagarcia@mendozafirm.com")
        driver.find_element(By.ID, "login_session_password").send_keys("Left4dead2")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(5)

        current_url = driver.current_url
        if "dashboard" in current_url:
            print("✅ Login exitoso. Ya estamos en el dashboard.")
        else:
            print(f"⚠️ No se llegó al dashboard. Página actual: {current_url}")
            driver.quit()
            return jsonify({"error": "No se llegó al dashboard", "pagina_actual": current_url}), 403

        driver.get(f"https://the-mendoza-law-firm.mycase.com/court_cases/{cliente_id}/notes")
        time.sleep(3)

        try:
            new_note_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'New Note')]"))
            )
            new_note_button.click()
        except Exception as e:
            driver.quit()
            return jsonify({"error": f"No se encontró el botón para nueva nota: {str(e)}"}), 500

        time.sleep(2)
        driver.find_element(By.NAME, "note[body]").send_keys(nota_texto)
        driver.find_element(By.NAME, "commit").click()
        time.sleep(2)

        driver.quit()
        return jsonify({"status": "Nota creada con éxito", "cliente_id": cliente_id}), 200

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

