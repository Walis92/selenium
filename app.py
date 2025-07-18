from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.mycase.com/login/")
        time.sleep(2)

        driver.find_element(By.ID, "login_session_email").send_keys("dagarcia@mendozafirm.com")
        driver.find_element(By.ID, "login_session_password").send_keys("Left4dead2")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(5)  # Espera para que cargue la verificación 2FA

        # Espera hasta que el usuario manualmente introduzca el código
        print("Esperando que ingreses el código 2FA en el navegador... (30s)")
        time.sleep(30)

        # Ir al dashboard y luego al cliente
        driver.get(f"https://the-mendoza-law-firm.mycase.com/court_cases/{cliente_id}/notes")
        time.sleep(3)

        # Crear nota (estos selectores deben ajustarse a lo que ves en pantalla)
        driver.find_element(By.LINK_TEXT, "New Note").click()
        time.sleep(2)
        driver.find_element(By.NAME, "note[body]").send_keys(nota_texto)
        driver.find_element(By.NAME, "commit").click()
        time.sleep(2)

        driver.quit()
        return jsonify({"status": "Nota creada con éxito", "cliente_id": cliente_id}), 200

    except Exception as e:
        driver.quit()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
