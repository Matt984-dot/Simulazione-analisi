import json
import random
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Simulatore Esame - Advanced Analysis", page_icon="📚", layout="centered"
)


# Funzione per caricare le domande dal file JSON
@st.cache_data
def carica_domande():
  try:
    with open("domande.json", "r", encoding="utf-8") as f:
      return json.loadf(f) if hasattr(json, "loadf") else json.load(f)
  except FileNotFoundError:
    return []


tutte_le_domande = carica_domande()

st.title("🎓 Simulatore d'Esame: Advanced Analysis")
st.write(
    "Mettiti alla prova con le domande del corso. Buono studio e buon divertimento!"
)

if not tutte_le_domande:
  st.error(
      "⚠️ Non è stato trovato alcun file `domande.json` o il file è vuoto."
      " Caricalo nel repository per iniziare!"
  )
else:
  # Inizializzazione dello stato della sessione per la simulazione
  if "domande_selezionate" not in st.session_state:
    # Estrae casualmente fino a 10 domande (o meno se il database ne ha di meno)
    num_pesca = min(10, len(tutte_le_domande))
    st.session_state.domande_selezionate = random.sample(
        tutte_le_domande, num_pesca
    )
    st.session_state.risposte_utente = {}
    st.session_state.inviato = False

  # Bottone per rigenerare una nuova simulazione
  if st.button("🔄 Nuova Simulazione (Estrai altre domande)"):
    num_pesca = min(8, len(tutte_le_domande))
    st.session_state.domande_selezionate = random.sample(
        tutte_le_domande, num_pesca
    )
    st.session_state.risposte_utente = {}
    st.session_state.inviato = False
    st.rerun()

  st.divider()

  # Form principale della simulazione
  with st.form("form_simulazione"):
    punteggio = 0
    totale = len(st.session_state.domande_selezionate)

    for i, q in enumerate(st.session_state.domande_selezionate):
      st.markdown(f"### Domanda {i + 1} di {totale}")
      if "nota" in q and q["nota"]:
        st.caption(f"📌 {q['nota']}")

      st.markdown(q["domanda"])

      # Visualizzazione in base al tipo di domanda
      if q["tipo"] == "vero_falso":
        opzioni = ["-- Seleziona --"] + q["opzioni"]
        risposta = st.radio(
            "La tua risposta:", opzioni, key=f"q_{q['id']}", index=0
        )
        st.session_state.risposte_utente[q["id"]] = risposta

      elif q["tipo"] == "aperta":
        risposta = st.text_input(
            "Scrivi la tua risposta:", key=f"q_{q['id']}"
        )
        st.session_state.risposte_utente[q["id"]] = risposta

      elif q["tipo"] == "multipla":
        risposta = st.multiselect(
            "Seleziona tutte le risposte corrette:",
            q["opzioni"],
            key=f"q_{q['id']}",
        )
        st.session_state.risposte_utente[q["id"]] = risposta

      st.markdown("---")

    # Pulsante per inviare le risposte
    submit_button = st.form_submit_button(
        "🚀 Invia risposte e vedi il punteggio"
    )

    if submit_button:
      st.session_state.inviato = True

  # Se l'utente ha inviato il test, mostriamo i risultati e le spiegazioni
  if st.session_state.inviato:
    punteggio_totale = 0
    st.header("📊 Risultati della Simulazione")

    for i, q in enumerate(st.session_state.domande_selezionate):
      risposta_utente = st.session_state.risposte_utente.get(q["id"])
      corretta = q["risposta_corretta"]

      # Valutazione della risposta in base al tipo
      if q["tipo"] == "vero_falso":
        is_correct = (
            risposta_utente is not None
            and risposta_utente.strip().lower() == corretta.strip().lower()
        )
      elif q["tipo"] == "aperta":
        is_correct = (
            risposta_utente is not None
            and risposta_utente.strip().lower() == str(corretta).strip().lower()
        )
      elif q["tipo"] == "multipla":
        # Confronta i set per ignorare l'ordine di selezione
        is_correct = set(risposta_utente or []) == set(corretta)

      # Output visivo per ogni domanda
      st.markdown(f"**Domanda {i + 1}:** {q['domanda']}")

      if q["tipo"] == "multipla":
        st.write(
            f"Tua risposta: `{', '.join(risposta_utente) if risposta_utente else 'Nessuna risposta'}`"
        )
        st.write(f"Risposta corretta: `{', '.join(corretta)}`")
      else:
        st.write(
            f"Tua risposta: `{risposta_utente if risposta_utente and risposta_utente != '-- Seleziona --' else 'Nessuna risposta'}`"
        )
        st.write(f"Risposta corretta: `{corretta}`")

      if is_correct:
        punteggio_totale += 1
        st.success("✅ Corretto!")
      else:
        st.error("❌ Sbagliato.")

      if "spiegazione" in q and q["spiegazione"]:
        st.info(f"💡 **Spiegazione:** {q['spiegazione']}")

      st.markdown("---")

    # Punteggio finale
    st.subheader(
        f"🎯 Punteggio finale: {punteggio_totale} / {totale} ({"{:.1f}".format((punteggio_totale / totale) * 100)}%)"
    )
    if punteggio_totale == totale:
      st.balloons()