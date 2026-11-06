import json
import random
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Simulazione Esonero Analisi Superiore", page_icon="📐", layout="centered"
)


# Funzione per caricare le domande dal file JSON
def carica_domande():
  try:
    with open("domande.json", "r", encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    st.error(
        "File 'domande.json' non trovato nella cartella. Assicurati che si"
        " trovi nello stesso percorso di app.py!"
    )
    return []


def main():
  st.title("Simulazione Primo Esonero")    

  tutte_le_domande = carica_domande()
  if not tutte_le_domande:
    return

  # Inizializzazione della sessione e sorteggio di 10 domande casuali
  if "domande_test" not in st.session_state:
    num_pesca = min(10, len(tutte_le_domande))
    st.session_state.domande_test = random.sample(tutte_le_domande, num_pesca)
    st.session_state.risposte_inviate = False

  domande = st.session_state.domande_test

  # Se l'utente ha inviato il modulo, mostriamo i risultati e le spiegazioni
  if st.session_state.get("risposte_inviate", False):
    st.header("📊 Risultati e Spiegazioni")
    punteggio = 0
    totale = len(domande)

    for i, q in enumerate(domande):
      risposta_data = st.session_state.get(f"q_{i}")
      risposta_corretta = q["risposta_corretta"]

      st.markdown(f"**Domanda {i + 1}:** {q['domanda']}")

      # Controllo correttezza
      user_ans_str = str(risposta_data).strip() if risposta_data else ""
      corr_ans_str = str(risposta_corretta).strip()

      if user_ans_str.lower() == corr_ans_str.lower():
        st.success(f"La tua risposta: **{risposta_data}** — **Corretta!** ✅")
        punteggio += 1
      else:
        st.error(
            f"La tua risposta: **{risposta_data if risposta_data else 'Nessuna risposta'}** — "
            f"La risposta corretta era: **{risposta_corretta}** ❌"
        )

      # Mostra la spiegazione con supporto LaTeX
      with st.expander("🔍 Mostra spiegazione dettagliata"):
        st.markdown(q["spiegazione"])

      st.divider()

    st.subheader(
        f"Punteggio finale: {punteggio} su {totale} ("
        f"{round((punteggio/totale)*100, 1)}%)"
    )

    if st.button("Ricomincia il test"):
      # Pulisce tutta la memoria di sessione per pescare nuove domande al prossimo giro
      for k in list(st.session_state.keys()):
        del st.session_state[k]
      st.rerun()

  else:
    with st.form("form_quiz"):
      for i, q in enumerate(domande):
        st.markdown(f"### Domanda {i + 1}")
        if "nota" in q:
          st.caption(f"*{q['nota']}*")

        st.markdown(q["domanda"])

        # Gestione dinamica in base al tipo di domanda
        if q["tipo"] in ["multipla", "vero_falso"]:
          st.radio(
              "Seleziona un'opzione:",
              q["opzioni"],
              key=f"q_{i}",
              index=None,
          )
        elif q["tipo"] == "aperta":
          st.text_input("Inserisci la tua risposta:", key=f"q_{i}")

        st.divider()

      submit_button = st.form_submit_button("Invia risposte e vedi risultati")

      if submit_button:
        st.session_state.risposte_inviate = True
        st.rerun()


if __name__ == "__main__":
  main()