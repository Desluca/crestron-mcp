# 🧪 Sistema di Test Crestron MCP

Sistema completo per testare il server MCP Crestron con mock server e integrazione Claude Desktop.

## 📁 File Inclusi

### File Principali
1. **mock_crestron_server.py** (13KB)
   - Server HTTP mock che simula API Crestron Home
   - Casa italiana tipica con 3 stanze, 15 dispositivi
   - Porta 8080, completamente standalone

2. **test_crestron_mcp.py** (10KB)
   - Suite di test automatici
   - 10 test che verificano tutti gli endpoint
   - Output colorato e dettagliato

3. **run_tests.sh** (5KB)
   - Script automatico che avvia tutto
   - Verifica dipendenze
   - Esegue test e fornisce istruzioni

### Guide e Documentazione
4. **GUIDA_TEST.md** (15KB)
   - Guida completa step-by-step
   - Setup, configurazione, troubleshooting
   - Esempi di conversazioni con Claude

5. **COMANDI_TEST.md** (7KB)
   - Quick reference con comandi pronti
   - 50+ comandi di esempio in italiano
   - Scenari completi da testare

## 🚀 Quick Start

### Metodo 1: Script Automatico (Consigliato)

```bash
# Avvia tutto automaticamente
./run_tests.sh

# Lo script farà:
# 1. Verifica dipendenze
# 2. Avvia mock server
# 3. Esegue test
# 4. Mostra istruzioni per Claude
```

### Metodo 2: Manuale

**Terminale 1 - Mock Server:**
```bash
python mock_crestron_server.py
```

**Terminale 2 - Test:**
```bash
python test_crestron_mcp.py
```

## 📊 Dati Mock - Casa Italiana

### Stanze (4)
- **Tutta la Casa** (ID: 1001) - Dispositivi globali
- **Soggiorno** (ID: 1) - 6 dispositivi
- **Camera da Letto** (ID: 2) - 6 dispositivi  
- **Cucina** (ID: 3) - 4 dispositivi

### Dispositivi (15)

#### Luci (8)
| Nome | ID | Tipo | Stanza | Stato Iniziale |
|------|-------|------|--------|----------------|
| Lampadario Soggiorno | 10 | Dimmer | Soggiorno | 100% |
| Applique Parete | 11 | Dimmer | Soggiorno | 50% |
| Lampada Lettura | 12 | Switch | Soggiorno | On |
| Lampadario Camera | 30 | Dimmer | Camera | Off |
| Abat-jour Sinistra | 31 | Dimmer | Camera | 25% |
| Abat-jour Destra | 32 | Dimmer | Camera | 25% |
| Luci Cucina | 60 | Dimmer | Cucina | 75% |
| Luce Piano Lavoro | 61 | Dimmer | Cucina | 100% |

#### Tapparelle (3)
| Nome | ID | Stanza | Posizione Iniziale |
|------|-------|--------|-------------------|
| Tapparella Grande | 20 | Soggiorno | Chiusa (0%) |
| Tapparella Finestra | 21 | Soggiorno | 50% |
| Tapparella Camera | 40 | Camera | Aperta (100%) |

#### Sensori (3)
| Nome | ID | Tipo | Stanza | Valore Iniziale |
|------|-------|------|--------|-----------------|
| Sensore Presenza Camera | 50 | Occupancy | Camera | Occupied |
| Sensore Luce Finestra | 70 | Photo | Cucina | 450 |
| Sensore Porta | 71 | Door | Cucina | Closed, Normal Battery |

#### Termostato (1)
| Nome | ID | Stanza | Configurazione |
|------|-------|--------|---------------|
| Termostato Principale | 80 | Casa | 23.5°C, Setpoint 22°C Cool, Fan Auto |

### Scene (7)
| Nome | ID | Tipo | Descrizione |
|------|-------|------|-------------|
| Tutto Acceso | 1 | Lighting | Accende tutte le luci |
| Tutto Spento | 2 | Lighting | Spegne tutte le luci |
| Film | 3 | Lighting | Abbassa luci soggiorno |
| Cena | 4 | Lighting | Illuminazione cucina |
| Notte | 5 | Lighting | Luci notturne camera |
| Buongiorno | 6 | Shade | Apre tapparelle |
| Buonanotte | 7 | Shade | Chiude tapparelle |

## 🧪 Test Inclusi

Lo script di test automatico verifica:

1. ✅ **Autenticazione** - Login con token
2. ✅ **Lista Stanze** - GET /rooms
3. ✅ **Lista Dispositivi** - GET /devices
4. ✅ **Stato Tapparelle** - GET /shades
5. ✅ **Controllo Tapparelle** - POST /shades/SetState
6. ✅ **Lista Scene** - GET /scenes
7. ✅ **Attivazione Scene** - POST /scenes/recall/{id}
8. ✅ **Stato Termostato** - GET /thermostats
9. ✅ **Controllo Termostato** - POST /thermostats/SetPoint
10. ✅ **Lettura Sensori** - GET /sensors

## 🔧 Configurazione

### Mock Server
```python
# In mock_crestron_server.py
PORT = 8080
AUTH_TOKEN = "test-token-123"
```

### Claude Desktop
```json
{
  "mcpServers": {
    "crestron": {
      "command": "python",
      "args": ["/path/assoluto/crestron_mcp.py"]
    }
  }
}
```

### Autenticazione MCP
```
Host: localhost:8080
Token: test-token-123
```

## 📝 Esempi di Test

### Con Script di Test
```bash
# Esegui tutti i test
python test_crestron_mcp.py

# Output atteso: 10/10 passed
```

### Con Claude Desktop

**1. Autenticazione:**
```
Autenticati con localhost:8080 token test-token-123
```

**2. Scoperta:**
```
Mostrami le stanze e i dispositivi
```

**3. Controllo:**
```
Chiudi la tapparella grande in soggiorno
```

**4. Scene:**
```
Attiva la scena Film
```

**5. Temperatura:**
```
Imposta il termostato a 21 gradi
```

## 🎯 Scenari di Test Completi

### Scenario 1: Sera Film
```
Prepara la casa per guardare un film:
- Attiva scena Film
- Chiudi tutte le tapparelle
- Abbassa termostato a 21 gradi
```

### Scenario 2: Mattina
```
Prepara la casa per la giornata:
- Attiva scena Buongiorno
- Verifica sensori
- Controlla temperatura
```

### Scenario 3: Partenza
```
Sto uscendo, metti tutto in sicurezza:
- Chiudi tutte le tapparelle
- Abbassa termostato a 18 gradi
- Verifica porte chiuse
```

## 📊 Log del Mock Server

Il mock server mostra log dettagliati:

```
✅ [AUTH] New session created: session-123...
📋 [ROOMS] Listing all rooms
📋 [DEVICES] Listing all devices
🎛️  [SHADES] Setting state for 1 shades
   ✅ Shade 20 (Tapparella Grande) → 0%
🎬 [SCENE] Activated scene 3 (Film)
   📺 Dimming living room lights to 10%...
🌡️  [THERMOSTAT] Setting 1 setpoint(s) for 80
   ✅ Cool setpoint → 21.0°C
```

## 🔍 Troubleshooting

### Problema: Porta occupata
```bash
# Trova processo
lsof -i :8080

# Termina
kill -9 <PID>

# Oppure usa porta diversa
python mock_crestron_server.py 8081
```

### Problema: Test falliscono
```bash
# Verifica mock server
curl http://localhost:8080/cws/api/rooms

# Verifica dipendenze
pip install -r requirements.txt

# Riavvia mock server
python mock_crestron_server.py
```

### Problema: Claude non vede MCP
1. Verifica percorso assoluto in config
2. Riavvia Claude Desktop completamente
3. Controlla log Claude

## 📚 Documentazione

### File Guida
- **GUIDA_TEST.md** - Guida completa con setup e troubleshooting
- **COMANDI_TEST.md** - 50+ comandi pronti da testare
- **README.md** - Documentazione principale MCP server

### Log e Debug
- **mock_server.log** - Log del mock server (se usi run_tests.sh)
- Output console - Log in tempo reale

## 🎓 Cosa Imparare

Questi test ti permettono di:

1. ✅ **Capire il protocollo MCP**
   - Come funzionano i tool
   - Input/output format
   - Error handling

2. ✅ **Testare senza hardware**
   - Sviluppo sicuro
   - Debug rapido
   - Iterazioni veloci

3. ✅ **Verificare integrazione Claude**
   - Risoluzione naturale del linguaggio
   - Disambiguazione
   - Batch operations

4. ✅ **Preparare deployment reale**
   - Una volta testato, basta cambiare host
   - Stessi comandi, hardware reale
   - Zero modifiche al codice

## 🚀 Prossimi Passi

### 1. Test Completo
- [ ] Esegui script automatico
- [ ] Verifica 10/10 test passati
- [ ] Prova comandi con Claude

### 2. Personalizzazione
- [ ] Modifica dati mock per la tua casa
- [ ] Aggiungi stanze e dispositivi
- [ ] Crea scene personalizzate

### 3. Deployment Reale
- [ ] Ottieni token Crestron reale
- [ ] Configura IP Crestron
- [ ] Testa con hardware reale

## 📞 Supporto

Per problemi o domande:

1. Consulta **GUIDA_TEST.md** sezione troubleshooting
2. Verifica log del mock server
3. Esegui test automatici per identificare il problema
4. Controlla configurazione Claude Desktop

## 🎉 Conclusione

Hai ora un ambiente di test completo che ti permette di:

- ✅ Sviluppare in sicurezza
- ✅ Testare tutte le funzionalità
- ✅ Verificare l'integrazione con Claude
- ✅ Simulare scenari realistici
- ✅ Prepararti per il deployment reale

**Il mock server è identico all'API Crestron reale** - quando sei pronto, basta cambiare l'host e tutto funziona con l'hardware vero!

---

**Buon testing! 🏠🤖**
