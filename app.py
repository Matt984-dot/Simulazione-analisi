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


# Funzione per ripulire le stringhe nel confronto (elimina spazi LaTeX superflui)
def pulisci_stringa(s):
  if isinstance(s, str):
    return s.replace(" ", "").strip()
  return s


def main():
  st.title("Simulazione Primo Esonero") 

  tutte_le_domande = carica_domande()
  if not tutte_le_domande:
    return

  # Inizializzazione della sessione e sorteggio di 15 domande casuali
  if "domande_test" not in st.session_state:
    num_pesca = min(15, len(tutte_le_domande))
    st.session_state.domande_test = random.sample(tutte_le_domande, num_pesca)
    st.session_state.risposte_inviate = False

  domande = st.session_state.domande_test

  # Se l'utente ha inviato il modulo, mostriamo i risultati e le spiegazioni
  if st.session_state.get("risposte_inviate", False):
    st.header("Risultati e Spiegazioni")
    punteggio = 0
    totale = len(domande)

    for i, q in enumerate(domande):
      risposta_data = st.session_state.get(f"q_{i}")
      risposta_corretta = q["risposta_corretta"]

      st.markdown(f"**Domanda {i + 1}:** {q['domanda']}")

      # Controllo correttezza in base al tipo di domanda
      tipo = q.get("tipo", "vero_falso")

      if tipo == "multipla":
        # Gestione multipla: confronta gli insiemi ripuliti dagli spazi LaTeX
        user_set = {pulisci_stringa(x) for x in risposta_data} if risposta_data else set()
        if isinstance(risposta_corretta, list):
          corr_set = {pulisci_stringa(x) for x in risposta_corretta}
        else:
          corr_set = {pulisci_stringa(risposta_corretta)}
        
        is_correct = (user_set == corr_set)
        
        user_str = ", ".join(risposta_data) if risposta_data else "Nessuna risposta"
        corr_str = ", ".join(risposta_corretta) if isinstance(risposta_corretta, list) else str(risposta_corretta)

        if is_correct:
          st.success(f"La tua risposta: **{user_str}** — **Corretta!** ✅")
          punteggio += 1
        else:
          st.error(
              f"La tua risposta: **{user_str}** — "
              f"La risposta corretta era: **{corr_str}** ❌"
          )
      else:
        # Gestione standard per vero_falso e aperta con confronto flessibile
        user_ans_str = pulisci_stringa(str(risposta_data)) if risposta_data else ""
        corr_ans_str = pulisci_stringa(str(risposta_corretta))

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

      submit_button = st.form_submit_button("Invia risposte e vedi risultati")

      if submit_button:
        # Raccoglie le opzioni selezionate per le domande a risposta multipla
        for i, q in enumerate(domande):
          if q.get("tipo", "vero_falso") == "multipla":
            selected = []
            for opt_idx, opzione in enumerate(q["opzioni"]):
              if st.session_state.get(f"q_{i}_opt_{opt_idx}", False):
                selected.append(opzione)
            st.session_state[f"q_{i}"] = selected

        st.session_state.risposte_inviate = True
        st.rerun()


if __name__ == "__main__":
  main()
