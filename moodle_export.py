import argparse
import getpass
import logging
import os
import re
import sys
import unicodedata

from playwright.sync_api import sync_playwright


def configure_logger():
    logger = logging.getLogger("MoodleBackup")
    logger.setLevel(logging.INFO)

    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    return logger


def generate_slug(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


def export_all_courses(user, password, base_url, show_ui, logger, timeout_min):
    timeout_ms = timeout_min * 60 * 1000

    # Limpiamos la URL por si se introduce con una barra al final
    base_url = base_url.rstrip('/')

    # Asegurar que el directorio de descargas existe para evitar errores
    os.makedirs("./backups", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not show_ui)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        logger.info(f"Iniciando login a través del SSO IdEA en {base_url}...")
        page.goto(f"{base_url}/login/index.php")

        # Clic en el botón de Moodle Centros
        logger.info("Seleccionando el método de autenticación...")
        # Usamos regex para ignorar acentos o mayúsculas en 'Acceso Único Educación'
        page.locator("text=/Acceso [Úu]nico Educaci[óo]n/i").first.click()

        # Esperamos a que el formulario de credenciales reales haya cargado
        page.wait_for_selector("input#username")

        page.fill("input#username", user)
        page.fill("input#password", password)
        page.click("button[type='submit']")

        try:
            # Intenta llegar al dashboard de Moodle de forma normal
            page.wait_for_url("**/my/**", timeout=15000)
        except Exception:
            # Si a los 15 segundos se atasca, comprobamos si es el pantallazo del error CAS
            if page.locator("text=INVALID_TICKET").is_visible() or page.locator(
                    "text=No se ha reconocido el tique").is_visible():
                logger.warning("Detectado error de validación CAS de la Junta. Forzando entrada al Área Personal...")
                # Navegar directamente a /my/ aprovecha la cookie de sesión ya creada
                page.goto(f"{base_url}/my/")
                page.wait_for_url("**/my/**")
            else:
                # Si falla por otro motivo (contraseña incorrecta, servidor caído...), lanzamos el error
                raise Exception(
                    "Fallo en el login por un motivo desconocido (no es el error CAS). Verifica tus credenciales o el estado de Séneca.")

        logger.info("Login exitoso. Navegando al índice general de cursos...")
        page.goto(f"{base_url}/course/index.php")

        boton_expandir = page.locator("text=/Expandir todo/i").first
        if boton_expandir.is_visible():
            logger.info("Desplegando todas las categorías del árbol de cursos...")
            boton_expandir.click()
            # Pausa breve para que Moodle renderice los nodos ocultos
            page.wait_for_timeout(10000)

        page.wait_for_selector("a[href*='/course/view.php?id=']", timeout=60000)

        links = page.locator("a[href*='/course/view.php?id=']").all()
        courses_found = {}

        for link in links:
            href = link.get_attribute("href")
            link_text = link.inner_text().strip()

            if href:
                match = re.search(r"id=(\d+)", href)
                if match:
                    course_id = match.group(1)
                    if course_id not in courses_found or len(link_text) > len(courses_found.get(course_id, "")):
                        courses_found[course_id] = link_text

        total_courses = len(courses_found)
        logger.info(f"Se han encontrado {total_courses} cursos listados.")

        current_course = 0

        for course_id, raw_name in courses_found.items():
            current_course += 1
            slug = generate_slug(raw_name) if raw_name else "modulo-generico"
            final_file_name = f"{course_id}-{slug}.mbz"
            backup_path = f"./backups/{final_file_name}"

            # Comprobación de archivo existente
            if os.path.exists(backup_path):
                logger.info(f"[{current_course}/{total_courses}] Omitiendo '{raw_name}' (ID: {course_id}) - El archivo ya existe.")
                continue

            logger.info(f"[{current_course}/{total_courses}] Iniciando backup del módulo '{raw_name}' (ID: {course_id}) (Timeout configurado: {timeout_min} min)...")

            page.goto(f"{base_url}/backup/backup.php?id={course_id}")

            # Comprueba instantáneamente si aparece el mensaje de error de permisos de Moodle
            if page.locator("text=Lo sentimos, pero no tiene los permisos para hacer esto").is_visible():
                logger.warning(f"[{current_course}/{total_courses}] Omitiendo módulo '{raw_name}' (ID: {course_id}): No hay permisos para copias de seguridad.")
                continue

            try:
                # Timeout ampliado aplicado directamente al botón oneclickbackup
                page.click("input[name='oneclickbackup']", timeout=timeout_ms)
                page.wait_for_selector("text=El archivo de copia de seguridad se creó con éxito", timeout=timeout_ms)
                page.click("button:has-text('Continuar')")

                with page.expect_download() as download_info:
                    page.locator("a:has-text('Descargar')").first.click()

                download = download_info.value
                download.save_as(backup_path)
                logger.info(f"[{current_course}/{total_courses}] Copia del curso '{raw_name}' guardada correctamente en {backup_path}")

            except Exception as e:
                logger.error(f"[{current_course}/{total_courses}] Error al procesar el curso '{raw_name}' (ID: {course_id}): {e}")
                continue

        browser.close()
        logger.info("Automatización de backups finalizada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatización de copias de seguridad de Moodle Centros.")

    parser.add_argument("-u", "--usuario", required=True, help="Usuario IdEA/Séneca")
    parser.add_argument("-p", "--password", required=False,
                        help="Contraseña IdEA/Séneca (si no se indica, se pedirá de forma oculta)")
    parser.add_argument("--url", required=True,
                        help="URL base de la provincia/año (ej: https://educacionadistancia.juntadeandalucia.es/centros/sevilla25)")
    parser.add_argument("-t", "--timeout", type=int, default=5,
                        help="Tiempo máximo de espera por curso en MINUTOS (defecto: 5)")
    parser.add_argument("--ui", action="store_true", help="Muestra la interfaz gráfica del navegador para depurar")

    args = parser.parse_args()

    input_password = args.password
    if not input_password:
        input_password = getpass.getpass(prompt=f"Introduce la contraseña para el usuario '{args.usuario}': ")

    configured_logger = configure_logger()

    export_all_courses(args.usuario, input_password, args.url, args.ui, configured_logger, args.timeout)
