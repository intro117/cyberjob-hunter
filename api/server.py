#!/usr/bin/env python3
import json, os, subprocess, threading, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import anthropic

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/vacantes.json")
FRONTEND  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend/index.html")

# ── PON TU API KEY AQUÍ ──────────────────────────────────
ANTHROPIC_API_KEY = "sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX"
# ────────────────────────────────────────────────────────

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_claude(prompt):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except anthropic.AuthenticationError:
        return "ERROR: API key inválida. Edita api/server.py y pon tu key de https://console.anthropic.com/"
    except Exception as e:
        return f"ERROR: {str(e)}"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self):
        with open(FRONTEND, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.send_html()
        elif path == "/api/vacantes":
            self.send_json(load())
        elif path == "/api/stats":
            v   = load()
            val = [x for x in v if x.get("empresa_validada")]
            self.send_json({
                "total":      len(v),
                "validas":    len(val),
                "pendientes": sum(1 for x in v if x.get("estado") == "pendiente"),
                "aprobadas":  sum(1 for x in v if x.get("estado") == "aprobada"),
                "rechazadas": sum(1 for x in v if x.get("estado") == "rechazada"),
                "bloqueadas": len(v) - len(val),
                "match_avg":  int(sum(x.get("match",0) for x in val) / max(len(val),1)),
            })
        elif path == "/api/scraper/run":
            def run():
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                subprocess.run(["python", "scraper/indeed_scraper.py"], cwd=base)
            threading.Thread(target=run, daemon=True).start()
            self.send_json({"ok": True})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()
        v    = body.get("vacante", {})

        if path == "/api/claude/carta":
            prompt = f"""Eres experto en cartas de presentación para ciberseguridad e IT.
Escribe una carta profesional en español, tono humano (NO corporativo), máximo 4 párrafos.

CANDIDATO: Sergio Iván Mera Aguilar
- 10+ años en ciberseguridad, redes y sistemas
- Skills: Wazuh, Suricata, ELK Stack, ISO 27001, Kali Linux, Fortinet, pfSense, Docker, Linux, Grafana, Prometheus
- Actual: Supervisor de Sistemas en Erillam Healthcare
- Antes: Subdirector de TI en gobierno de Morelos, coordinó con ITAM
- Proyectos: SIEM propio con ELK+Wazuh+Suricata, honeypots, monitoreo Prometheus+Grafana

VACANTE:
- Puesto: {v.get('puesto','')}
- Empresa: {v.get('empresa','')}
- Ubicación: {v.get('ubicacion','')}
- Descripción: {v.get('descripcion','')}
- Skills: {', '.join(v.get('requiere', []))}

ESTRUCTURA:
Párrafo 1: Por qué me interesa ESTA empresa y ESTE puesto
Párrafo 2: 2 logros concretos que encajan con los requisitos
Párrafo 3: Qué aportaré en los primeros 90 días
Párrafo 4: Cierre natural con llamada a acción

NO uses: "me complace", "adjunto mi CV", "estimado departamento"
SÍ menciona herramientas específicas de la vacante."""
            self.send_json({"texto": call_claude(prompt)})

        elif path == "/api/claude/entrevista":
            prompt = f"""Eres coach de entrevistas para ciberseguridad e IT en México.
Genera preguntas y respuestas modelo para esta vacante.

PUESTO: {v.get('puesto','')}
EMPRESA: {v.get('empresa','')}
DESCRIPCIÓN: {v.get('descripcion','')}
SKILLS: {', '.join(v.get('requiere', []))}

CANDIDATO: Sergio Iván Mera Aguilar
- 10+ años en ciberseguridad e infraestructura
- Implementó SIEM: Wazuh + Suricata + ELK Stack en producción
- ISO 27001, Kali Linux pentesting, Fortinet, pfSense, Docker, Linux
- Monitoreo: Prometheus + Grafana, honeypots para detección
- Supervisor en Erillam Healthcare (entorno crítico de salud)
- Subdirector de TI en gobierno estatal, coordinó con ITAM

Genera:
- 4 preguntas técnicas específicas para el puesto
- 2 preguntas conductuales

Formato por pregunta:
🔧 PREGUNTA [N]:
[La pregunta]

💬 RESPUESTA MODELO:
[Cómo respondería Sergio — natural, con ejemplos reales, 2-3 párrafos]

💡 TIP:
[Consejo corto específico]

---"""
            self.send_json({"texto": call_claude(prompt)})

        else:
            self.send_response(404); self.end_headers()

    def do_PUT(self):
        path = urlparse(self.path).path
        m    = re.match(r"/api/vacantes/([^/]+)/estado", path)
        if m:
            vid   = m.group(1)
            nuevo = self.read_body().get("estado", "pendiente")
            datos = load()
            for x in datos:
                if x["id"] == vid:
                    x["estado"] = nuevo
                    break
            save(datos)
            self.send_json({"ok": True})
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    port = 3001
    key_ok = "XXXXXXX" not in ANTHROPIC_API_KEY
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║   CyberJob Hunter — Servidor activo          ║")
    print(f"║   http://localhost:{port}                      ║")
    print(f"╠══════════════════════════════════════════════╣")
    if key_ok:
        print(f"║   ✓  Claude API configurada                  ║")
    else:
        print(f"║   ⚠️  Falta API key — edita api/server.py    ║")
    print(f"╚══════════════════════════════════════════════╝")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
