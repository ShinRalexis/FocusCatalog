FOCUSCATALOG — README.TXT ENG
================================

Short preface
-------------
FocusCatalog is a **local catalog** for your Fooocus models (Checkpoints and LoRA).
It scans the folders you choose, builds an **index** with thumbnails, file size and dates,
and — if you want — imports **trigger words** and **previews** from Civitai by linking a model card.
The UI runs on a small Flask server and exposes simple APIs for health, config, rescan and preview import.

Folder contents
---------------
- server.py   — Flask server + APIs and static files (serves index.html, options.html, help.html).
- scan_models.py — Model scanner: creates public/index.json, generates thumbnails and marks "NEW".
- index.html  — Catalog page with cards, search, filters, favorites, "NEW" badge and Civitai link.
- options.html — Options: save paths (checkpoints/LoRA) and global NSFW filter.
- help.html   — Quick guide and usage tips.
- public/     — Output and static assets folder (index.json, config.json, previews will be created here).

Requirements (native install)
-----------------------------
- Python 3.10+ recommended.
- Packages: flask, flask-cors, requests, Pillow.

Install packages (Windows, macOS, Linux)
----------------------------------------
(Optional) create and activate a virtual environment, then install requirements:

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install flask flask-cors requests pillow

Native run (without Docker) — Step by step
------------------------------------------
1) Unzip the project (HTML and Python files must be together).
2) Start the server (pick one):

   Windows (PowerShell):
       python server.py --host 127.0.0.1 --port 8765 --out public

   macOS / Linux:
       python server.py --host 127.0.0.1 --port 8765 --out public

   Useful CLI options:
       --roots <folder1> <folder2>       # pre-set the roots to scan
       --scan-script <path/scan_models.py>  # if scan_models.py lives elsewhere

3) Open the browser at: http://127.0.0.1:8765/
   The server serves static files from the “--out” folder (default: public).

4) Set your paths in "Options"
   - Fill in "Checkpoints folder path" and "LoRA folder path" then click "Save settings".
   - This writes public/config.json and the paths are applied immediately (no restart needed).

5) Scan your models
   - From the main page click "Refresh catalog" (calls /api/refresh) and updates index.json.

6) (Optional) Add a Civitai link to a card
   - Click the little gear on the card and paste the Civitai link (you can use a modelVersionId).
   - Up to 3 previews will be downloaded; the display name and — for LoRA — the trigger words will be updated.
   - If you place a local image with the same file name of the model (.png/.jpg/.jpeg/.webp),
     it will be used as the preview.

7) Favorites, NSFW, New
   - Favorites are stored locally in your browser (localStorage).
   - The global "SAFE only / Also show NSFW" filter is in Options.
   - Recently added/modified models (e.g., <= 30 days) are marked with the "NEW" badge.

Run with Docker (recommended)
-----------------------------
Prerequisites: Docker Desktop (Windows/macOS) or Docker Engine (Linux).

A) Dockerfile (place next to server.py and scan_models.py)
----------------------------------------------------------
    FROM python:3.11-slim
    WORKDIR /app
    COPY server.py scan_models.py index.html options.html help.html ./
    RUN pip install --no-cache-dir flask flask-cors requests pillow
    EXPOSE 8765
    CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8765", "--out", "public"]

B) docker-compose.yml (recommended)
-----------------------------------
Replace host paths with yours (Windows: C:/path/...; Linux/macOS: /path/...)

    services:
      focuscatalog:
        build: .
        ports:
          - "8765:8765"
        volumes:
          # Model folders (read-only)
          - C:/PATH/TO/checkpoints:/models/checkpoints:ro
          - C:/PATH/TO/loras:/models/loras:ro
          # Persist output (index.json, previews, config.json)
          - ./public:/app/public
        command: >
          python server.py --host 0.0.0.0 --port 8765
          --out public
          --roots /models/checkpoints /models/loras
        restart: unless-stopped

Quick commands
--------------
    # build image and start with Compose
    docker compose build
    docker compose up -d
    # then open http://localhost:8765

    # alternative: single docker run
    docker build -t focuscatalog .

    # Windows (PowerShell ^ for line continuation)
    docker run --rm -p 8765:8765 ^
      -v C:/PATH/TO/checkpoints:/models/checkpoints:ro ^
      -v C:/PATH/TO/loras:/models/loras:ro ^
      -v %cd%/public:/app/public ^
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

    # Linux/macOS
    docker run --rm -p 8765:8765 \
      -v /PATH/TO/checkpoints:/models/checkpoints:ro \
      -v /PATH/TO/loras:/models/loras:ro \
      -v "$PWD/public":/app/public \
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

API quick reference
-------------------
- GET  /api/health              → server status and current roots
- GET  /api/index               → current public/index.json
- GET  /api/config              → read saved checkpointDir / loraDir (with current roots)
- POST /api/config (JSON)       → save paths and update roots at runtime
- POST /api/refresh             → run scan_models.py with current roots and rebuild the index
- POST /api/set_link_and_fetch  → save civitai_url to a card, download previews and (for LoRA) trigger words

Supported formats & previews
----------------------------
- Models: .safetensors, .ckpt, .pt, .bin, .gguf
- Preview images: .png, .jpg, .jpeg, .webp (thumbnails auto-created in public/assets/previews/<slug>/...)
- Civitai previews are saved to assets/previews/<slug>/civitai_#.png|jpg and shown in the model card.

Packaging tip
-------------
Do NOT ship your personal data files:
- Exclude: public/index.json, public/config.json, public/assets/previews/
- Include: server.py, scan_models.py, HTML files, images, and an empty public/ (you may add a .keep).

Troubleshooting
---------------
- "scan_models.py not found" → start the server with --scan-script pointing to the correct path,
  or keep server.py and scan_models.py in the same directory.
- "Invalid path" on /api/config → make sure the folder exists, then save again.
- Expose to LAN → use --host 0.0.0.0 (remember APIs use permissive CORS: protect access at network level).
- No preview shown → add a local image with the same base name as the model, or link Civitai.

Thank you
---------
If FocusCatalog helps you, a small thank-you is always appreciated. Enjoy your catalog!

— MetaDarko

FOCUSCATALOG — README.TXT ITA
================================

Piccolo preambolo
-----------------
FocusCatalog è un **catalogo locale** per i tuoi modelli di Fooocus (Checkpoint e LoRA).
Scansiona le cartelle che indichi, genera un index con anteprime, dimensioni, date e — se vuoi —
importa trigger words e preview da Civitai collegando la scheda del modello al relativo link.
L’interfaccia gira via un server Flask leggero ed espone API per:
salute, configurazione percorsi, refresh scansione e download preview.

Contenuto della cartella
------------------------
- server.py — server Flask + API e statici (serve index.html, options.html, help.html).
- scan_models.py — scanner dei modelli: genera public/index.json, crea miniature e marca “NUOVO”.
- index.html — catalogo con cards, ricerca, filtri, preferiti, badge “NUOVO” e link Civitai.
- options.html — opzioni: salvataggio percorsi (checkpoint/LoRA) e filtro NSFW globale.
- help.html — guida rapida e consigli d’uso.

Requisiti (installazione “nativa”)
----------------------------------
- Python 3.10+ consigliato.
- Pacchetti: flask, flask-cors, requests, Pillow.

Installazione pacchetti (Windows, macOS, Linux)
-----------------------------------------------
(opzionale) crea e attiva un ambiente virtuale, poi installa i requisiti:

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install flask flask-cors requests pillow

Avvio “nativo” (senza Docker) — Passo passo
-------------------------------------------
1) Scompatta la cartella del progetto (i file HTML e Python devono stare insieme).
2) Avvia il server (scegli uno dei comandi):

   Windows (PowerShell):
       python server.py --host 127.0.0.1 --port 8765 --out public

   macOS / Linux:
       python server.py --host 127.0.0.1 --port 8765 --out public

   Opzioni utili a riga di comando:
       --roots <cartella1> <cartella2>   # Imposta subito le radici da scansionare
       --scan-script <path/scan_models.py>  # Se si trova altrove

3) Apri il browser su: http://127.0.0.1:8765/
   Il server espone i file statici dalla cartella “--out” (default: public).

4) Imposta i percorsi in ⚙️ Opzioni
   - Compila “Percorso cartella Checkpoints” e “Percorso cartella LoRA”, poi “Salva impostazioni”.
   - Viene scritto public/config.json e i percorsi sono applicati SUBITO (senza riavvio).

5) Scansiona i modelli
   - Dalla pagina principale premi “Aggiorna catalogo” (chiama /api/refresh) e aggiorna index.json.

6) (Facoltativo) Civitai su una scheda
   - Clicca l’ingranaggio nella card → incolla il link Civitai (puoi usare un modelVersionId).
   - Verranno scaricate fino a 3 preview; verranno aggiornati nome visualizzato e — per i LoRA — le trigger words.
   - Se metti un’immagine locale con lo stesso nome del file modello (.png/.jpg/.jpeg/.webp), verrà usata come anteprima.

7) Preferiti, NSFW, Nuovi
   - Le stelline/cuori dei preferiti sono locali al browser (salvati sul tuo dispositivo).
   - Il filtro “Solo SAFE / Mostra anche NSFW” è in ⚙️ Opzioni.
   - I modelli aggiunti/modificati di recente (es. ≤30 giorni) sono marcati con il badge “NUOVO”.

Avvio con Docker (consigliato)
------------------------------
Prerequisiti: Docker Desktop (Windows/macOS) o Docker Engine (Linux).

A) Dockerfile (posiziona accanto a server.py e scan_models.py)
--------------------------------------------------------------
    FROM python:3.11-slim
    WORKDIR /app
    COPY server.py scan_models.py index.html options.html help.html ./
    RUN pip install --no-cache-dir flask flask-cors requests pillow
    EXPOSE 8765
    CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8765", "--out", "public"]

B) docker-compose.yml (consigliato)
-----------------------------------
Sostituisci i percorsi host con i tuoi (su Windows: C:/percorso/...; su Linux/macOS: /percorso/...)

    services:
      focuscatalog:
        build: .
        ports:
          - "8765:8765"
        volumes:
          # Cartelle modelli in sola lettura
          - C:/PATH/TO/checkpoints:/models/checkpoints:ro
          - C:/PATH/TO/loras:/models/loras:ro
          # Persistenza dell'output (index.json, previews, config.json)
          - ./public:/app/public
        command: >
          python server.py --host 0.0.0.0 --port 8765
          --out public
          --roots /models/checkpoints /models/loras
        restart: unless-stopped

Comandi rapidi
--------------
    # build immagine e avvio con Compose
    docker compose build
    docker compose up -d
    # apri poi il browser su http://localhost:8765

    # in alternativa, docker run singolo
    docker build -t focuscatalog .
    docker run --rm -p 8765:8765 ^
      -v C:/PATH/TO/checkpoints:/models/checkpoints:ro ^
      -v C:/PATH/TO/loras:/models/loras:ro ^
      -v %cd%/public:/app/public ^
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

API (panoramica rapida)
-----------------------
- GET  /api/health            → stato server e radici correnti
- GET  /api/index             → download di public/index.json
- GET  /api/config            → legge checkpointDir / loraDir salvati (con roots correnti)
- POST /api/config (JSON)     → salva percorsi e aggiorna le roots a runtime
- POST /api/refresh           → esegue scan_models.py con le roots correnti e rigenera l’indice
- POST /api/set_link_and_fetch → collega civitai_url a una scheda, scarica preview e (per LoRA) trigger words

Formati supportati e anteprime
------------------------------
- Modelli: .safetensors, .ckpt, .pt, .bin, .gguf
- Immagini anteprima: .png, .jpg, .jpeg, .webp (thumbnail automatiche in public/assets/previews/<slug>/...)
- Preview da Civitai salvate in assets/previews/<slug>/civitai_#.png|jpg e mostrate nella card del modello.

Troubleshooting veloce
----------------------
- “scan_models.py non trovato” → avvia server con --scan-script puntando al percorso corretto oppure
  assicurati che server.py e scan_models.py siano nella stessa cartella.
- “Percorso non valido” in /api/config → verifica che la directory esista e riprova a salvare.
- Esporre sulla LAN → usa --host 0.0.0.0 (ricorda che l’API ha CORS permissivo: proteggi l’accesso a livello rete).
- Se non vedi anteprime → metti file immagine con lo stesso nome del modello accanto al file .safetensors/.ckpt, oppure collega Civitai.

Grazie!
-------
Se FocusCatalog ti è utile, un piccolo “grazie” fa sempre piacere. Buon catalogo!

— MetaDarko

FOCUSCATALOG — README.TXT ESP
================================

Breve preámbulo
----------------
FocusCatalog es un **catálogo local** para tus modelos de Fooocus (Checkpoints y LoRA).
Escanea las carpetas que elijas, crea un **índice** con miniaturas, tamaño y fechas
y — si quieres — importa **trigger words** y **previews** desde Civitai enlazando la ficha del modelo.
La interfaz corre sobre un pequeño servidor Flask y expone APIs sencillas para estado, configuración,
re-escaneo e importación de previews.

Contenido de la carpeta
-----------------------
- server.py        — Servidor Flask + APIs y archivos estáticos (sirve index.html, options.html, help.html).
- scan_models.py   — Escáner de modelos: crea public/index.json, genera miniaturas y marca "NEW".
- index.html       — Catálogo con tarjetas, búsqueda, filtros, favoritos, distintivo "NEW" y enlace a Civitai.
- options.html     — Opciones: guardar rutas (checkpoints/LoRA) y filtro NSFW global.
- help.html        — Guía rápida y consejos de uso.
- public/          — Carpeta de salida y estáticos (aquí se crearán index.json, config.json, previews).

Requisitos (instalación nativa)
-------------------------------
- Se recomienda Python 3.10+.
- Paquetes: flask, flask-cors, requests, Pillow.

Instalar paquetes (Windows, macOS, Linux)
-----------------------------------------
(Opcional) crea y activa un entorno virtual y luego instala los requisitos:

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install flask flask-cors requests pillow

Ejecución nativa (sin Docker) — Paso a paso
-------------------------------------------
1) Descomprime el proyecto (los archivos HTML y Python deben ir juntos).
2) Inicia el servidor (elige uno):

   Windows (PowerShell):
       python server.py --host 127.0.0.1 --port 8765 --out public

   macOS / Linux:
       python server.py --host 127.0.0.1 --port 8765 --out public

   Opciones útiles de CLI:
       --roots <carpeta1> <carpeta2>         # define desde ya las raíces a escanear
       --scan-script <ruta/scan_models.py>   # si scan_models.py está en otra ubicación

3) Abre el navegador en: http://127.0.0.1:8765/
   El servidor sirve los estáticos desde la carpeta “--out” (por defecto: public).

4) Configura tus rutas en "Opciones"
   - Completa "Ruta de la carpeta Checkpoints" y "Ruta de la carpeta LoRA" y pulsa "Guardar".
   - Se escribe public/config.json y las rutas se aplican **de inmediato** (sin reiniciar).

5) Escanear modelos
   - En la página principal pulsa "Actualizar catálogo" (llama a /api/refresh) y actualiza index.json.

6) (Opcional) Añadir enlace de Civitai a una tarjeta
   - Pulsa el engranaje de la tarjeta y pega el enlace de Civitai (puedes usar un modelVersionId).
   - Se descargarán hasta 3 previews; se actualizarán el nombre visible y — para LoRA — las trigger words.
   - Si colocas una imagen local con el **mismo nombre de archivo** del modelo (.png/.jpg/.jpeg/.webp),
     se usará como preview.

7) Favoritos, NSFW, Nuevos
   - Los favoritos se guardan localmente en tu navegador (localStorage).
   - El filtro global "Sólo SAFE / Mostrar también NSFW" está en Opciones.
   - Los modelos añadidos/modificados recientemente (p. ej., ≤ 30 días) llevan el distintivo "NEW".

Ejecutar con Docker (recomendado)
---------------------------------
Requisitos previos: Docker Desktop (Windows/macOS) o Docker Engine (Linux).

A) Dockerfile (colócalo junto a server.py y scan_models.py)
-----------------------------------------------------------
    FROM python:3.11-slim
    WORKDIR /app
    COPY server.py scan_models.py index.html options.html help.html ./
    RUN pip install --no-cache-dir flask flask-cors requests pillow
    EXPOSE 8765
    CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8765", "--out", "public"]

B) docker-compose.yml (recomendado)
-----------------------------------
Sustituye las rutas del host por las tuyas (Windows: C:/ruta/...; Linux/macOS: /ruta/...)

    services:
      focuscatalog:
        build: .
        ports:
          - "8765:8765"
        volumes:
          # Carpetas de modelos en solo lectura
          - C:/PATH/TO/checkpoints:/models/checkpoints:ro
          - C:/PATH/TO/loras:/models/loras:ro
          # Persistencia de salida (index.json, previews, config.json)
          - ./public:/app/public
        command: >
          python server.py --host 0.0.0.0 --port 8765
          --out public
          --roots /models/checkpoints /models/loras
        restart: unless-stopped

Comandos rápidos
----------------
    # construir imagen e iniciar con Compose
    docker compose build
    docker compose up -d
    # luego abre http://localhost:8765

    # alternativa: un solo docker run
    docker build -t focuscatalog .

    # Windows (PowerShell, ^ para continuar líneas)
    docker run --rm -p 8765:8765 ^
      -v C:/PATH/TO/checkpoints:/models/checkpoints:ro ^
      -v C:/PATH/TO/loras:/models/loras:ro ^
      -v %cd%/public:/app/public ^
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

    # Linux/macOS
    docker run --rm -p 8765:8765 \
      -v /PATH/TO/checkpoints:/models/checkpoints:ro \
      -v /PATH/TO/loras:/models/loras:ro \
      -v "$PWD/public":/app/public \
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

Referencia rápida de la API
---------------------------
- GET  /api/health              → estado del servidor y raíces actuales
- GET  /api/index               → public/index.json actual
- GET  /api/config              → lee checkpointDir / loraDir guardados (con raíces actuales)
- POST /api/config (JSON)       → guarda rutas y actualiza raíces en caliente
- POST /api/refresh             → ejecuta scan_models.py con las raíces actuales y regenera el índice
- POST /api/set_link_and_fetch  → guarda civitai_url en una tarjeta, descarga previews y (para LoRA) trigger words

Formatos soportados y previews
------------------------------
- Modelos: .safetensors, .ckpt, .pt, .bin, .gguf
- Imágenes de preview: .png, .jpg, .jpeg, .webp (miniaturas automáticas en public/assets/previews/<slug>/...)
- Las previews de Civitai se guardan en assets/previews/<slug>/civitai_#.png|jpg y se muestran en la tarjeta.

Consejos de empaquetado
-----------------------
NO distribuyas tus datos personales:
- Excluir: public/index.json, public/config.json, public/assets/previews/
- Incluir: server.py, scan_models.py, archivos HTML, imágenes y una carpeta public/ vacía (puedes añadir un .keep).

Solución de problemas
---------------------
- "scan_models.py not found" → inicia el servidor con --scan-script apuntando a la ruta correcta,
  o mantén server.py y scan_models.py en el mismo directorio.
- "Invalid path" en /api/config → asegúrate de que la carpeta exista y vuelve a guardar.
- Exponer en LAN → usa --host 0.0.0.0 (recuerda que las APIs usan CORS permisivo: protege el acceso a nivel de red).
- No se ve la preview → añade una imagen local con el mismo nombre base del modelo o enlaza Civitai.

Gracias
-------
Si FocusCatalog te ayuda, siempre se agradece un pequeño “gracias”. ¡Disfruta del catálogo!

— MetaDarko

FOCUSCATALOG — README.TXT FR
================================

Bref préambule
--------------
FocusCatalog est un **catalogue local** pour vos modèles Fooocus (Checkpoints et LoRA).
Il analyse les dossiers que vous choisissez, construit un **index** avec vignettes, tailles et dates,
et — si vous le souhaitez — importe **trigger words** et **aperçus (previews)** depuis Civitai en liant la fiche d’un modèle.
L’interface tourne sur un petit serveur Flask et expose des API simples pour l’état, la configuration,
le rescannage et l’import des aperçus.

Contenu du dossier
------------------
- server.py        — Serveur Flask + API et fichiers statiques (sert index.html, options.html, help.html).
- scan_models.py   — Scanner de modèles : crée public/index.json, génère des vignettes et marque « NEW ».
- index.html       — Catalogue avec cartes, recherche, filtres, favoris, badge « NEW » et lien Civitai.
- options.html     — Options : enregistrement des chemins (checkpoints/LoRA) et filtre NSFW global.
- help.html        — Guide rapide et conseils d’utilisation.
- public/          — Dossier de sortie et des statiques (index.json, config.json, aperçus seront générés ici).

Prérequis (installation native)
-------------------------------
- Python 3.10+ recommandé.
- Paquets : flask, flask-cors, requests, Pillow.

Installer les paquets (Windows, macOS, Linux)
---------------------------------------------
(Facultatif) créez et activez un environnement virtuel, puis installez les dépendances :

    python -m venv .venv
    # Windows : .venv\Scripts\activate
    # macOS/Linux : source .venv/bin/activate
    pip install flask flask-cors requests pillow

Exécution « native » (sans Docker) — Pas à pas
----------------------------------------------
1) Décompressez le projet (les fichiers HTML et Python doivent rester ensemble).
2) Lancez le serveur (choisissez une commande) :

   Windows (PowerShell) :
       python server.py --host 127.0.0.1 --port 8765 --out public

   macOS / Linux :
       python server.py --host 127.0.0.1 --port 8765 --out public

   Options CLI utiles :
       --roots <dossier1> <dossier2>          # définir tout de suite les racines à scanner
       --scan-script <chemin/scan_models.py>  # si scan_models.py se trouve ailleurs

3) Ouvrez le navigateur sur : http://127.0.0.1:8765/
   Le serveur sert les fichiers statiques depuis le dossier « --out » (par défaut : public).

4) Définissez vos chemins dans « Options »
   - Renseignez « Dossier Checkpoints » et « Dossier LoRA », puis cliquez sur « Enregistrer ».
   - Un fichier public/config.json est écrit et les chemins sont appliqués **immédiatement** (sans redémarrage).

5) Scanner les modèles
   - Depuis la page principale, cliquez « Actualiser le catalogue » (appelle /api/refresh) et met à jour index.json.

6) (Facultatif) Ajouter un lien Civitai à une carte
   - Cliquez sur le petit engrenage de la carte et collez le lien Civitai (vous pouvez utiliser un modelVersionId).
   - Jusqu’à 3 aperçus seront téléchargés ; le nom d’affichage et — pour les LoRA — les trigger words seront mis à jour.
   - Si vous placez une image locale portant **le même nom de fichier** que le modèle (.png/.jpg/.jpeg/.webp),
     elle sera utilisée comme aperçu.

7) Favoris, NSFW, Nouveaux
   - Les favoris sont stockés localement dans votre navigateur (localStorage).
   - Le filtre global « SAFE uniquement / Afficher aussi NSFW » se trouve dans Options.
   - Les modèles ajoutés/modifiés récemment (p. ex. ≤ 30 jours) portent le badge « NEW ».

Exécuter avec Docker (recommandé)
---------------------------------
Prérequis : Docker Desktop (Windows/macOS) ou Docker Engine (Linux).

A) Dockerfile (à placer à côté de server.py et scan_models.py)
--------------------------------------------------------------
    FROM python:3.11-slim
    WORKDIR /app
    COPY server.py scan_models.py index.html options.html help.html ./
    RUN pip install --no-cache-dir flask flask-cors requests pillow
    EXPOSE 8765
    CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8765", "--out", "public"]

B) docker-compose.yml (recommandé)
----------------------------------
Remplacez les chemins hôtes par les vôtres (Windows : C:/chemin/... ; Linux/macOS : /chemin/...) :

    services:
      focuscatalog:
        build: .
        ports:
          - "8765:8765"
        volumes:
          # Dossiers des modèles en lecture seule
          - C:/PATH/TO/checkpoints:/models/checkpoints:ro
          - C:/PATH/TO/loras:/models/loras:ro
          # Persistance (index.json, previews, config.json)
          - ./public:/app/public
        command: >
          python server.py --host 0.0.0.0 --port 8765
          --out public
          --roots /models/checkpoints /models/loras
        restart: unless-stopped

Commandes rapides
-----------------
    # construire l’image et démarrer avec Compose
    docker compose build
    docker compose up -d
    # puis ouvrez http://localhost:8765

    # alternative : docker run unique
    docker build -t focuscatalog .

    # Windows (PowerShell, ^ pour continuation de ligne)
    docker run --rm -p 8765:8765 ^
      -v C:/PATH/TO/checkpoints:/models/checkpoints:ro ^
      -v C:/PATH/TO/loras:/models/loras:ro ^
      -v %cd%/public:/app/public ^
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

    # Linux/macOS
    docker run --rm -p 8765:8765 \
      -v /PATH/TO/checkpoints:/models/checkpoints:ro \
      -v /PATH/TO/loras:/models/loras:ro \
      -v "$PWD/public":/app/public \
      focuscatalog python server.py --host 0.0.0.0 --port 8765 --out public --roots /models/checkpoints /models/loras

Référence rapide de l’API
-------------------------
- GET  /api/health              → état du serveur et racines actuelles
- GET  /api/index               → public/index.json courant
- GET  /api/config              → lit checkpointDir / loraDir enregistrés (avec racines actuelles)
- POST /api/config (JSON)       → enregistre les chemins et met à jour les racines à chaud
- POST /api/refresh             → exécute scan_models.py avec les racines courantes et reconstruit l’index
- POST /api/set_link_and_fetch  → enregistre civitai_url sur une carte, télécharge des aperçus et (pour LoRA) les trigger words

Formats pris en charge & aperçus
--------------------------------
- Modèles : .safetensors, .ckpt, .pt, .bin, .gguf
- Images d’aperçu : .png, .jpg, .jpeg, .webp (vignettes auto-créées dans public/assets/previews/<slug>/...)
- Les aperçus Civitai sont sauvegardés dans assets/previews/<slug>/civitai_#.png|jpg et affichés sur la carte du modèle.

Conseils de packaging
---------------------
Ne diffusez PAS vos fichiers personnels :
- Exclure : public/index.json, public/config.json, public/assets/previews/
- Inclure : server.py, scan_models.py, fichiers HTML, images, et un dossier public/ vide (vous pouvez ajouter un .keep).

Dépannage
---------
- « scan_models.py not found » → démarrez le serveur avec --scan-script pointant vers le bon chemin,
  ou gardez server.py et scan_models.py dans le même répertoire.
- « Invalid path » sur /api/config → vérifiez que le dossier existe puis enregistrez à nouveau.
- Exposer sur le LAN → utilisez --host 0.0.0.0 (les API ont un CORS permissif : protégez l’accès au niveau réseau).
- Aucun aperçu affiché → placez une image locale portant le même nom de base que le modèle, ou liez Civitai.

Merci
-----
Si FocusCatalog vous est utile, un petit merci fait toujours plaisir. Bon catalogue !

— MetaDarko