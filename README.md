# House Hunter Agent

Agente immobiliare personale per monitorare alert Gmail di Immobiliare.it e Casa.it, salvare annunci in SQLite, rilevare nuovi immobili e ribassi, calcolare uno score e preparare un digest WhatsApp.

## Stato attuale

Il progetto è pronto per integrazioni reali future:

- Gmail API per leggere le label `house-hunter-immobiliare.it` e `house-hunter-casa.it`.
- SQLite locale in `data/house_hunter.db`.
- Scoring trasparente per acquisto in Roma Prati.
- Digest WhatsApp costruito automaticamente.
- Invio WhatsApp predisposto tramite Meta WhatsApp Cloud API, disattivato di default.

## Prova senza credenziali

```bash
python3 main.py --sample
```

Questa modalità usa due email di esempio e verifica tutto il flusso senza accedere a Gmail o WhatsApp.

## Esecuzione reale Gmail

1. Installa le dipendenze:

```bash
python3 -m pip install -r requirements.txt
```

2. Scarica dal Google Cloud Console le credenziali OAuth di tipo "Desktop app".
3. Salva il file scaricato come:

```text
credentials/client_secret.json
```

4. Crea il token Gmail read-only:

```bash
python3 setup_gmail.py
```

Lo script apre il browser, chiede accesso Gmail in sola lettura e salva:

```text
credentials/token.json
```

5. Esegui l'import reale:

```bash
python3 main.py
```

## WhatsApp con Meta Cloud API

L'invio reale è disattivato di default. Copia il file di esempio:

```bash
cp .env.example .env
```

Poi modifica `.env` con i valori Meta:

```text
HOUSE_HUNTER_WHATSAPP_ENABLED=true
HOUSE_HUNTER_WHATSAPP_TO=39...
META_WHATSAPP_PHONE_NUMBER_ID=...
META_WHATSAPP_ACCESS_TOKEN=...
META_WHATSAPP_API_VERSION=v23.0
```

`HOUSE_HUNTER_WHATSAPP_TO` deve essere il tuo numero in formato internazionale senza `+`, per esempio `393331234567`.

## Flusso

1. Gmail legge gli alert etichettati.
2. Il parser normalizza ogni email in un annuncio.
3. Il database conserva annunci e storico prezzi.
4. Il change detector rileva nuovi annunci e ribassi.
5. Lo scorer assegna priorità.
6. WhatsApp prepara il digest giornaliero.

## Automazione giornaliera su macOS

Il file `scripts/run_daily.sh` esegue l'agente e carica le variabili da `.env`.

Il template `launchd/com.crago.house-hunter-agent.plist.template` può essere copiato in:

```text
~/Library/LaunchAgents/com.crago.house-hunter-agent.plist
```

Poi si abilita con:

```bash
launchctl load ~/Library/LaunchAgents/com.crago.house-hunter-agent.plist
```

Di default l'agente parte ogni giorno alle 09:00.

## Deploy online su Render

La versione web espone questi endpoint:

```text
GET  /health
GET  /webhook
POST /webhook
POST /daily-run
```

- `/health` serve a Render per verificare che l'app sia viva.
- `/webhook` riceve le risposte WhatsApp da Meta.
- `/daily-run` esegue il controllo annunci e invia il messaggio giornaliero.

### Variabili ambiente Render

Imposta queste variabili in Render, nella sezione Environment:

```text
HOUSE_HUNTER_WHATSAPP_ENABLED=true
HOUSE_HUNTER_WHATSAPP_TO=39...
META_WHATSAPP_PHONE_NUMBER_ID=...
META_WHATSAPP_ACCESS_TOKEN=...
META_WHATSAPP_API_VERSION=v23.0
META_WHATSAPP_DAILY_TEMPLATE_NAME=daily_house_hunter_update
META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE=it
META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT=1
WEBHOOK_VERIFY_TOKEN=scegli-una-frase-segreta
DAILY_RUN_SECRET=scegli-una-seconda-frase-segreta
GMAIL_TOKEN_JSON={...contenuto di credentials/token.json...}
DATABASE_PATH=/var/data/house_hunter.db
```

Per non perdere preferiti, feedback e storico annunci, su Render deve esistere anche un disco persistente:

```text
Name: house-hunter-data
Mount path: /var/data
Size: 1 GB
```

Senza disco persistente, Render puo svuotare il database a ogni deploy o riavvio.

Se il template approvato non ha variabili, imposta:

```text
META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT=0
```

In quel caso l'app invia il template fisso. Per il riepilogo dinamico dettagliato usa `META_WHATSAPP_DAILY_USE_TEMPLATE=false`.

Su Render usa:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Health Check Path: /health
```

### Webhook Meta

Quando Render ti dà un URL tipo:

```text
https://house-hunter-agent.onrender.com
```

su Meta configura il webhook così:

```text
Callback URL: https://house-hunter-agent.onrender.com/webhook
Verify token: lo stesso valore di WEBHOOK_VERIFY_TOKEN
```

Poi sottoscrivi gli eventi WhatsApp messages.

### Daily run

Per eseguire il controllo manualmente:

```bash
curl -X POST "https://house-hunter-agent.onrender.com/daily-run" \
  -H "Authorization: Bearer DAILY_RUN_SECRET"
```

Per automatizzarlo ogni giorno puoi usare un Render Cron Job o un servizio esterno che chiama `/daily-run` una volta al giorno.

## Sicurezza operativa

L'agente non contatta agenzie e non fissa visite in autonomia.

L'agente capisce risposte naturali come:

```text
salva il primo
scarta il secondo
mandami il terzo
fammi vedere il primo
contatta il primo
```

Se nel riepilogo c'e un solo annuncio, puoi scrivere anche solo `contatta`. Se ci sono piu annunci, l'agente ti chiede quale intendi.

Quando chiedi di contattare un annuncio, prepara una bozza messaggio per l'agenzia e te la rimanda in WhatsApp. L'invio reale resta una tua decisione.
