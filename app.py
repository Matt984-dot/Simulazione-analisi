from datetime import datetime
import json
import random
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulazione Esonero Analisi Superiore",
    page_icon="📐",
    layout="centered",
)

FILE_ESONERI = {
    "1° Esonero": "domande.json",
    "2° Esonero": "domande2.json",
}

COLONNE_FOGLIO = [
    "timestamp",
    "giocatore",
    "esonero",
    "argomento",
    "punteggio",
    "totale",
    "errori_json",
]

NOMI_PREDEFINITI = ["Matteo (creatore)", "Matteo (beta tester)"]
CHIAVI_PROFILO = ("giocatore_nome", "select_giocatore", "input_giocatore_nuovo")


def resetta_stato_sessione(preserva_chiavi=()):
  chiavi_da_tenere = set(CHIAVI_PROFILO) | set(preserva_chiavi)
  for k in list(st.session_state.keys()):
    if k not in chiavi_da_tenere:
      del st.session_state[k]


@st.cache_resource
def get_worksheet():
  if "gcp_service_account" not in st.secrets or "sheets" not in st.secrets:
    return None
  scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(
      st.secrets["gcp_service_account"], scopes=scopes
  )
  client = gspread.authorize(creds)
  sh = client.open_by_key(st.secrets["sheets"]["spreadsheet_id"])
  ws_name = st.secrets["sheets"].get("worksheet_name", "Foglio1")
  ws = sh.worksheet(ws_name)
  if not ws.row_values(1):
    ws.append_row(COLONNE_FOGLIO)
  return ws


def salva_tentativo_sheets(
    giocatore, esonero, argomento, punteggio, totale, domande_errori
):
  ws = get_worksheet()
  if ws is None:
    return False
  try:
    errori_payload = [
        {
            "id": q.get("id", q.get("nota", f"domanda_{idx}")),
            "nota": q.get("nota", ""),
            "argomenti": estrai_argomenti(q),
            "domanda": q.get("domanda", "")[:120],
        }
        for idx, q in enumerate(domande_errori)
    ]
    riga = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        giocatore,
        esonero,
        argomento,
        int(punteggio),
        int(totale),
        json.dumps(errori_payload, ensure_ascii=False),
    ]
    ws.append_row(riga)
    carica_statistiche.clear()
    return True
  except Exception as e:
    st.warning(f"Impossibile salvare su Google Sheets al momento: {e}")
    return False


@st.cache_data(ttl=30)
def carica_statistiche():
  ws = get_worksheet()
  if ws is None:
    return []
  try:
    return ws.get_all_records()
  except Exception as e:
    st.warning(f"Errore nel leggere le statistiche da Google Sheets: {e}")
    return []


def carica_domande(percorso_file):
  try:
    with open(percorso_file, "r", encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    st.error(f"File '{percorso_file}' non trovato nella cartella!")
    return []


def estrai_argomenti(q):
  raw = q.get("argomento") if "argomento" in q else q.get("argomenti")
  if isinstance(raw, list):
    puliti = [str(a).strip() for a in raw if str(a).strip()]
    return puliti if puliti else ["Da classificare"]
  if isinstance(raw, str) and raw.strip():
    return [raw.strip()]
  return ["Da classificare"]


def pulisci_stringa(s):
  if isinstance(s, str):
    return s.replace(" ", "").strip()
  return s


def verifica_risposta_singola(risposta_data, risposta_corretta, tipo):
  if tipo == "multipla":
    user_set = (
        {pulisci_stringa(x) for x in risposta_data} if risposta_data else set()
    )
    if isinstance(risposta_corretta, list):
      corr_set = {pulisci_stringa(x) for x in risposta_corretta}
    else:
      corr_set = {pulisci_stringa(risposta_corretta)}
    return user_set == corr_set
  else:
    user_ans_str = pulisci_stringa(str(risposta_data)) if risposta_data else ""
    corr_ans_str = pulisci_stringa(str(risposta_corretta))
    return user_ans_str.lower() == corr_ans_str.lower()


def seleziona_giocatore_sidebar():
  nome_salvato = st.session_state.get("giocatore_nome", NOMI_PREDEFINITI[0])
  indice_iniziale = (
      NOMI_PREDEFINITI.index(nome_salvato)
      if nome_salvato in NOMI_PREDEFINITI[:-1]
      else len(NOMI_PREDEFINITI) - 1
  )

  scelta_profilo = st.sidebar.selectbox(
      "Seleziona il giocatore:",
      NOMI_PREDEFINITI,
      index=indice_iniziale,
      key="select_giocatore",
  )

  if scelta_profilo == "Altro...":
    valore_iniziale = (
        "" if nome_salvato in NOMI_PREDEFINITI[:-1] else nome_salvato
    )
    giocatore_scelto = (
        st.sidebar.text_input(
            "Inserisci un nuovo nome:",
            value=valore_iniziale,
            key="input_giocatore_nuovo",
        ).strip()
        or "Giocatore 3"
    )
  else:
    giocatore_scelto = scelta_profilo

  st.session_state.giocatore_nome = giocatore_scelto
  return giocatore_scelto


def mostra_statistiche():
  st.header("📊 Statistiche e Progressi")

  if get_worksheet() is None:
    st.info(
        "Collega **Google Sheets** tramite `st.secrets` (`[gcp_service_account]`"
        " e `[sheets]`) per attivare il salvataggio automatico e il"
        " confronto tra giocatori."
    )
    return

  records = carica_statistiche()
  if not records:
    st.info(
        "Nessun tentativo registrato ancora. Completa un esame o una"
        " sessione di allenamento per iniziare!"
    )
    return

  giocatori = sorted(
      list({
          str(r.get("giocatore", "")).strip()
          for r in records
          if r.get("giocatore")
      })
  )
  col1, col2 = st.columns(2)
  with col1:
    filtro_giocatore = st.selectbox(
        "Filtra per giocatore:", ["Tutti"] + giocatori
    )
  with col2:
    filtro_esonero = st.selectbox(
        "Filtra per test:", ["Tutti", "1° Esonero", "2° Esonero"]
    )

  filtrati = []
  for r in records:
    if (
        filtro_giocatore != "Tutti"
        and str(r.get("giocatore")) != filtro_giocatore
    ):
      continue
    if filtro_esonero != "Tutti" and str(r.get("esonero")) != filtro_esonero:
      continue
    filtrati.append(r)

  if not filtrati:
    st.warning("Nessun dato per i filtri selezionati.")
    return

  tentativi = len(filtrati)
  percentuali = []
  conteggio_errori = {}

  for r in filtrati:
    p = r.get("punteggio", 0)
    t = r.get("totale", 0)
    if isinstance(t, (int, float)) and t > 0:
      percentuali.append((p / t) * 100)
    raw_err = r.get("errori_json", "[]")
    try:
      errori_list = (
          json.loads(raw_err) if isinstance(raw_err, str) else (raw_err or [])
      )
    except Exception:
      errori_list = []

    for err in errori_list:
      chiave = err.get("id") or err.get("domanda") or "Domanda sconosciuta"
      if chiave not in conteggio_errori:
        conteggio_errori[chiave] = {
            "errori": 0,
            "nota": err.get("nota", ""),
            "argomenti": ", ".join(err.get("argomenti", [])),
            "domanda": err.get("domanda", ""),
        }
      conteggio_errori[chiave]["errori"] += 1

  media_pct = round(sum(percentuali) / len(percentuali), 1) if percentuali else 0
  miglior_pct = round(max(percentuali), 1) if percentuali else 0

  m1, m2, m3 = st.columns(3)
  m1.metric("Tentativi", tentativi)
  m2.metric("Media punteggio", f"{media_pct}%")
  m3.metric("Miglior risultato", f"{miglior_pct}%")

  st.divider()
  st.subheader("📈 Andamento punteggi e tentativi")

  righe_grafico = []
  for idx, r in enumerate(filtrati, start=1):
    p = r.get("punteggio", 0)
    t = r.get("totale", 0)
    pct = (
        round((p / t) * 100, 1)
        if isinstance(t, (int, float)) and t > 0
        else 0.0
    )
    ts_raw = str(r.get("timestamp", ""))
    giorno = ts_raw[:10] if len(ts_raw) >= 10 else f"Tentativo {idx}"
    righe_grafico.append({
        "ordine": f"#{idx} ({ts_raw[5:16]})" if len(ts_raw) >= 16 else f"#{idx}",
        "giorno": giorno,
        "giocatore": str(r.get("giocatore", "")),
        "percentuale": pct,
        "tentativi": 1,
    })

  df_graf = pd.DataFrame(righe_grafico)

  st.caption("Andamento % punteggio per tentativo")
  st.line_chart(df_graf.set_index("ordine")["percentuale"])

  if filtro_giocatore == "Tutti" and df_graf["giocatore"].nunique() > 1:
    st.caption("Tentativi per giocatore e giorno")
    pivot_gioc = df_graf.pivot_table(
        index="giorno",
        columns="giocatore",
        values="tentativi",
        aggfunc="sum",
        fill_value=0,
    )
    st.bar_chart(pivot_gioc)
  else:
    st.caption("Numero di tentativi per giorno")
    tentativi_giorno = df_graf.groupby("giorno", sort=False)["tentativi"].sum()
    st.bar_chart(tentativi_giorno)

  st.divider()
  st.subheader("🎯 Domande sbagliate più spesso")

  if not conteggio_errori:
    st.success("Nessun errore registrato per questa selezione!")
  else:
    classifica = sorted(
        conteggio_errori.values(), key=lambda x: x["errori"], reverse=True
    )[:10]
    for item in classifica:
      etichetta = f"**{item['errori']} errori**"
      if item["nota"]:
        etichetta += f" — *{item['nota']}*"
      if item["argomenti"]:
        etichetta += f" · `{item['argomenti']}`"
      st.markdown(f"* {etichetta}")
      if item["domanda"]:
        st.caption(item["domanda"])

  st.divider()
  st.subheader("🕒 Ultimi tentativi")
  tabella_storico = [
      {
          "Data/Ora": r.get("timestamp", ""),
          "Giocatore": r.get("giocatore", ""),
          "Test": r.get("esonero", ""),
          "Argomento": r.get("argomento", ""),
          "Punteggio": f"{r.get('punteggio', 0)}/{r.get('totale', 0)}",
      }
      for r in reversed(filtrati[-20:])
  ]
  st.dataframe(tabella_storico, use_container_width=True, hide_index=True)


def main():
  st.title("Simulazione Esonero Analisi Superiore")

  st.sidebar.header("🧭 Navigazione e Profilo")
  sezione = st.sidebar.radio(
      "Vai a:",
      ("📝 Simulazione / Allenamento", "📊 Statistiche"),
  )

  giocatore_scelto = seleziona_giocatore_sidebar()

  if sezione == "📊 Statistiche":
    mostra_statistiche()
    return

  st.sidebar.divider()
  st.sidebar.header("⚙️ Impostazioni Test")

  esonero_scelto = st.sidebar.selectbox(
      "Seleziona il test:",
      list(FILE_ESONERI.keys()),
      index=1,
  )
  file_domande_scelto = FILE_ESONERI[esonero_scelto]

  tutte_le_domande = carica_domande(file_domande_scelto)
  if not tutte_le_domande:
    return

  argomento_scelto = "Tutti gli argomenti"
  domande_filtrate = tutte_le_domande

  if esonero_scelto == "2° Esonero":
    st.sidebar.divider()
    st.sidebar.subheader("🏷️ Filtro Argomento")
    tutte_etichette = set()
    for q in tutte_le_domande:
      tutte_etichette.update(estrai_argomenti(q))

    argomenti_disponibili = sorted(list(tutte_etichette))
    opzioni_argomento = ["Tutti gli argomenti"] + argomenti_disponibili
    argomento_scelto = st.sidebar.selectbox(
        "Seleziona l'argomento:", opzioni_argomento
    )

    if argomento_scelto != "Tutti gli argomenti":
      domande_filtrate = [
          q for q in tutte_le_domande if argomento_scelto in estrai_argomenti(q)
      ]

  if not domande_filtrate:
    st.warning("Nessuna domanda trovata per l'argomento selezionato.")
    return

  modalita = st.sidebar.radio(
      "Scegli la modalità:",
      (
          "Modalità Esame (Tutte insieme)",
          "Modalità Allenamento (Casuali, una per volta)",
      ),
  )

  max_q = len(domande_filtrate)
  if max_q <= 1:
    num_pesca = max_q
    st.sidebar.info(f"Domande disponibili: **{max_q}**")
  else:
    max_slider = min(50, max_q)
    default_val = min(20, max_slider)
    num_pesca = st.sidebar.slider(
        "Numero di domande da estrarre:",
        min_value=1,
        max_value=max_slider,
        value=default_val,
    )

  stato_corrente = (
      file_domande_scelto,
      argomento_scelto,
      modalita,
      num_pesca,
  )
  if (
      "stato_prec" not in st.session_state
      or st.session_state.stato_prec != stato_corrente
  ):
    st.session_state.stato_prec = stato_corrente
    resetta_stato_sessione(preserva_chiavi=("stato_prec",))
    st.rerun()

  if "domande_test" not in st.session_state:
    st.session_state.domande_test = random.sample(domande_filtrate, num_pesca)

  domande = st.session_state.domande_test

  # ==========================================
  # MODALITÀ 1: ESAME
  # ==========================================
  if "Modalità Esame" in modalita:
    if not st.session_state.get("risposte_inviate", False):
      with st.form("form_quiz"):
        st.info(
            f"📝 **{esonero_scelto} ({argomento_scelto}) — Giocatore:"
            f" {giocatore_scelto}** · {len(domande)} domande."
        )

        for i, q in enumerate(domande):
          st.markdown(f"### Domanda {i + 1}")
          if "nota" in q:
            st.caption(f"*{q['nota']}*")
          st.markdown(q["domanda"])

          tipo = q.get("tipo", "vero_falso")
          if tipo == "vero_falso":
            st.radio(
                "Seleziona un'opzione:",
                q["opzioni"],
                key=f"q_{i}",
                index=None,
                format_func=lambda x: f"{x}",
            )
          elif tipo == "multipla":
            st.write("Seleziona tutte le risposte corrette:")
            for opt_idx, opzione in enumerate(q["opzioni"]):
              st.checkbox(opzione, key=f"q_{i}_opt_{opt_idx}")
          elif tipo == "aperta":
            st.text_input("Inserisci la tua risposta:", key=f"q_{i}")

          st.divider()

        if st.form_submit_button("Invia risposte e vedi risultati"):
          for i, q in enumerate(domande):
            if q.get("tipo", "vero_falso") == "multipla":
              selected = [
                  opzione
                  for opt_idx, opzione in enumerate(q["opzioni"])
                  if st.session_state.get(f"q_{i}_opt_{opt_idx}", False)
              ]
              st.session_state[f"q_{i}"] = selected
          st.session_state.risposte_inviate = True
          st.session_state.salvatro_esame = False
          st.rerun()

    else:
      st.header(f"Risultati e Spiegazioni — {esonero_scelto}")
      punteggio = 0
      totale = len(domande)
      domande_errori = []

      for i, q in enumerate(domande):
        risposta_data = st.session_state.get(f"q_{i}")
        risposta_corretta = q["risposta_corretta"]
        tipo = q.get("tipo", "vero_falso")

        st.markdown(f"**Domanda {i + 1}:** {q['domanda']}")
        is_correct = verifica_risposta_singola(
            risposta_data, risposta_corretta, tipo
        )

        if tipo == "multipla":
          user_str = (
              ", ".join(risposta_data) if risposta_data else "Nessuna risposta"
          )
          corr_str = (
              ", ".join(risposta_corretta)
              if isinstance(risposta_corretta, list)
              else str(risposta_corretta)
          )
        else:
          user_str = str(risposta_data) if risposta_data else "Nessuna risposta"
          corr_str = str(risposta_corretta)

        if is_correct:
          st.success(f"La tua risposta: **{user_str}** — **Corretta!** ✅")
          punteggio += 1
        else:
          domande_errori.append(q)
          st.error(
              f"La tua risposta: **{user_str}** — La risposta corretta era:"
              f" **{corr_str}** ❌"
          )

        with st.expander("🔍 Mostra spiegazione dettagliata"):
          st.markdown(q["spiegazione"])
        st.divider()

      if not st.session_state.get("salvatro_esame", False):
        salva_tentativo_sheets(
            giocatore_scelto,
            esonero_scelto,
            argomento_scelto,
            punteggio,
            totale,
            domande_errori,
        )
        st.session_state.salvatro_esame = True

      percentuale = round((punteggio / totale) * 100, 1) if totale > 0 else 0
      st.subheader(f"Punteggio finale: {punteggio} su {totale} ({percentuale}%)")

      if st.button("Ricomincia il test"):
        resetta_stato_sessione(preserva_chiavi=("stato_prec",))
        st.rerun()

  # ==========================================
  # MODALITÀ 2: ALLENAMENTO
  # ==========================================
  else:
    if "indice_allenamento" not in st.session_state:
      st.session_state.indice_allenamento = 0
      st.session_state.punteggio_allenamento = 0
      st.session_state.verificato_corrente = False
      st.session_state.errori_allenamento = []
      st.session_state.salvatro_allenamento = False

    idx = st.session_state.indice_allenamento
    totale = len(domande)

    if idx < totale:
      q = domande[idx]
      st.progress((idx + 1) / totale)

      nota_testo = f" — *{q['nota']}*" if "nota" in q else ""
      st.caption(
          f"{giocatore_scelto} · {esonero_scelto} · Domanda {idx + 1} di"
          f" {totale}{nota_testo}"
      )

      st.markdown(f"### {q['domanda']}")
      tipo = q.get("tipo", "vero_falso")

      if tipo == "vero_falso":
        risposta_utente = st.radio(
            "Seleziona un'opzione:",
            q["opzioni"],
            key=f"train_q_{idx}",
            index=None,
            format_func=lambda x: f"{x}",
        )
      elif tipo == "multipla":
        st.write("Seleziona tutte le risposte corrette:")
        risposta_utente = []
        for opt_idx, opzione in enumerate(q["opzioni"]):
          if st.checkbox(opzione, key=f"train_q_{idx}_opt_{opt_idx}"):
            risposta_utente.append(opzione)
      elif tipo == "aperta":
        risposta_utente = st.text_input(
            "Inserisci la tua risposta:", key=f"train_q_{idx}"
        )

      st.markdown("---")

      if not st.session_state.verificato_corrente:
        if st.button("Verifica Risposta", type="primary"):
          st.session_state.verificato_corrente = True
          st.rerun()
      else:
        is_correct = verifica_risposta_singola(
            risposta_utente, q["risposta_corretta"], tipo
        )

        if is_correct:
          st.success("🎉 **Risposta Corretta!**")
          if f"registrato_{idx}" not in st.session_state:
            st.session_state.punteggio_allenamento += 1
            st.session_state[f"registrato_{idx}"] = True
        else:
          st.error("❌ **Risposta Errata.**")
          if f"registrato_{idx}" not in st.session_state:
            st.session_state.errori_allenamento.append(q)
            st.session_state[f"registrato_{idx}"] = True
          if isinstance(q["risposta_corretta"], list):
            corr_str = ", ".join(q["risposta_corretta"])
          else:
            corr_str = str(q["risposta_corretta"])
          st.info(f"La risposta corretta era: `{corr_str}`")

        if "spiegazione" in q and q["spiegazione"]:
          st.markdown(f"> **Spiegazione:** {q['spiegazione']}")

        if st.button("Prossima Domanda ➡️"):
          st.session_state.verificato_corrente = False
          st.session_state.indice_allenamento += 1
          st.rerun()

    else:
      punteggio = st.session_state.punteggio_allenamento
      if not st.session_state.get("salvatro_allenamento", False):
        salva_tentativo_sheets(
            giocatore_scelto,
            esonero_scelto,
            argomento_scelto,
            punteggio,
            totale,
            st.session_state.errori_allenamento,
        )
        st.session_state.salvatro_allenamento = True

      st.header("Sessione di allenamento completata! 🎉")
      percentuale = round((punteggio / totale) * 100, 1) if totale > 0 else 0
      st.subheader(
          f"Hai totalizzato {punteggio} su {totale} ({percentuale}%)"
      )

      if st.button("Nuova sessione di allenamento casuale"):
        resetta_stato_sessione(preserva_chiavi=("stato_prec",))
        st.rerun()


if __name__ == "__main__":
  main()