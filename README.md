# 🛡️ CyberJob Hunter

> Sistema inteligente de búsqueda de empleo para perfiles de **Ciberseguridad, IT e Infraestructura**.  
> Automatiza la búsqueda de vacantes, valida empresas, genera cartas de presentación con IA y entrena para entrevistas técnicas.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Claude AI](https://img.shields.io/badge/Claude-AI%20Powered-orange?logo=anthropic)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-WSL%20%7C%20Linux%20%7C%20macOS-lightgrey)

---

##  Tabla de contenidos

1. [¿Qué hace este sistema?](#qué-hace)
2. [Arquitectura](#arquitectura)
3. [Requisitos del sistema](#requisitos)
4. [Instalación paso a paso](#instalación)
5. [Configurar tu CV](#configurar-cv)
6. [Obtener API Key de Claude](#api-key)
7. [Levantar el sistema](#levantar)
8. [Cómo usar el dashboard](#uso)
9. [Estructura del proyecto](#estructura)
10. [Solución de problemas](#troubleshooting)
11. [Contribuir](#contribuir)

---

## ¿Qué hace?

CyberJob Hunter es una plataforma que automatiza el proceso de búsqueda de empleo en ciberseguridad e IT:

| Módulo | Función |
|---|---|
|  **Scraper** | Busca vacantes en Computrabajo, OCC, RemoteOK y Arbeitnow |
|  **Validador** | Detecta y bloquea ofertas fraudulentas automáticamente |
|  **Match IA** | Califica cada vacante según tu perfil (0-99%) |
|  **Carta IA** | Genera carta de presentación personalizada por vacante |
|  **Entrevista IA** | Prepara preguntas y respuestas modelo para cada empresa |
|  **Cola de aprobación** | Tú decides qué vacantes aprobar antes de aplicar |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     CYBERJOB HUNTER                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Tu CV (config.py)                                           │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │   Scraper   │───▶│  Validador   │───▶│  Match Score  │   │
│  │             │    │  Anti-fraude │    │   (0-99%)     │   │
│  │ Computrabajo│    └──────────────┘    └───────┬───────┘   │
│  │ OCC Mundial │                                │           │
│  │ RemoteOK    │                                ▼           │
│  │ Arbeitnow   │                    ┌───────────────────┐   │
│  └─────────────┘                    │  data/vacantes.json│   │
│                                     └─────────┬─────────┘   │
│                                               │             │
│                                               ▼             │
│                                    ┌───────────────────┐    │
│                                    │   API Server       │    │
│                                    │   (server.py)      │    │
│                                    │   puerto 3001      │    │
│                                    └─────────┬─────────┘    │
│                                              │              │
│                          ┌───────────────────┼──────────┐   │
│                          │                   │          │   │
│                          ▼                   ▼          ▼   │
│                    Dashboard            Claude AI    Scraper │
│                    (browser)            API          (bg)    │
│                    localhost:3001                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Requisitos

### Sistema operativo
- **Windows 10/11** con WSL2 (Ubuntu 22.04 o 24.04) ← recomendado
- **Linux** (Ubuntu, Debian, Fedora)
- **macOS** 12+

### Software requerido
| Software | Versión mínima | Cómo instalar |
|---|---|---|
| Python | 3.11+ | `sudo apt install python3` |
| pip | 24+ | `sudo apt install python3-pip` |
| Git | 2.x | `sudo apt install git` |
| WSL2 | (Windows) | Microsoft Store → Ubuntu |

### Cuenta requerida
- **Anthropic** (gratuita) → https://console.anthropic.com — para la IA de cartas y entrevistas

---

## Instalación

### En Windows con WSL2

**Paso 1 — Instalar WSL2 y Ubuntu**

Abre PowerShell como Administrador y ejecuta:
```powershell
wsl --install
```
Reinicia tu PC. Al abrir Ubuntu por primera vez, crea tu usuario y contraseña.

**Paso 2 — Clonar el proyecto**

```bash
# En tu terminal WSL (Ubuntu)
git clone https://github.com/TU_USUARIO/cyberjob-hunter.git
cd cyberjob-hunter
```

**Paso 3 — Crear entorno virtual**

```bash
sudo apt update
sudo apt install -y python3-full python3-venv

python3 -m venv venv
source venv/bin/activate
```

**Paso 4 — Instalar dependencias**

```bash
pip install -r requirements.txt
```

**Paso 5 — Configurar tu perfil de CV**

```bash
cp config.example.py config.py
nano config.py
# → Edita con tus datos (ver sección siguiente)
```

**Paso 6 — Configurar API key de Claude**

```bash
nano api/server.py
# → Busca ANTHROPIC_API_KEY y pon tu key
```

**Paso 7 — Primera búsqueda de vacantes**

```bash
python scraper/indeed_scraper.py
```

**Paso 8 — Levantar el dashboard**

```bash
python api/server.py
```

Abre en tu navegador: **http://localhost:3001**

---

### En Linux / macOS

```bash
git clone https://github.com/TU_USUARIO/cyberjob-hunter.git
cd cyberjob-hunter

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp config.example.py config.py
# Edita config.py con tu perfil

python scraper/indeed_scraper.py
python api/server.py
```

---

## Configurar tu CV

Edita el archivo `config.py` con **tus datos reales**:

```python
# config.py — Tu perfil profesional

PERFIL = {
    # ── Datos personales ────────────────────────────────
    "nombre":    "Tu Nombre Completo",
    "titulo":    "Especialista en Ciberseguridad",  # Tu título profesional
    "email":     "tu@email.com",
    "telefono":  "55 1234 5678",
    "ubicacion": "Ciudad de México, México",

    # ── Experiencia ─────────────────────────────────────
    "anos_experiencia": 5,
    "ultimo_puesto":    "Analista de Seguridad en Empresa XYZ",
    "resumen": """
        5 años en ciberseguridad y administración de sistemas.
        Especialista en SIEM, respuesta a incidentes e ISO 27001.
        Experiencia con Wazuh, Suricata, Fortinet y Linux.
    """,

    # ── Skills técnicos ─────────────────────────────────
    # Lista todas tus habilidades técnicas
    "skills": [
        "Wazuh", "Suricata", "Elasticsearch", "Grafana",
        "Kali Linux", "ISO 27001", "Fortinet", "pfSense",
        "Docker", "Linux", "SIEM", "Pentesting",
        # Agrega las tuyas...
    ],

    # ── Puestos a los que quieres aplicar ───────────────
    "puestos_objetivo": [
        "Especialista en Ciberseguridad",
        "Analista SOC",
        "Ingeniero de Seguridad",
        "Administrador de Sistemas",
        # Agrega los tuyos...
    ],

    # ── Palabras clave para búsqueda ────────────────────
    "keywords_busqueda": [
        "ciberseguridad",
        "seguridad informatica",
        "SOC analyst",
        "SIEM",
        "administrador sistemas",
        # Agrega las tuyas...
    ],

    # ── Pretensión salarial ─────────────────────────────
    "sueldo_min_mxn": 35000,   # Mínimo en pesos mexicanos
    "sueldo_min_usd": 2000,    # Mínimo en dólares (para remotos)

    # ── Preferencias de búsqueda ────────────────────────
    "modalidad": ["Remoto", "Híbrido", "Presencial"],  # Quita los que no quieras
    "paises":    ["México", "Internacional"],
}
```

**El sistema usa este perfil para:**
- Calcular el % de match de cada vacante
- Personalizar las cartas de presentación
- Adaptar las preguntas de entrevista
- Filtrar búsquedas en las plataformas

---

## Obtener API Key de Claude

1. Ve a **https://console.anthropic.com/**
2. Crea una cuenta gratuita
3. Menú izquierdo → **API Keys**
4. Clic **Create Key** → ponle nombre `cyberjob-hunter`
5. **Copia la key** (empieza con `sk-ant-...`)
   >  Solo se muestra una vez — guárdala en un lugar seguro
6. Pégala en `api/server.py`:
   ```python
   ANTHROPIC_API_KEY = "sk-ant-TU-KEY-AQUI"
   ```

---

## Levantar el sistema

### Opción A — Manual (recomendado para empezar)

```bash
# Terminal 1 — Dashboard
cd cyberjob-hunter
source venv/bin/activate
python api/server.py
# → Abre http://localhost:3001

# Terminal 2 — Buscar vacantes (cuando quieras actualizar)
source venv/bin/activate
python scraper/indeed_scraper.py
```

### Opción B — Script único

```bash
chmod +x start.sh
./start.sh
```

### Opción C — Automático cada 6 horas

```bash
# Agregar al cron de WSL
crontab -e
# Agrega esta línea:
0 */6 * * * cd ~/cyberjob-hunter && venv/bin/python scraper/indeed_scraper.py >> data/scraper.log 2>&1
```

---

## Cómo usar el dashboard

### Pestaña  Pendientes
- Lista de vacantes encontradas ordenadas por % de match
- **Aprobar** → pasa a cola de aprobadas
- **Carta IA** → Claude genera carta personalizada para esa empresa
- **Entrenar** → Claude genera preguntas y respuestas de entrevista
- **Descartar** → la vacante se archiva

### Pestaña  Aprobadas
- Vacantes que aprobaste listas para aplicar
- Botón **Abrir oferta** → va directo a la página de la empresa
- Puedes generar carta y entrenar entrevista desde aquí

### Pestaña  Bloqueadas
- Ofertas detectadas como posible fraude
- El sistema las bloquea automáticamente por señales como:
  - "sin experiencia y gana miles"
  - "inversión inicial requerida"
  - Empresa sin nombre válido

### Botón  Buscar vacantes ahora
- Lanza el scraper en background
- Espera 3-5 minutos
- El dashboard se actualiza automáticamente

---

## Estructura del proyecto

```
cyberjob-hunter/
│
├── config.example.py          ← Plantilla de perfil (copia a config.py)
├── config.py                  ← Tu perfil personal (NO subir a GitHub)
├── requirements.txt           ← Dependencias Python
├── start.sh                   ← Script para levantar todo
├── README.md                  ← Este archivo
├── .gitignore                 ← Excluye config.py, data/, venv/
│
├── scraper/
│   └── indeed_scraper.py      ← Scraper Computrabajo + OCC + RemoteOK + Arbeitnow
│
├── api/
│   └── server.py              ← Servidor HTTP + proxy para Claude API
│
├── frontend/
│   └── index.html             ← Dashboard web completo
│
└── data/                      ← Generado automáticamente, NO en GitHub
    └── vacantes.json          ← Vacantes encontradas (se regenera solo)
```

---

## Solución de problemas

### Error: `No module named 'bs4'`
```bash
source venv/bin/activate
pip install beautifulsoup4
```

### Error: `venv/bin/activate: No such file or directory`
```bash
python3 -m venv venv
source venv/bin/activate
```

### El scraper encuentra 0 vacantes
```bash
# Verificar conexión a las plataformas
curl -s -o /dev/null -w "%{http_code}" https://mx.computrabajo.com
# Si sale 403 → espera 10 minutos e intenta de nuevo
```

### Claude devuelve error de API key
```bash
nano api/server.py
# Verifica que tu key empiece con sk-ant-
# y no tenga espacios al inicio/final
```

### Puerto 3001 ocupado
```bash
# Ver qué está usando el puerto
lsof -i :3001
# Matar el proceso
kill -9 PID_DEL_PROCESO
```

### El dashboard no carga en Windows
```bash
# Verificar que el servidor corre en WSL
python api/server.py
# Verificar IP de WSL
ip addr show eth0 | grep "inet "
# Si localhost no funciona, usar la IP de WSL directamente
```
---




##  Configurar Claude AI (requerido para cartas y entrevistas)

CyberJob Hunter usa **Claude AI de Anthropic** para generar cartas de presentación
personalizadas y prepararte para entrevistas técnicas.

>  Sin esta configuración el sistema igual funciona — puedes buscar vacantes,
> aprobarlas y verlas en el dashboard. Solo las funciones de IA no estarán disponibles.

---

### ¿Qué necesitas?

Una **API Key de Anthropic** — es diferente a la suscripción de Claude.ai Pro.
Son dos productos separados:

| Producto | Para qué sirve | Costo |
|---|---|---|
| **Claude.ai** (chat) | Hablar con Claude en el navegador | $20/mes |
| **API de Anthropic** | Que tus apps usen Claude | Por uso |

Para CyberJob Hunter necesitas la **API**, no la suscripción de chat.

---

### Pasos para obtener tu API Key

**1. Crear cuenta en Anthropic Console**
```
Ve a: https://console.anthropic.com
→ Sign up con tu email (o Google/GitHub)
→ Verifica tu email
```

**2. Agregar crédito**
```
console.anthropic.com → Billing → Add credit
→ Mínimo recomendado: $5 USD
→ Con $5 puedes generar ~1,600 cartas/entrevistas
→ Solo pagas lo que usas (no hay cobro mensual fijo)
```

**3. Generar tu API Key**
```
console.anthropic.com → API Keys → Create Key
→ Nombre: cyberjob-hunter
→ Clic Create Key
→ COPIA LA KEY — solo se muestra una vez
   Empieza con: sk-ant-...
```

**4. Pegar la key en el servidor**
```bash
nano api/server.py
# Busca esta línea:
ANTHROPIC_API_KEY = "sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX"
# Reemplaza con tu key real
# Guarda: Ctrl+O → Enter → Ctrl+X
```

**5. Reiniciar el servidor**
```bash
cd ~/cyberjob-hunter
source venv/bin/activate
python api/server.py
```

---

### ¿Cuánto cuesta en la práctica?

El modelo usado es **Claude Sonnet** — uno de los más económicos:

| Acción | Costo aproximado |
|---|---|
| Generar 1 carta de presentación | ~$0.003 USD |
| Preparar 1 sesión de entrevista | ~$0.004 USD |
| 100 cartas + 100 entrevistas | ~$0.70 USD |

Con **$5 USD** tienes suficiente para varios meses de uso normal.

---

### Verificar que funciona

Una vez configurada la key, entra al dashboard y haz clic en
**✉️ Carta IA** en cualquier vacante aprobada. Si genera la carta, todo está correcto.

Si ves un error `API key inválida`, verifica que copiaste la key completa
incluyendo el prefijo `sk-ant-`.


---

## Contribuir

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b feature/nueva-plataforma`
3. Haz tus cambios y commits: `git commit -m "feat: agregar LinkedIn scraper"`
4. Push: `git push origin feature/nueva-plataforma`
5. Abre un Pull Request

### Ideas para contribuir
- Scraper para LinkedIn Jobs
- Scraper para Glassdoor
- Soporte para más idiomas (inglés, portugués)
- Exportar vacantes a CSV/Excel
- Notificaciones por email cuando hay nuevas vacantes
- App móvil con React Native

---

## Licencia

MIT License — libre para uso personal y comercial.

---

## Autor

Ivan Mera :)

Desarrollado como proyecto de automatización de búsqueda de empleo en ciberseguridad.

*Powered by Claude AI (Anthropic) + Python + BeautifulSoup*
