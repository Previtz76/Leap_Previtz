# Leapmotor B10 OTA — archivio italiano

Sito statico per GitHub Pages con monitoraggio giornaliero dello storico OTA della pagina tedesca:
https://leapmotor.bwwb.de/modelle/b10/

## Cosa fa
- Scarica ogni giorno la pagina di riferimento.
- Estrae le schede OTA e le relative fonti.
- Distingue fonti ufficiali, community e rumor non confermati con euristiche trasparenti.
- Rileva schede nuove o modificate e conserva le voci precedenti se la fonte non le mostra temporaneamente.
- Traduce titoli e contenuti in italiano tramite DeepL API Free.
- Pubblica il sito come pagina statica e mantiene `data/ota.json` nello storico Git.

## Pubblicazione su GitHub Pages
1. Crea un repository GitHub nuovo (pubblico se vuoi usare GitHub Pages gratis).
2. Carica tutti i file e le cartelle di questo progetto nella radice del repository.
3. Vai in **Settings → Pages** e seleziona **Deploy from a branch**, branch `main`, cartella `/ (root)`, quindi salva.
4. Vai in **Settings → Secrets and variables → Actions → New repository secret**.
5. Crea il secret `DEEPL_API_KEY` con una chiave DeepL API Free. La chiave è necessaria per tradurre automaticamente; senza di essa il sistema archivia il testo ma lo contrassegna come non tradotto.
6. Apri **Actions → Aggiorna archivio OTA B10 → Run workflow** per il primo controllo manuale.
7. Attendi il completamento del workflow. Il sito sarà pubblicato all'indirizzo `https://TUO-UTENTE.github.io/NOME-REPOSITORY/`.

## Controllo giornaliero
Il workflow è pianificato alle 04:20 UTC ogni giorno. GitHub può ritardare l'avvio dei workflow pianificati nei momenti di carico. Puoi avviarlo manualmente dalla scheda Actions.

## Limiti e verifiche da fare
- La struttura HTML del sito sorgente può cambiare; se succede, va aggiornato `scripts/update_ota.py`.
- Il rilevamento ufficiale/community/rumor è automatico e imperfetto: verifica sempre le fonti collegate.
- Le traduzioni sono automatiche: consulta il tedesco originale per i dettagli importanti.
- La pagina monitorata è un progetto indipendente, non Leapmotor/Stellantis. Il sito italiano qui creato è a sua volta indipendente.
- Il sito sorgente può aggiornare una scheda esistente invece di aggiungerne una nuova; il sistema prova a rilevare le modifiche confrontando il contenuto.
- Il primo avvio può richiedere alcuni minuti e potrebbe fallire se la fonte limita le richieste.

## Costi
GitHub Pages e GitHub Actions per un piccolo repository pubblico sono normalmente utilizzabili gratuitamente entro i limiti del piano. DeepL API Free richiede registrazione e una chiave gratuita con limiti di utilizzo; non è una chiave inclusa in questo progetto.

## Licenze e attribuzione
Il sito non copia immagini del progetto originale. Mostra estratti testuali e collegamenti alla fonte originale, con attribuzione. Se il progetto viene reso pubblico, mantieni visibili gli avvisi di indipendenza e i link alle fonti.
