#!/usr/bin/env python3
"""
CyberJob Hunter — Scraper v5
Fixes: match recalibrado, OCC HTML directo, umbrales ajustados
"""
import requests, json, time, random, hashlib, os, re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../data/vacantes.json"
)

PERFIL_SKILLS = [
    "ciberseguridad","siem","wazuh","suricata","elasticsearch",
    "grafana","kali","iso 27001","fortinet","pfsense","linux",
    "docker","pentesting","soc","seguridad informatica","infraestructura",
    "monitoreo","firewall","vpn","ossec","prometheus","ids","ips",
    "cybersecurity","security engineer","administrador de sistemas","redes",
    "hacking","incidentes","vulnerabilidades","hardening","cyberark","pam",
    "sistemas","administrador","supervisor","infraestructura ti",
]

SKILLS_DETECTAR = [
    "wazuh","suricata","elasticsearch","grafana","prometheus","kali",
    "iso 27001","fortinet","pfsense","docker","linux","siem","soc",
    "splunk","vpn","vlan","bash","python","azure","aws","firewall",
    "ids","ips","ossec","nessus","cissp","ceh","crowdstrike",
    "ciberseguridad","pentesting","hardening","cyberark","pam",
    "incidentes","vulnerabilidades","devops","devsecops","redes",
    "infraestructura","sistemas","monitoreo","seguridad",
]

EXCLUIR_TITULO = [
    "seguridad social","imss","nómina","nomina","infonavit",
    "siroc","recursos humanos","rh ","contabilidad","contador",
    "ventas","marketing","diseño","chef","cocina","enfermera",
    "médico","medico","operador","almacén","almacen","logística",
    "logistica","chofer","conductor","cajero","camarero","camarera",
    "recepcionista","limpieza","mantenimiento general",
    "redes sociales","community manager","social media",
    "mini bodegas","naves industriales","sucursal",
    "practicante","pasante","becario",
    "control de calidad","costos","compras",
]

FRAUDE = [
    "sin experiencia y gana miles","gana desde casa fácil",
    "100% comisión sin sueldo base","dinero fácil desde casa",
    "negocio propio multinivel","inversión inicial requerida",
    "criptomonedas urgente","sin entrevista gana miles",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

def pausa(min_s=2.0, max_s=4.5):
    time.sleep(random.uniform(min_s, max_s))

def pausa_card(min_s=1.2, max_s=2.8):
    time.sleep(random.uniform(min_s, max_s))

def es_titulo_valido(titulo):
    t = titulo.lower()
    for excluir in EXCLUIR_TITULO:
        if excluir in t:
            return False
    return True

def match_score(titulo, desc):
    """
    Score v5 — calibrado para perfil Sergio:
    - Keyword en TÍTULO: 15 pts
    - Keyword en DESC:    5 pts
    - Skill técnico exacto: 10 pts
    - Cap: 99
    """
    titulo_l = titulo.lower()
    desc_l   = (desc or "").lower()

    # Keywords de área — peso por título vs descripción
    area_kw = [
        "ciberseguridad","cybersecurity","seguridad informática",
        "seguridad informatica","seguridad de la información",
        "infraestructura","soc","siem","redes","networking",
        "sistemas","linux","devops","devsecops","firewall",
        "pentesting","hacking ético","cyberark","pam","noc",
        "administrador","supervisor ti","supervisor sistemas",
    ]
    score = 0
    for kw in area_kw:
        if kw in titulo_l:
            score += 15
        elif kw in desc_l:
            score += 5

    # Skills técnicos específicos del perfil
    skills_kw = [
        "wazuh","suricata","fortinet","pfsense","kali","iso 27001",
        "elasticsearch","grafana","prometheus","ossec","splunk",
        "docker","kubernetes","bash","python","aws","azure",
        "nessus","cissp","ceh","crowdstrike","vpn","ids","ips",
        "syslog","snort","zeek","ansible","terraform",
    ]
    for kw in skills_kw:
        if kw in titulo_l:
            score += 12
        elif kw in desc_l:
            score += 10

    return min(score, 99)

def es_fraude(titulo, empresa, desc, salario):
    texto = (titulo + " " + empresa + " " + desc + " " + salario).lower()
    for f in FRAUDE:
        if f in texto:
            return True, f"Señal de fraude: '{f}'"
    if len(empresa.strip()) < 3:
        return True, "Empresa sin nombre válido"
    return False, "OK"

def gen_id(titulo, empresa):
    raw = f"{titulo.lower().strip()}{empresa.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]

def skills_en_texto(texto):
    t = texto.lower()
    return [
        s.upper() if len(s) <= 5 else s.title()
        for s in SKILLS_DETECTAR if s in t
    ][:7]

def fetch_desc_computrabajo(url, session):
    """Obtiene descripción completa de la página de la vacante en CT"""
    if not url or "computrabajo" not in url:
        return ""
    try:
        r = session.get(
            url,
            headers={**HEADERS, "Referer": "https://mx.computrabajo.com/"},
            timeout=15
        )
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        # CT mete la descripción en div.container — tomar el más largo
        candidates = []
        for div in soup.find_all("div", class_=True):
            cls = " ".join(div.get("class", []))
            if "container" in cls or "box_detail" in cls:
                txt = div.get_text(separator=" ", strip=True)
                # Limpiar navegación y textos de UI
                for noise in ["Oferta ocultaMostrar oferta","Ya aplicaste","Recuperar oferta",
                               "Ofertas ocultas","Deshacer","Buscar empleos"]:
                    txt = txt.replace(noise, "")
                txt = txt.strip()
                if len(txt) > 200:
                    candidates.append(txt)
        if candidates:
            # El más largo tiene la descripción completa
            best = max(candidates, key=len)
            # Extraer desde "Descripción de la oferta" si existe
            if "Descripción de la oferta" in best:
                best = best.split("Descripción de la oferta", 1)[1].strip()
            return best[:800]
        return ""
    except Exception:
        return ""

def hacer_vacante(titulo, empresa, ubic, salario, desc, url, plataforma, fecha="Reciente"):
    score = match_score(titulo, desc)
    fraude, razon = es_fraude(titulo, empresa, desc, salario)
    return {
        "id":               gen_id(titulo, empresa),
        "puesto":           titulo.strip(),
        "empresa":          empresa.strip(),
        "ubicacion":        ubic.strip(),
        "salario":          salario.strip() if salario else "Ver oferta",
        "descripcion":      desc.strip()[:450],
        "url":              url,
        "plataforma":       plataforma,
        "match":            score,
        "empresa_validada": not fraude,
        "razon_rechazo":    razon if fraude else None,
        "estado":           "pendiente",
        "fecha_publicacion": fecha,
        "fecha_encontrada": datetime.now().isoformat(),
        "requiere":         skills_en_texto(desc + " " + titulo),
    }

# ══════════════════════════════════════════════════════════
#  1. COMPUTRABAJO
# ══════════════════════════════════════════════════════════
def scrape_computrabajo(keyword):
    vacantes = []
    session  = requests.Session()
    slug     = re.sub(r'[^a-z0-9]+', '-', keyword.lower()).strip('-')
    url      = f"https://mx.computrabajo.com/trabajo-de-{slug}"

    print(f"  [CT] '{keyword}'", flush=True)
    try:
        r = session.get(
            url,
            headers={**HEADERS, "Referer": "https://www.google.com.mx/"},
            timeout=20, allow_redirects=True
        )
        if r.status_code != 200:
            print(f"    Status: {r.status_code}", flush=True)
            return vacantes

        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("article", class_="box_offer")
        print(f"    {len(cards)} tarjetas", flush=True)

        for card in cards:
            try:
                h2 = card.find("h2")
                if not h2:
                    continue
                titulo = h2.get_text(strip=True)
                for s in ["Postulado","Vista","Nuevo","Destacado","Premium"]:
                    titulo = titulo.replace(s, "").strip()
                if len(titulo) < 5:
                    continue
                if not es_titulo_valido(titulo):
                    continue

                emp_el  = card.find("p", class_=lambda c: c and "dFlex" in c and "fc_base" in c)
                empresa = emp_el.get_text(strip=True) if emp_el else "No especificada"
                empresa = re.sub(r'^\d+\.\d+', '', empresa).strip()

                ps   = card.find_all("p", class_=re.compile("fc_base"))
                ubic = ps[1].get_text(strip=True) if len(ps) > 1 else "México"

                fecha_el = card.find("p", class_=re.compile("fc_aux"))
                fecha    = fecha_el.get_text(strip=True) if fecha_el else "Reciente"
                fecha    = re.sub(r'\s+', ' ', fecha).strip()

                a    = card.find("a", href=True)
                link = ("https://mx.computrabajo.com" + a["href"]
                        if a and a["href"].startswith("/") else
                        a["href"] if a else "")

                # Obtener descripción completa desde la página individual
                desc_full = fetch_desc_computrabajo(link, session)
                # Limpiar texto sucio del botón toggle de CT
                desc_full = desc_full.replace("Oferta ocultaMostrar oferta","").strip()
                desc = desc_full if len(desc_full) > 60 else titulo

                v = hacer_vacante(titulo, empresa, ubic, "Ver oferta", desc, link, "Computrabajo", fecha)
                if v["match"] >= 15:
                    vacantes.append(v)
                    print(f"    ✓ {v['match']:3}% | {titulo[:42]} — {empresa[:22]}", flush=True)

            except Exception:
                continue
            pausa_card()
        pausa()
    except Exception as e:
        print(f"    ✗ {e}", flush=True)

    print(f"    → {len(vacantes)} relevantes", flush=True)
    return vacantes

# ══════════════════════════════════════════════════════════
#  2. OCC — GraphQL/JSON endpoint público
# ══════════════════════════════════════════════════════════
def scrape_occ(keyword):
    vacantes = []
    session  = requests.Session()
    print(f"  [OCC] '{keyword}'", flush=True)
    try:
        # OCC expone un endpoint de búsqueda usado por su app móvil
        headers_occ = {
            "User-Agent":   "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36",
            "Accept":       "application/json",
            "Referer":      "https://www.occ.com.mx/",
            "Origin":       "https://www.occ.com.mx",
        }
        params = {
            "q":        keyword,
            "location": "Mexico",
            "l":        "mexico",
            "rows":     20,
            "start":    0,
        }
        r = session.get(
            "https://www.occ.com.mx/empleos/",
            params={"q": keyword},
            headers={**HEADERS, "Referer": "https://www.google.com.mx/"},
            timeout=20,
            allow_redirects=True,
        )
        print(f"    Status HTML: {r.status_code}", flush=True)
        if r.status_code != 200:
            return vacantes

        soup = BeautifulSoup(r.text, "html.parser")

        # OCC inyecta datos en __NEXT_DATA__ (Next.js)
        script = soup.find("script", id="__NEXT_DATA__")
        if script:
            try:
                data  = json.loads(script.string)
                # Navegar el árbol hasta los jobs
                props = data.get("props",{}).get("pageProps",{})
                jobs  = (props.get("jobs") or
                         props.get("vacancies") or
                         props.get("results") or
                         props.get("data",{}).get("jobs") or [])
                print(f"    __NEXT_DATA__ jobs: {len(jobs)}", flush=True)
                for job in jobs:
                    titulo  = str(job.get("title","") or job.get("name",""))
                    empresa = str(job.get("company","") or job.get("companyName","") or "No especificada")
                    ubic    = str(job.get("location","") or job.get("city","") or "México")
                    sal     = str(job.get("salary","") or job.get("salaryText","") or "Ver oferta")
                    desc    = BeautifulSoup(
                        str(job.get("description","") or job.get("shortDescription","") or titulo),
                        "html.parser"
                    ).get_text()[:450]
                    path    = str(job.get("url","") or job.get("path","") or "")
                    link    = path if path.startswith("http") else f"https://www.occ.com.mx{path}"

                    if not titulo or not es_titulo_valido(titulo):
                        continue
                    v = hacer_vacante(titulo, empresa, ubic, sal, desc, link, "OCC Mundial")
                    if v["match"] >= 15:
                        vacantes.append(v)
                        print(f"    ✓ {v['match']:3}% | {titulo[:42]} — {empresa[:22]}", flush=True)
            except Exception as e:
                print(f"    __NEXT_DATA__ error: {e}", flush=True)
        else:
            # Fallback: buscar JSON embebido en window.__data__ u otros patterns
            matches = re.findall(r'window\.__(?:data|store|state)__\s*=\s*(\{.+?\});', r.text, re.S)
            print(f"    window.__data__ matches: {len(matches)}", flush=True)

        pausa()
    except Exception as e:
        print(f"    ✗ {e}", flush=True)

    print(f"    → {len(vacantes)} relevantes", flush=True)
    return vacantes

# ══════════════════════════════════════════════════════════
#  3. REMOTEOK
# ══════════════════════════════════════════════════════════
TAGS_OBJETIVO = {
    "security","devops","linux","sysadmin","cloud","infra",
    "infrastructure","networking","python","aws","azure","gcp",
    "devsecops","sre","monitoring","docker","backend","golang",
    "infosec","sys admin","engineer",
}

def scrape_remoteok():
    vacantes = []
    print(f"  [RemoteOK] API...", flush=True)
    try:
        r = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "CyberJobHunter/4.0", "Accept": "application/json"},
            timeout=20
        )
        if r.status_code != 200:
            print(f"    Status: {r.status_code}", flush=True)
            return vacantes

        todos = r.json()
        jobs  = [j for j in todos if isinstance(j, dict) and j.get("position")]
        print(f"    Jobs en API: {len(jobs)}", flush=True)

        for job in jobs:
            titulo  = str(job.get("position",""))
            empresa = str(job.get("company","No especificada"))
            tags    = [str(t).lower() for t in job.get("tags", [])]
            desc_raw= str(job.get("description",""))
            desc    = BeautifulSoup(desc_raw, "html.parser").get_text()[:450]

            tag_match   = bool(TAGS_OBJETIVO & set(tags))
            title_match = any(kw in titulo.lower() for kw in [
                "security","cybersecurity","devops","sysadmin",
                "linux","infrastructure","network","infra","sre",
                "engineer","admin","cloud",
            ])

            if not tag_match and not title_match:
                continue
            if not es_titulo_valido(titulo):
                continue

            sal_min = job.get("salary_min")
            sal_max = job.get("salary_max")
            if sal_min and sal_max:
                salario = f"${int(sal_min):,} - ${int(sal_max):,} USD/año"
            elif sal_min:
                salario = f"Desde ${int(sal_min):,} USD/año"
            else:
                salario = "Ver oferta"

            fecha = str(job.get("date",""))[:10] or "Reciente"
            link  = str(job.get("apply_url","") or job.get("url",""))

            v = hacer_vacante(titulo, empresa, "Remoto Internacional",
                              salario, desc, link, "RemoteOK", fecha)
            if v["match"] >= 15:
                vacantes.append(v)
                print(f"    ✓ {v['match']:3}% | {titulo[:42]} — {empresa[:22]}", flush=True)

        pausa()
    except Exception as e:
        print(f"    ✗ {e}", flush=True)

    print(f"    → {len(vacantes)} relevantes", flush=True)
    return vacantes

# ══════════════════════════════════════════════════════════
#  4. ARBEITNOW
# ══════════════════════════════════════════════════════════
def scrape_arbeitnow():
    vacantes = []
    print(f"  [Arbeitnow] API...", flush=True)
    try:
        r = requests.get(
            "https://www.arbeitnow.com/api/job-board-api",
            headers={"Accept": "application/json"},
            timeout=15
        )
        if r.status_code != 200:
            print(f"    Status: {r.status_code}", flush=True)
            return vacantes

        data = r.json()
        jobs = data.get("data", [])
        print(f"    Jobs: {len(jobs)}", flush=True)

        for job in jobs:
            titulo  = str(job.get("title",""))
            empresa = str(job.get("company_name","No especificada"))

            raw_tags = job.get("tags", [])
            if raw_tags and isinstance(raw_tags[0], dict):
                tags = [str(t.get("value","")) for t in raw_tags]
            else:
                tags = [str(t) for t in raw_tags]
            tags_str = " ".join(tags).lower()

            desc_raw = str(job.get("description",""))
            desc     = BeautifulSoup(desc_raw, "html.parser").get_text()[:450]
            remoto   = job.get("remote", False)
            ubic     = "Remoto Internacional" if remoto else str(job.get("location","Internacional"))
            link     = str(job.get("url",""))
            fecha    = str(job.get("created_at",""))[:10] or "Reciente"

            if not es_titulo_valido(titulo):
                continue

            es_tech = any(kw in (titulo + " " + tags_str).lower() for kw in [
                "security","cybersecurity","devops","linux","sysadmin",
                "infrastructure","network","cloud","sre","devsecops",
                "infra","monitoring","firewall","backend","python",
                "engineer","admin","systems","seguridad","sistemas",
            ])
            if not es_tech:
                continue
            # Excluir falsos positivos de Arbeitnow
            titulo_lower = titulo.lower()
            if any(fp in titulo_lower for fp in [
                "social media","marketing","sales","content","design",
                "student","werkstudent","praktikant","hr ","recruiter",
                "accountant","finance","legal","medical","nurse",
            ]):
                continue

            v = hacer_vacante(titulo, empresa, ubic, "Ver oferta",
                              desc, link, "Arbeitnow", fecha)
            if v["match"] >= 15:
                vacantes.append(v)
                print(f"    ✓ {v['match']:3}% | {titulo[:42]} — {empresa[:22]}", flush=True)

        pausa()
    except Exception as e:
        print(f"    ✗ {e}", flush=True)

    print(f"    → {len(vacantes)} relevantes", flush=True)
    return vacantes

# ── Deduplicar ────────────────────────────────────────────
def dedup(vacantes):
    seen, result = set(), []
    for v in vacantes:
        if v["id"] not in seen:
            seen.add(v["id"])
            result.append(v)
    return result

# ── Guardar preservando estados del usuario ───────────────
def guardar(vacantes):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    estados = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, encoding="utf-8") as f:
                for v in json.load(f):
                    estados[v["id"]] = v.get("estado","pendiente")
        except Exception:
            pass
    for v in vacantes:
        if v["id"] in estados:
            v["estado"] = estados[v["id"]]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(vacantes, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Guardado: {OUTPUT_FILE}")

# ── MAIN ──────────────────────────────────────────────────
CT_KEYWORDS = [
    "ciberseguridad",
    "seguridad informatica",
    "SOC analista",
    "administrador sistemas linux",
    "ingeniero seguridad redes",
    "infraestructura TI",
    "analista seguridad",
    "DevOps seguridad",
    "supervisor sistemas",
    "administrador redes",
]

OCC_KEYWORDS = [
    "ciberseguridad",
    "seguridad-informatica",
    "administrador-linux",
    "infraestructura-ti",
    "soc-analista",
]

if __name__ == "__main__":
    print("=" * 58)
    print("  CyberJob Hunter — Scraper v5")
    print(f"  Perfil: Sergio Iván Mera — Ciberseguridad/IT")
    print(f"  Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 58)

    todas = []

    print("\n[1/4] Computrabajo México...")
    for kw in CT_KEYWORDS:
        todas += scrape_computrabajo(kw)

    print("\n[2/4] OCC Mundial...")
    for kw in OCC_KEYWORDS:
        todas += scrape_occ(kw)

    print("\n[3/4] RemoteOK...")
    todas += scrape_remoteok()

    print("\n[4/4] Arbeitnow...")
    todas += scrape_arbeitnow()

    todas = dedup(todas)
    todas.sort(key=lambda x: x["match"], reverse=True)

    validas    = [v for v in todas if v["empresa_validada"]]
    bloqueadas = [v for v in todas if not v["empresa_validada"]]

    print(f"\n{'='*58}")
    print(f"  Total      : {len(todas)}")
    print(f"  Válidas    : {len(validas)}")
    print(f"  Bloqueadas : {len(bloqueadas)}")

    if validas:
        avg = int(sum(v['match'] for v in validas) / len(validas))
        print(f"  Match avg  : {avg}%")
        print(f"\n  TOP 15:")
        print(f"  {'%':>4}  {'Puesto':42}  {'Empresa':22}  Fuente")
        print(f"  {'-'*95}")
        for v in validas[:15]:
            print(f"  {v['match']:3}%  {v['puesto'][:42]:42}  {v['empresa'][:22]:22}  {v['plataforma']}")

    print("=" * 58)
    guardar(todas)
