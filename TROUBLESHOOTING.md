# Errori da non ripetere

Questo file serve come memoria pratica del progetto House Hunter Agent.

## Non caricare segreti su GitHub

Non caricare mai:

- `.env`
- `credentials/`
- `credentials/client_secret.json`
- `credentials/token.json`
- `data/house_hunter.db`

Questi file contengono token, credenziali o dati locali. Sono esclusi da `.gitignore`, ma prima di fare push va comunque controllato.

## WhatsApp Meta: messaggi liberi vs template

Il messaggio `hello_world` arriva perche e un template ufficiale Meta.

I messaggi personalizzati dell'agente non sempre arrivano se sono testo libero. Per inviare aggiornamenti giornalieri automatici serve un template approvato, per esempio:

```text
daily_house_hunter_update
```

Quindi il daily-run su Render deve usare il template approvato, non un messaggio libero.

## Token Meta

Se Meta risponde:

```text
Malformed access token
```

quasi sempre nel file `.env` e rimasto il token finto:

```text
EAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Il token reale e molto piu lungo e non contiene `xxxx`.

## Numero WhatsApp destinatario

Nel file `.env`, il numero destinatario deve essere senza `+`.

Esempio corretto:

```text
HOUSE_HUNTER_WHATSAPP_TO=393331234567
```

Esempio sbagliato:

```text
HOUSE_HUNTER_WHATSAPP_TO=+393331234567
```

## Render e database SQLite

Su Render, se si usa il piano gratuito senza disco persistente, il database SQLite locale puo sparire ai riavvii.

Sintomo tipico:

- WhatsApp risponde `Non hai ancora annunci salvati nei preferiti dell'agente.`
- la pagina `/favorites` torna vuota dopo deploy, riavvio o sleep del servizio.

Soluzione consigliata per questo MVP:

```text
DATABASE_PATH=/var/data/house_hunter.db
Render persistent disk:
- name: house-hunter-data
- mount path: /var/data
- size: 1 GB
```

Per produzione stabile serve uno di questi:

- disco persistente Render;
- database esterno;
- altra soluzione di storage stabile.

## Gmail su Render

Render non puo leggere i file locali `credentials/token.json` dal Mac.

Per usare Gmail online serve copiare il contenuto JSON del token nella variabile ambiente:

```text
GMAIL_TOKEN_JSON
```

Il comando locale per ottenere il valore e:

```bash
python3 -c "import json; print(json.dumps(json.load(open('credentials/token.json'))))"
```

## Terminale

Attenzione ai comandi digitati male. Per esempio:

```bash
cpython3 main.py --sample --reset-db
```

e sbagliato.

Il comando corretto e:

```bash
python3 main.py --sample --reset-db
```
