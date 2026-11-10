import json
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Simulatore Esame - Analisi Avanzata",
    page_icon="📚",
    layout="centered",
)


# Funzione per caricare il file JSON delle domande
def carica_domande():
  try:
    with open("domande.json", "r", encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    # Se il file non è nella stessa cartella, restituisce una lista vuota o gestisce l'errore
    return []


# Funzione per ripulire le stringhe LaTeX nel confronto (elimina spazi superflui)
def pulisci_stringa(s):
  if isinstance(s, str):
    return s.replace(" ", "").strip()
  return s


def verifica_risposta(user_ans, correct_ans):
  if isinstance(correct_ans, list):
    user_set = {pulisci_stringa(x) for x in user_ans}
    correct_set = {pulisci_stringa(x) for x in correct_ans}
    return user_set == correct_set
  else:
    return pulisci_stringa(user_ans) == pulisci_stringa(correct_ans)


def main():
  st.title("🎓 Simulatore d'Esame - Analisi Avanzata")
  st.write(
      "Mettiti alla prova con i quesiti del test. Riceverai il riscontro e le"
      " spiegazioni dettagliate."
  )

  tutte_le_domande = carica_domande()

  if not tutte_le_domande:
    st.error(
        "⚠️ Non è stato possibile caricare il file delle domande o il file"
        " `domande.json` è vuoto/assente."
    )
    return

  # Inizializzazione dello stato della sessione
  if "indice_corrente" not in st.session_state:
    st.session_state.indice_corrente = 0
  if "risposte_utente" not in st.session_state:
    st.session_state.risposte_utente = {}
  if "mostra_risultato" not in st.session_state:
    st.session_state.mostra_risultato = False

  idx = st.session_state.indice_corrente
  domanda_corrente = tutte_le_domande[idx]

  # Barra di progresso
  st.progress((idx + 1) / len(tutte_le_domande))
  st.caption(
      f"Domanda {idx + 1} di {len(tutte_le_domande)} — Nota:"
      f" {domanda_corrente.get('nota', 'N/D')}"
  )

  st.markdown("---")

  # Visualizzazione della domanda (supporta nativamente il LaTeX)
  st.markdown(f"### {domanda_corrente['domanda']}")

  tipo = domanda_corrente["tipo"]
  opzioni = domanda_corrente.get("opzioni", [])
  chiave_risposta = f"domanda_{idx}"

  # Gestione delle risposte in base al tipo di quesito
  risposta_utente = None

  if tipo in ["vero_falso", "multipla_singola"]:
    # Per Vero/Falso o Scelta Singola
    risposta_utente = st.radio(
        "Seleziona un'opzione:",
        options=opzioni,
        key=chiave_risposta,
        format_func=lambda x: f"{x}",
    )

  elif tipo == "multipla":
    # Per Risposta Multipla (più opzioni corrette) - risolve il problema del rendering LaTeX nelle checkbox
    st.write(
        "*Quesito a risposta multipla (seleziona tutte le opzioni corrette):*"
    )
    risposta_utente = []
    for i, opzione in enumerate(opzioni):
      # Usiamo st.checkbox con etichetta pulita e supporto markdown implicito
      if st.checkbox(opzione, key=f"{chiave_risposta}_opt_{i}"):
        risposta_utente.append(opzione)

  elif tipo == "aperta":
    # Per domande a risposta numerica o aperta breve
    risposta_utente = st.text_input(
        "Inserisci la tua risposta:", key=chiave_risposta
    )

  st.markdown("---")

  # Pulsanti di navigazione e verifica
  col1, col2, col3 = st.columns([1, 1, 1])

  with col1:
    if idx > 0:
      if st.button("⬅️ Precedente"):
        st.session_state.indice_corrente -= 1
        st.rerun()

  with col2:
    if not st.session_state.mostra_risultato:
      if st.button("✅ Verifica Risposta", type="primary"):
        st.session_state.risposte_utente[idx] = risposta_utente
        st.session_state.mostra_risultato = True
        st.rerun()

  with col3:
    if idx < len(tutte_le_domande) - 1:
      if st.button("Successiva ➡️"):
        st.session_state.mostra_risultato = False
        st.session_state.indice_corrente += 1
        st.rerun()

  # Se l'utente ha cliccato su verifica, mostra l'esito e la spiegazione
  if st.session_state.mostra_risultato:
    risposta_data = st.session_state.risposte_utente.get(idx)
    risposta_corretta = domanda_corrente["risposta_corretta"]

    corretto = verifica_risposta(risposta_data, risposta_corretta)

    if corretto:
      st.success("🎉 **Risposta Corretta!**")
    else:
      st.error("❌ **Risposta Errata.**")
      if isinstance(risposta_corretta, list):
        st.info(
            "Le risposte corrette erano: "
            + ", ".join([f"`{r}`" for r in risposta_corretta])
        )
      else:
        st.info(f"La risposta corretta era: `{risposta_corretta}`")

    spiegazione = domanda_corrente.get("spiegazione", "")
    if spiegazione:
      st.markdown(f"> **Spiegazione:** {spiegazione}")


if __name__ == "__main__":
  main()
