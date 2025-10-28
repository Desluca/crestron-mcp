# Su Windows
cd C:\path\to\your\files
cd
# Output: C:\Users\tuonome\Downloads\crestron

# Il percorso sarà: C:\Users\tuonome\Downloads\crestron\crestron_mcp.py
```

### 3️⃣ Riavvia Claude Desktop

Chiudi **completamente** Claude Desktop e riaprilo.

### 4️⃣ Verifica Connessione

In Claude Desktop, dovresti vedere:
- Un'icona 🔌 nella barra inferiore
- Cliccandoci, vedi "crestron" nella lista

## 🎯 Workflow Completo per il Tuo Esempio

Ora quando chiedi: **"Spegni il lampadario del soggiorno"**

Claude farà automaticamente:

### Step 1: Autenticazione (prima volta)

**Tu devi dire a Claude**:
```
Prima di tutto, autenticati con il sistema Crestron usando:
- Host: localhost:8080  
- Token: test-token-123
```

Claude chiamerà `crestron_authenticate` e otterrà la sessione.

### Step 2: Il Tuo Comando

**Tu**:
```
Spegni il lampadario del soggiorno
```

**Claude farà automaticamente**:

1. **Risoluzione del dispositivo**:
```
   Tool: crestron_resolve_device
   Input: {
     "utterance": "lampadario soggiorno",
     "preferred_room_id": null
   }