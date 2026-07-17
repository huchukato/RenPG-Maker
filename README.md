# rpgm2vn

Convertitore da giochi **RPG Maker MV/MZ** a **Ren'Py** in stile visual novel.

## Obiettivo

Rimuovere la parte esplorativa della mappa e mantenere solo gli elementi di
visual novel: dialoghi, scelte, immagini, audio, variabili e rami condizionali.

## Installazione

```bash
cd /Users/huchukato/CascadeProjects/rpgm2vn
python3 -m pip install -e .
```

## Uso

```bash
python3 -m rpgm2vn.cli /percorso/gioco/www/data /percorso/output
```

Oppure:

```bash
python3 -m rpgm2vn /percorso/gioco/www/data /percorso/output
```

## Limitazioni attuali

- I comandi di movimento sulla mappa sono ignorati.
- I plugin personalizzati sono commentati o gestiti in modo euristico.
- Gli asset criptati (`.rpgmvp`, `.rpgmvo`, ...) non vengono copiati.
- Le mappe vengono generate come label; il flusso inizia dalla mappa di
  partenza definita in `System.json`.

## Test

Prova con il gioco di esempio:

```bash
python3 -m rpgm2vn "/Volumes/NVME/Games/Symphony of the Serpent/SymphonyOfTheSerpent[v.71071]-ITALIAN/www/data" "/tmp/sots_vn"
```
