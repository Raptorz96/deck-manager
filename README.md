# 🃏 Magic: The Gathering Commander Synergy Analyzer

Un'applicazione web avanzata per analizzare la tua collezione di carte Magic: The Gathering e ricevere raccomandazioni personalizzate basate sui mazzi precon Commander.

## ✨ Funzionalità Principali

### 📚 Gestione Collezione
- **Importa** la tua lista di carte da file .deck o .txt
- **Aggiungi** carte manualmente con quantità
- **Gestisci** la tua collezione in modo intuitivo
- **Visualizza** statistiche in tempo reale

### 🎯 Analisi Sinergie
- Analizza automaticamente la compatibilità delle tue carte con **10+ mazzi precon Commander** recenti
- Sistema di **scoring intelligente** (0-100) basato su:
  - Identità di colore
  - Temi condivisi (artifacts, tokens, graveyard, etc.)
  - Meccaniche compatibili
  - Archetipi del mazzo

### 💎 Raccomandazioni Intelligenti
- Ricevi suggerimenti di carte da aggiungere alla tua collezione
- Priorità automatica: **Alta** 🔴, **Media** 🟡, **Bassa** 🟢
- Visualizza **carte chiave** dei mazzi precon
- Immagini delle carte e link a Scryfall

### 📊 Analisi Dettagliata
- Identifica **lacune** nella tua collezione per precon specifici
- Visualizza **copertura tematiche** con progress bar
- Statistiche complete su compatibilità e sinergie

## 🚀 Installazione

### Prerequisiti
- Python 3.12 o superiore
- pip (gestore pacchetti Python)

### Setup

1. **Clona il repository**
```bash
git clone <repository-url>
cd deck-manager
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

3. **Avvia l'applicazione**
```bash
streamlit run app.py
```

4. **Apri il browser**
L'applicazione si aprirà automaticamente su `http://localhost:8501`

## 📖 Come Usare

### 1. Importa la tua collezione

Puoi importare la tua collezione in due modi:

**Metodo A: File .deck/.txt**
1. Vai nella sidebar → "📥 Importa Collezione"
2. Carica un file nel formato:
```
4 Sol Ring
1 Command Tower
1 Arcane Signet
2 Lightning Greaves
```

**Metodo B: Aggiunta Manuale**
1. Vai nella sidebar → "➕ Aggiungi Carta"
2. Inserisci nome e quantità
3. Clicca "Aggiungi"

### 2. Esplora i Precon Raccomandati

1. Vai al tab **"🎯 Precon Raccomandati"**
2. L'app analizzerà automaticamente la tua collezione
3. Vedrai i top 5 mazzi precon più compatibili con le tue carte
4. Espandi ciascun precon per vedere:
   - Commander e colori
   - Archetipo e temi
   - Le tue migliori carte per quel mazzo
   - Statistiche di compatibilità

### 3. Ricevi Raccomandazioni

1. Vai al tab **"💎 Raccomandazioni Carte"**
2. Vedrai carte suggerite da aggiungere, organizzate per precon
3. Ogni raccomandazione include:
   - Priorità (Alta/Media/Bassa)
   - Score di sinergia (0-100)
   - Motivi dettagliati
   - Immagine della carta
   - Link a Scryfall per maggiori informazioni

### 4. Analizza in Dettaglio

1. Vai al tab **"📊 Analisi Dettagliata"**
2. Seleziona un precon specifico da analizzare
3. Clicca "🔍 Analizza Lacune"
4. Vedrai:
   - Carte chiave mancanti del precon
   - Copertura percentuale per ogni tema
   - Top raccomandazioni prioritarie

## 🎮 Mazzi Precon Supportati

L'applicazione include database di mazzi precon da:
- **The Brothers' War Commander** (2024)
- **Commander Legends: Battle for Baldur's Gate** (2024)
- **Fallout Commander** (2024)
- **Murders at Karlov Manor** (2024)
- **Commander Masters** (2024)
- E altri...

Archetipi supportati:
- Artifact Tokens
- Dragon Tribal
- Token +1/+1 Counters
- Graveyard Recursion
- Group Hug
- Eldrazi Ramp
- E molti altri...

## 🔧 Tecnologie Utilizzate

### Backend
- **Python 3.12** - Linguaggio di programmazione
- **Streamlit** - Framework web per l'interfaccia utente
- **Pandas** - Analisi e manipolazione dati

### API & Data
- **Scryfall API** - Database completo di carte Magic
- **JSON** - Storage locale collezione e database precon

### Features
- **Sistema di Caching** - Per performance ottimali
- **Rate Limiting** - Rispetto delle policy API Scryfall
- **Type Hints** - Codice sicuro e documentato
- **Logging** - Debugging e monitoraggio

## 📁 Struttura del Progetto

```
deck-manager/
├── app.py                      # Applicazione principale Streamlit
├── scryfall_api.py            # Client API Scryfall
├── commander_precons.py       # Database mazzi precon
├── synergy_analyzer.py        # Sistema analisi sinergie
├── recommendation_engine.py   # Motore raccomandazioni
├── requirements.txt           # Dipendenze Python
├── data/
│   ├── collection.json        # Tua collezione (auto-generato)
│   └── commander_precons.json # Database precon (auto-generato)
├── templates/                 # Template HTML (legacy)
└── static/                    # File statici (legacy)
```

## 🎯 Sistema di Scoring

Il sistema di scoring (0-100) valuta la sinergia tra carte e precon basandosi su:

### Identità di Colore (30 punti)
- ✅ Carta compatibile con i colori del precon
- ❌ Carta incompatibile = 0 punti totali

### Temi Condivisi (40 punti max)
- +15 punti per ogni tema condiviso
- Temi: artifacts, tokens, graveyard, tribal, counters, etc.

### Meccaniche Rilevanti (20 punti max)
- +5 punti per ogni meccanica rilevante
- Meccaniche: draw, sacrifice, flash, etc.

### Bonus Archetipo (10 punti max)
- Bonus speciale se la carta supporta l'archetipo specifico del mazzo

## 🔮 Esempio di Utilizzo

### Scenario: Giocatore con collezione artifacts

1. **Importa collezione** con carte come:
   - Sol Ring
   - Arcane Signet
   - Sai, Master Thopterist
   - Thopter Spy Network

2. **L'app raccomanda**:
   - "Urza's Iron Alliance" (97/100 compatibility)
   - "Mishra's Burnished Banner" (89/100 compatibility)

3. **Ricevi suggerimenti**:
   - 🔴 HIGH: "Cranial Plating" (95/100) - Carta chiave precon
   - 🟡 MEDIUM: "Steel Overseer" (75/100) - Supporta tokens artifacts
   - 🟢 LOW: "Thopter Foundry" (65/100) - Genera token thopter

## 🆕 Prossime Funzionalità

- [ ] Export collezione e raccomandazioni in PDF
- [ ] Filtraggio per budget (carte economiche vs costose)
- [ ] Integrazione con prezzi carte (TCGPlayer/Cardmarket)
- [ ] Database mazzi precon aggiornato automaticamente
- [ ] Sistema di wishlist
- [ ] Confronto tra collezioni
- [ ] Supporto per altri formati (Modern, Pioneer, etc.)

## 🐛 Troubleshooting

### L'app non si avvia
```bash
# Verifica versione Python
python --version  # Deve essere 3.12+

# Reinstalla dipendenze
pip install -r requirements.txt --force-reinstall
```

### Errori API Scryfall
- L'API Scryfall ha rate limiting (100ms tra richieste)
- L'app gestisce automaticamente il rate limiting
- In caso di errori, riprova dopo qualche secondo

### Database precon non trovato
- Il database viene creato automaticamente al primo avvio
- Verifica che la cartella `data/` sia scrivibile

## 📝 Formato File .deck

Il formato supportato è semplice testo:

```
# Commento (righe che iniziano con # sono ignorate)
4 Sol Ring
1 Command Tower
2 Arcane Signet (CMR)
3 Lightning Greaves

# Puoi includere il set tra parentesi, verrà ignorato
1 Skullclamp (C21)
```

## 🤝 Contribuire

Contributi sono benvenuti! Per aggiungere nuovi mazzi precon:

1. Modifica `commander_precons.py`
2. Aggiungi un nuovo dizionario nel formato:
```python
{
    "name": "Nome Mazzo",
    "year": 2024,
    "set_code": "XYZ",
    "commanders": ["Commander Name"],
    "color_identity": ["W", "U", "B"],
    "themes": ["theme1", "theme2"],
    "archetype": "archetype description",
    "key_cards": ["Card 1", "Card 2"],
    "description": "Descrizione mazzo"
}
```

## 📜 Licenza

Questo progetto è fornito "as-is" per uso personale ed educativo.

Magic: The Gathering è un marchio registrato di Wizards of the Coast.
Questo progetto non è affiliato con Wizards of the Coast.

I dati delle carte sono forniti da [Scryfall](https://scryfall.com/).

## 🙏 Crediti

- **Scryfall** - Per l'eccellente API gratuita
- **Streamlit** - Per il fantastico framework web
- **Wizards of the Coast** - Per Magic: The Gathering

---

Realizzato con ❤️ per la community di Magic: The Gathering Commander
