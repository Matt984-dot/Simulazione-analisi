import json
import random
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Simulazione Esonero Analisi Superiore",
    page_icon="📐",
    layout="centered",
)

FILE_ESONERI = {
    "1° Esonero": "domande.json",
    "2° Esonero": "domande2.json",
}


def carica_domande(percorso_file):
  try:
    with open(percorso_file, "r", encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    st.error(f"File '{percorso_file}' non trovato nella cartella!")
    return []


def estrai_capitolo_da_nota(nota):
  if not nota:
    return "Non specificato"
  if "," in nota:
    return nota.split(",", 1)[0].strip()
  return nota.strip()


def pulisci_stringa(s):
  if isinstance(s, str):
    return s.replace(" ", "").strip()
  return s


def verifica_risposta_singola(risposta_data, risposta_corretta, tipo):
  """Funzione di supporto per verificare una singola risposta."""
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


def main():
  st.title("Simulazione Esonero Analisi Superiore")

  # --- SIDEBAR PER IMPOSTAZIONI E MODALITÀ ---
  st.sidebar.header("⚙️ Impostazioni Test")

  esonero_scelto = st.sidebar.selectbox(
      "Seleziona il test:",
      list(FILE_ESONERI.keys()),
      index=1,  # Default sul 2° Esonero; metti 0 per partire dal 1°
  )
  file_domande_scelto = FILE_ESONERI[esonero_scelto]

  tutte_le_domande = carica_domande(file_domande_scelto)
  if not tutte_le_domande:
    return

  capitolo_scelto = "Tutte le schede"
  domande_filtrate = tutte_le_domande

  if esonero_scelto == "2° Esonero":
    st.sidebar.divider()
    st.sidebar.subheader("📖 Filtro Scheda / Capitolo")
    capitoli_disponibili = sorted(
        list(
            set(
                estrai_capitolo_da_nota(q.get("nota"))
                for q in tutte_le_domande
            )
        )
    )
    opzioni_capitolo = ["Tutte le schede"] + capitoli_disponibili
    capitolo_scelto = st.sidebar.selectbox(
        "Seleziona la scheda:", opzioni_capitolo
    )

    if capitolo_scelto != "Tutte le schede":
      domande_filtrate = [
          q
          for q in tutte_le_domande
          if estrai_capitolo_da_nota(q.get("nota")) == capitolo_scelto
      ]

  if not domande_filtrate:
    st.warning("Nessuna domanda trovata per la selezione corrente.")
    return

  modalita = st.sidebar.radio(
      "Scegli la modalità:",
      (
          "Modalità Esame (Tutte insieme)",
          "Modalità Allenamento (Casuali, una per volta)",
      ),
  )

  max_q = len(domande_filtrate)
  min_q = min(1, max_q)
  num_pesca = st.sidebar.slider(
      "Numero di domande da estrarre:",
      min_value=min_q,
      max_value=min(50, max_q),
      value=min(20, max_q),
  )

  # Reset dello stato quando cambia test, scheda, modalità o numero di domande
  stato_corrente = (
      file_domande_scelto,
      capitolo_scelto,
      modalita,
      num_pesca,
  )
  if (
      "stato_prec" not in st.session_state
      or st.session_state.stato_prec != stato_corrente
  ):
    st.session_state.stato_prec = stato_corrente
    for k in list(st.session_state.keys()):
      if k != "stato_prec":
        del st.session_state[k]
    st.rerun()

  if "domande_test" not in st.session_state:
    st.session_state.domande_test = random.sample(domande_filtrate, num_pesca)

  domande = st.session_state.domande_test

  # ==========================================
  # MODALITÀ 1: ESAME (Tutte le domande in un form)
  # ==========================================
  if "Modalità Esame" in modalita:
    if not st.session_state.get("risposte_inviate", False):
      with st.form("form_quiz"):
        st.info(
            f"📝 **{esonero_scelto} ({capitolo_scelto}) — Modalità Esame"
            f" attiva**: Stai affrontando un set di {len(domande)} domande."
            " Rispondi a tutto e invia."
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
          st.rerun()

    else:
      st.header(f"Risultati e Spiegazioni — {esonero_scelto}")
      punteggio = 0
      totale = len(domande)

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
          st.error(
              f"La tua risposta: **{user_str}** — La risposta corretta era:"
              f" **{corr_str}** ❌"
          )

        with st.expander("🔍 Mostra spiegazione dettagliata"):
          st.markdown(q["spiegazione"])
        st.divider()

      percentuale = round((punteggio / totale) * 100, 1) if totale > 0 else 0
      st.subheader(f"Punteggio finale: {punteggio} su {totale} ({percentuale}%)")

      if st.button("Ricomincia il test"):
        for k in list(st.session_state.keys()):
          if k != "stato_prec":
            del st.session_state[k]
        st.rerun()

  # ==========================================
  # MODALITÀ 2: ALLENAMENTO (Casuale, una alla volta con feedback)
  # ==========================================
  else:
    if "indice_allenamento" not in st.session_state:
      st.session_state.indice_allenamento = 0
      st.session_state.punteggio_allenamento = 0
      st.session_state.verificato_corrente = False

    idx = st.session_state.indice_allenamento
    totale = len(domande)

    if idx < totale:
      q = domande[idx]
      st.progress((idx + 1) / totale)

      nota_testo = f" — *{q['nota']}*" if "nota" in q else ""
      st.caption(
          f"{esonero_scelto} · Allenamento (Casuale) - Domanda {idx + 1} di"
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
          if f"punteggiato_{idx}" not in st.session_state:
            st.session_state.punteggio_allenamento += 1
            st.session_state[f"punteggiato_{idx}"] = True
        else:
          st.error("❌ **Risposta Errata.**")
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
      st.header("Sessione di allenamento completata! 🎉")
      punteggio = st.session_state.punteggio_allenamento
      percentuale = round((punteggio / totale) * 100, 1) if totale > 0 else 0
      st.subheader(
          f"Hai totalizzato {punteggio} su {totale} ({percentuale}%)"
      )

      if st.button("Nuova sessione di allenamento casuale"):
        for k in list(st.session_state.keys()):
          if k != "stato_prec":
            del st.session_state[k]
        st.rerun()


if __name__ == "__main__":
  main()