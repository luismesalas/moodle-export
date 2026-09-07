# Moodle Centros Andalucía - Automatización de Backups

Este script en Python utiliza Playwright para automatizar la descarga de copias de seguridad (`.mbz`) de todos los cursos activos en los que estás matriculado en Moodle Centros Andalucía.

Está diseñado para lidiar con las particularidades del sistema de la Junta, como el inicio de sesión SSO (IdEA), los errores de validación CAS, y la comprobación de permisos de backup por módulo para omitir aquellos en los que la exportación no está disponible (como es el caso del "punto de encuentro" de tu centro).

Genera automáticamente nombres de archivo limpios utilizando un *slug* con el nombre del curso (ej. `1234-sistemas-operativos-en-red.mbz`) dentro de una carpeta llamada "backups" en la misma ubicación en la que ejecutes el script.

## Requisitos e Instalación

Para ejecutar este script, necesitas **Python 3.12** (actualmente la última versión estable recomendada y garantizada como compatible con Playwright 1.62, aunque el soporte abarca desde Python 3.8 en adelante).

Puedes instalar las dependencias directamente en tu instalación local de Python o aislar el proyecto utilizando un entorno virtual (`virtualenv` o `venv`).

### Instala las dependencias incluidas en el repositorio:
```bash
pip install -r requirements.txt
```

### Instala los navegadores de Playwright:
```bash
playwright install
```

## Uso y Ejecución

Por motivos de seguridad, se recomienda no incluir la contraseña directamente en el comando para que el script la solicite de forma segura (oculta) por terminal.

### Ejecución básica (Recomendada)

```bash
python moodle_export.py -u tu_usuario_idea --url https://educacionadistancia.juntadeandalucia.es/centros/sevilla25
```

### Ejecución guardando un registro de logs

Como el script emite toda la información por la salida estándar, puedes redirigir los logs a un archivo de texto utilizando `>`:

```bash
python moodle_export.py -u tu_usuario_idea --url https://educacionadistancia.juntadeandalucia.es/centros/sevilla25 > historial_backups.log
```

### Ejecución para depuración (viendo el navegador y aumentando el timeout)

```bash
python moodle_export.py -u tu_usuario_idea --url https://educacionadistancia.juntadeandalucia.es/centros/sevilla25 --ui -t 15
```

### Opciones Disponibles

Igualmente, aquí tienes un resumen de las opciones disponibles.

| Argumento | Corto | Descripción |
| --- | --- | --- |
| `--usuario` | `-u` | **(Obligatorio)** Tu nombre de usuario de Séneca/IdEA. |
| `--url` |  | **(Obligatorio)** URL base de tu instancia de Moodle Centros (ej: `[https://educacionadistancia.juntadeandalucia.es/centros/sevilla25](https://educacionadistancia.juntadeandalucia.es/centros/sevilla25)`). Permite apuntar al curso académico y provincia correspondientes. |
| `--password` | `-p` | (Opcional) Tu contraseña. Si no se incluye, el script pausará la ejecución y te la pedirá por pantalla de forma segura. |
| `--timeout` | `-t` | (Opcional) Tiempo máximo de espera para exportar cada curso en **minutos**. Por defecto es `5`. Útil para aumentar el límite en módulos con máquinas virtuales o muchos adjuntos. |
| `--ui` |  | (Opcional) Bandera que desactiva el modo oculto (*headless*). Abre la ventana del navegador para que puedas ver el proceso en tiempo real (ideal para depuración). |

## Autoría y Licencia

Este script ha sido desarrollado para automatizar y facilitar el trabajo administrativo del profesorado de Formación Profesional, aunque es aplicable a cualquier otro cuerpo de profesores que use Moodle Centros como plataforma de aprendizaje.

**Autor:** Luis Mesa

**Contacto:** [luismesalas@gmail.com](mailto:luismesalas@gmail.com), [LinkedIn](https://www.linkedin.com/in/mesa)

[![Licencia CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

Este proyecto se distribuye bajo una licencia [CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/deed.es). Eres libre de copiar, adaptar, remezclar y redistribuir este código para automatizar tus propios módulos o los de tu centro, siempre y cuando se cite la autoría original y las nuevas versiones se distribuyan bajo esta misma licencia. Tienes más información en el fichero [LICENSE.txt](LICENSE.txt)


El script se ha hecho en una tarde y estoy seguro de que tiene margen de mejora porque se han tomado ciertas decisiones de forma un poco arbitraria. Siéntete libre de compartirme sugerencias, ya sea por correo o mediante PR y serán evaluadas a la mayor brevedad posible.

Si crees que puede servir a cualquier otro compañero o compañera, no dudes en compartir. Si no sabes que es eso de Python y necesitas ayuda para ejecutarlo, habla con tu coordinador o coordinadora TIC/TDE.

Muchas gracias y un saludo, Luis Mesa.
