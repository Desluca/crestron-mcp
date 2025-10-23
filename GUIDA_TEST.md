# Guida Completa per Test del Crestron MCP Server

Questa guida ti mostrerà come testare completamente il server MCP Crestron usando un mock server e integrandolo con Claude Desktop.

## 📋 Sommario

1. [Setup Iniziale](#setup-iniziale)
2. [Avviare il Mock Server](#avviare-il-mock-server)
3. [Test Automatici](#test-automatici)
4. [Integrazione con Claude Desktop](#integrazione-con-claude-desktop)
5. [Test con Claude](#test-con-claude)
6. [Risoluzione Problemi](#risoluzione-problemi)

---

## Setup Iniziale

### 1. Verifica Dipendenze

```bash
# Installa le dipendenze (se non già fatto)
pip install -r requirements.txt

# Verifica che tutto sia installato
python -c "import mcp, httpx, pydantic; print('✅ Tutte le dipendenze installate')"
```

### 2. Struttura File

Assicurati di avere questi file nella stessa directory:

```
crestron-mcp/
├── crestron_mcp.py              # Server MCP principale
├── mock_crestron_server.py      # Mock del sistema Crestron
├── test_crestron_mcp.py         # Script di test automatici
├── requirements.txt
└── README.md
```

---

## Avviare il Mock Server

### 1. Avvio del Mock Server

Apri un **primo terminale** e avvia il mock server:

```bash
python mock_crestron_server.py
```

Dovresti vedere:

```
======================================================================
🏠 MOCK CRESTRON HOME SERVER
======================================================================

✅ Server running on http://localhost:8080
✅ API base URL: http://localhost:8080/cws/api

🔑 Auth Token: test-token-123

📊 Mock Data Loaded:
   - Stanze: 4
   - Dispositivi: 15
     • Luci: 8
     • Tapparelle: 3
     • Sensori: 3
     • Termostati: 1
   - Scene: 7

🏘️  Stanze:
   • Soggiorno (ID: 1) - 6 dispositivi
   • Camera da Letto (ID: 2) - 6 dispositivi
   • Cucina (ID: 3) - 4 dispositivi
```

**⚠️ IMPORTANTE**: Lascia questo terminale aperto! Il server deve rimanere in esecuzione.

### 2. Verifica Mock Server

Apri un **secondo terminale** e testa che il mock funzioni:

```bash
# Test semplice con curl
curl http://localhost:8080/cws/api/rooms
```

Dovresti ricevere un errore di autenticazione (normale - significa che funziona!).

---

## Test Automatici

### 1. Esegui i Test Automatici

Nel **secondo terminale**, esegui lo script di test:

```bash
python test_crestron_mcp.py
```

### 2. Output Atteso

Dovresti vedere qualcosa del genere:

```
ℹ️  Starting Crestron MCP test suite...
ℹ️  Target: http://localhost:8080
ℹ️  Auth Token: test-token-123

======================================================================
🧪 CRESTRON MCP TEST SUITE
======================================================================

🧪 Test 1: Authentication
✅ Authentication successful. Session key: session-1729619282-1...

🧪 Test 2: List Rooms
✅ Retrieved 4 rooms
   • Tutta la Casa (ID: 1001)
   • Soggiorno (ID: 1)
   • Camera da Letto (ID: 2)
   • Cucina (ID: 3)

🧪 Test 3: List Devices
✅ Retrieved 15 devices
   • light: 8 device(s)
     - Lampadario Soggiorno (ID: 10)
     - Applique Parete (ID: 11)
   • shade: 3 device(s)
     - Tapparella Grande (ID: 20)
     - Tapparella Finestra (ID: 21)
   ...

======================================================================
📊 TEST SUMMARY
======================================================================

✅ Passed: 10/10
❌ Failed: 0/10

Success Rate: 100.0%

🎉 All tests passed!
```

### 3. Cosa Testano gli Script

Lo script di test verifica:

1. ✅ **Autenticazione** - Login con token
2. ✅ **Lista Stanze** - Recupero di tutte le stanze
3. ✅ **Lista Dispositivi** - Scoperta dispositivi
4. ✅ **Stato Tapparelle** - Lettura posizione tapparelle
5. ✅ **Controllo Tapparelle** - Modifica posizione
6. ✅ **Lista Scene** - Recupero scene disponibili
7. ✅ **Attivazione Scene** - Esecuzione scena
8. ✅ **Stato Termostato** - Lettura temperatura
9. ✅ **Controllo Termostato** - Modifica setpoint
10. ✅ **Sensori** - Lettura sensori

---

## Integrazione con Claude Desktop

### 1. Trova il File di Configurazione

**macOS**: 
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows**:
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

### 2. Aggiungi la Configurazione MCP

Modifica il file JSON per includere il server Crestron:

```json
{
  "mcpServers": {
    "crestron": {
      "command": "python",
      "args": [
        "/percorso/assoluto/a/crestron_mcp.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**⚠️ IMPORTANTE**: Sostituisci `/percorso/assoluto/a/crestron_mcp.py` con il percorso reale del file!

Per trovare il percorso assoluto:

```bash
# Su macOS/Linux
cd /directory/dei/tuoi/file
pwd
# Output esempio: /Users/tuonome/crestron-mcp

# Il percorso completo sarà:
# /Users/tuonome/crestron-mcp/crestron_mcp.py
```

### 3. Riavvia Claude Desktop

Chiudi completamente Claude Desktop e riaprilo.

### 4. Verifica l'Integrazione

In Claude Desktop, dovresti vedere:
- Un'icona 🔌 nella barra inferiore
- Cliccandoci, dovresti vedere "crestron" nella lista dei server MCP

---

## Test con Claude

### 1. Prima Autenticazione

**Comando**:
```
Autenticati con il mio sistema Crestron. 
Host: localhost:8080
Token: test-token-123
```

**Risposta Attesa**:
Claude userà il tool `crestron_authenticate` e risponderà che l'autenticazione è avvenuta con successo.

### 2. Scoperta Casa

#### Test 2.1: Lista Stanze

**Comando**:
```
Mostrami tutte le stanze della casa
```

**Risposta Attesa**:
Claude userà `crestron_list_rooms` e mostrerà:
- Tutta la Casa
- Soggiorno
- Camera da Letto
- Cucina

#### Test 2.2: Dispositivi in una Stanza

**Comando**:
```
Quali dispositivi ci sono in soggiorno?
```

**Risposta Attesa**:
Claude userà `crestron_list_devices` con filtro per stanza e mostrerà:
- Lampadario Soggiorno
- Applique Parete
- Lampada Lettura
- Tapparella Grande
- Tapparella Finestra

### 3. Controllo Dispositivi

#### Test 3.1: Controllo Tapparelle

**Comando in Italiano**:
```
Chiudi la tapparella grande in soggiorno
```

**Cosa Succede**:
1. Claude usa `crestron_resolve_device` per trovare "Tapparella Grande"
2. Identifica il dispositivo con ID 20
3. Usa `crestron_set_shade_position` con posizione 0 (chiuso)
4. Conferma l'operazione

**Guarda il Mock Server**:
Nel terminale del mock server vedrai:
```
🎛️  [SHADES] Setting state for 1 shades
   ✅ Shade 20 (Tapparella Grande) → 0%
```

#### Test 3.2: Controllo Batch

**Comando**:
```
Chiudi tutte le tapparelle
```

**Cosa Succede**:
1. Claude scopre tutte le tapparelle con `crestron_list_devices`
2. Usa `crestron_set_shade_position` per tutte contemporaneamente
3. Mock server processa il batch

#### Test 3.3: Scene

**Comando**:
```
Attiva la scena Film
```

**Cosa Succede**:
1. Claude usa `crestron_list_scenes` per trovare la scena "Film"
2. Identifica scene ID 3
3. Usa `crestron_activate_scene` con ID 3
4. Mock server simula l'attivazione

**Mock Server Log**:
```
🎬 [SCENE] Activated scene 3 (Film)
   📺 Dimming living room lights to 10%...
```

### 4. Controllo Climatizzazione

#### Test 4.1: Informazioni Termostato

**Comando**:
```
Che temperatura c'è in casa?
```

**Risposta Attesa**:
Claude userà `crestron_get_thermostats` e mostrerà:
- Temperatura attuale: 23.5°C
- Setpoint: 22.0°C
- Modalità: Cool
- Fan: Auto

#### Test 4.2: Modifica Temperatura

**Comando**:
```
Imposta il termostato a 21 gradi
```

**Cosa Succede**:
1. Claude identifica il termostato
2. Usa `crestron_set_thermostat_setpoint` con 21°C
3. Mock server aggiorna il valore

**Mock Server Log**:
```
🌡️  [THERMOSTAT] Setting 1 setpoint(s) for 80
   ✅ Cool setpoint → 21.0°C
```

### 5. Sensori

**Comando**:
```
Mostrami i sensori in cucina
```

**Risposta Attesa**:
Claude userà `crestron_get_sensors` filtrato per la cucina e mostrerà:
- Sensore Luce Finestra (PhotoSensor): livello 450
- Sensore Porta (DoorSensor): Chiuso, batteria normale

### 6. Test di Risoluzione Naturale

#### Test 6.1: Comando Ambiguo

**Comando**:
```
Accendi la luce in camera
```

**Cosa Succede**:
1. Claude usa `crestron_resolve_device` con "luce camera"
2. Trova 3 match: Lampadario Camera, Abat-jour Sinistra, Abat-jour Destra
3. Chiede chiarimenti all'utente
4. L'utente specifica quale luce
5. Claude esegue il comando

#### Test 6.2: Comando Specifico

**Comando**:
```
Spegni il lampadario in camera da letto
```

**Cosa Succede**:
1. Claude usa `crestron_resolve_device`
2. Match univoco: Lampadario Camera (ID 30)
3. Confidence > 0.8
4. Esegue direttamente (nota: controllo luci non implementato nel mock, ma la risoluzione funziona)

---

## Esempi di Conversazioni Complete

### Esempio 1: Scenario Sera

**Tu**:
```
È sera, voglio rilassarmi. Prepara la casa per guardare un film.
```

**Claude**:
```
Perfetto! Per preparare la casa per vedere un film, farò:

1. Attivo la scena "Film" che regola l'illuminazione
2. Chiudo le tapparelle per oscurare l'ambiente
3. Abbasso leggermente il termostato per comfort

Procedo?
```

**Tu**:
```
Sì, vai
```

**Claude** (esegue):
1. `crestron_activate_scene` con ID 3 (Film)
2. `crestron_set_shade_position` per tutte le tapparelle a 0
3. `crestron_set_thermostat_setpoint` a 21°C

### Esempio 2: Scenario Mattina

**Tu**:
```
Buongiorno! Prepara la casa per la giornata
```

**Claude**:
```
Buongiorno! Preparo la casa:

1. Attivo la scena "Buongiorno" che apre le tapparelle
2. Accendo le luci in cucina
3. Verifico i sensori per vedere se c'è presenza

Iniziamo?
```

**Tu**:
```
Perfetto
```

**Claude** (esegue e riporta):
1. Scena attivata
2. Stato luci aggiornato
3. Sensori: presenza rilevata in camera, porta cucina chiusa

### Esempio 3: Controllo Dettagliato

**Tu**:
```
Analizza lo stato completo della casa
```

**Claude** (esegue più chiamate):
1. `crestron_list_rooms`
2. `crestron_list_devices`
3. `crestron_get_thermostats`
4. `crestron_get_sensors`
5. `crestron_list_scenes`

Poi fornisce un report completo con:
- Stanze e dispositivi per stanza
- Temperatura attuale
- Stato sensori
- Scene disponibili

---

## Risoluzione Problemi

### Problema 1: Mock Server Non Si Avvia

**Sintomo**:
```
Address already in use
```

**Soluzione**:
```bash
# Trova processo sulla porta 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Termina il processo o usa un'altra porta
python mock_crestron_server.py 8081
```

### Problema 2: Claude Non Vede il Server MCP

**Sintomi**:
- Nessuna icona 🔌 in Claude Desktop
- Server non in lista MCP

**Soluzioni**:
1. Verifica percorso assoluto in `claude_desktop_config.json`
2. Riavvia completamente Claude Desktop
3. Controlla i log di Claude:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### Problema 3: Errore "Not authenticated"

**Sintomo**:
```
Not authenticated or session expired
```

**Soluzione**:
Ri-autentica con Claude:
```
Autenticati con host: localhost:8080, token: test-token-123
```

### Problema 4: Test Automatici Falliscono

**Sintomo**:
```
❌ Mock Crestron server is not running!
```

**Soluzione**:
1. Verifica che il mock server sia in esecuzione
2. Controlla che sia sulla porta corretta (8080)
3. Prova a riavviare il mock server

### Problema 5: Import Error

**Sintomo**:
```
ModuleNotFoundError: No module named 'mcp'
```

**Soluzione**:
```bash
pip install --upgrade -r requirements.txt
```

---

## Prossimi Passi

### 1. Test Sistematici

Esegui tutti questi comandi con Claude per testare completamente:

**Autenticazione**:
- ✅ Autenticati con localhost:8080

**Scoperta**:
- ✅ Mostra le stanze
- ✅ Mostra i dispositivi in soggiorno
- ✅ Mostra tutti i sensori

**Controllo**:
- ✅ Chiudi la tapparella grande
- ✅ Apri tutte le tapparelle al 50%
- ✅ Attiva la scena Notte
- ✅ Imposta termostato a 23 gradi

**Risoluzione Naturale**:
- ✅ "Spegni il lampadario in soggiorno"
- ✅ "Controlla i sensori in cucina"
- ✅ "Che temperatura c'è?"

### 2. Modifica Mock Data

Puoi personalizzare i dati nel mock server editando `mock_crestron_server.py`:

- Aggiungi stanze modificando `ROOMS`
- Aggiungi dispositivi modificando `DEVICES`
- Aggiungi scene modificando `SCENES`

### 3. Transizione a Crestron Reale

Quando sei pronto per usare il sistema Crestron reale:

1. Ferma il mock server
2. Modifica la configurazione di Claude con il vero IP Crestron
3. Usa il token reale dal sistema Crestron
4. Tutto il resto funziona identico!

---

## Checklist Test Completi

Prima di considerare il test completo, verifica:

- [ ] Mock server si avvia correttamente
- [ ] Test automatici passano tutti (10/10)
- [ ] Claude si autentica con successo
- [ ] Scoperta stanze funziona
- [ ] Scoperta dispositivi funziona
- [ ] Controllo tapparelle funziona
- [ ] Attivazione scene funziona
- [ ] Controllo termostato funziona
- [ ] Lettura sensori funziona
- [ ] Risoluzione dispositivi per nome funziona
- [ ] Comandi in italiano funzionano
- [ ] Batch operations funzionano

---

## Supporto

Se hai problemi:

1. **Controlla i log** del mock server (nel terminale)
2. **Esegui i test automatici** per identificare il problema
3. **Verifica la configurazione** di Claude Desktop
4. **Controlla la sezione Risoluzione Problemi** sopra

---

## Conclusione

Ora hai un ambiente di test completo per il Crestron MCP server! 

Puoi:
- ✅ Testare tutte le funzionalità senza hardware reale
- ✅ Sviluppare e debuggare in sicurezza
- ✅ Verificare l'integrazione con Claude
- ✅ Testare comandi in italiano
- ✅ Simulare scenari realistici

**Buon testing! 🎉**
