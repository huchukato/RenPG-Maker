# 🎮 RenPG Maker

![RenPG Maker Logo](img/logo_512.png)

![Python](https://img.shields.io/badge/python-3.8+-06b6d4.svg)
![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-7c3aed.svg)

Converti giochi **RPG Maker MV/MZ** in visual novel **Ren'Py**, mantenendo solo dialoghi, scelte, immagini, audio, variabili e rami condizionali.

![RenPG Maker GUI](img/gui.png)

## 🚀 Installazione e avvio

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

`uv` viene installato automaticamente se non presente. Gli script `start.sh` / `start.bat` creano anche un ambiente virtuale e installano le dipendenze necessarie.

Puoi anche avviare la GUI direttamente:

```bash
python3 -m rpgm2vn.gui
```

Oppure usare la riga di comando:

```bash
python3 -m rpgm2vn.cli /percorso/gioco/www/data /percorso/output
```

## 🎬 Converti e Builda

La GUI supporta anche il workflow one-click **Converti e Builda**:

1. Seleziona il gioco e la cartella di output.
2. Scegli il target di build: `all`, `win`, `mac` o `linux`.
3. Clicca **Converti e Builda**.

La prima volta che fai la build, l'SDK Ren'Py 8.5.3 viene scaricato automaticamente in `renpy-sdk/`. Poi il progetto viene convertito e impacchettato per la piattaforma desktop scelta.

Gli asset criptati di RPG Maker MV/MZ (`.rpgmvp`, `.rpgmvo`, `.rpgmvm`, `.rpgmve`) vengono decriptati automaticamente usando la chiave in `System.json`. Anche i filmati nella cartella `movies/` vengono copiati nel progetto.

## 🎨 UI, icona e splash screen

La GUI usa una palette ispirata al logo del progetto, con il logo ingrandito in alto a sinistra e l'icona RenPG nella finestra. Anche il gioco Ren'Py generato mostra uno splash screen prima del menu principale, usando `img/splash.png`, visualizzato una sola volta per sessione per 2,5 secondi.

## 📦 Build per tutte le piattaforme

Oltre al workflow **Converti e Builda** della GUI, puoi creare bundle standalone per la piattaforma che preferisci:

### Sorgenti (`build.sh`)

```bash
./build.sh
```

Genera `dist/RenPGMaker-v0.1.0.zip` con i file sorgente del progetto, pronto per essere distribuito o eseguito manualmente.

### macOS

```bash
./build/build_mac_app.sh
```

Crea `dist/RenPGMaker.app`, un bundle `.app` autocontenuto con icona, virtual environment e file del progetto. Girerà nativamente su Apple Silicon (M1/M2/M3) e su Intel.

### Linux

```bash
./build/build_linux.sh
```

Crea `dist/RenPGMaker-linux/` contenente il progetto, `.venv` e uno script `start.sh` per avviare la GUI.

### Windows

```bat
build\build_windows.bat
```

Crea `dist\RenPGMaker-windows\` contenente il progetto, `.venv` e `start.bat` per avviare la GUI.
