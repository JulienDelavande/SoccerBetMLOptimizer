import os
import shutil

# Dossier source et destination
SRC_DIR = "logos/teams/1x1"
DST_DIR = "logos/teams"

# Mapping manuel des équipes nationales vers le fichier de drapeau correspondant
NATIONAL_TEAMS_FLAG_MAP = {
    "Argentina": "ar.svg",
    "Australia": "au.svg",
    "Austria": "at.svg",
    "Belgium": "be.svg",
    "Brazil": "br.svg",
    "Cameroon": "cm.svg",
    "Canada": "ca.svg",
    "Chile": "cl.svg",
    "China PR": "cn.svg",
    "Colombia": "co.svg",
    "Costa Rica": "cr.svg",
    "Croatia": "hr.svg",
    "Czechia": "cz.svg",
    "Czechoslovakia": "cs.svg",  # Hypothétique : vérifier s'il existe
    "Denmark": "dk.svg",
    "Dutch East Indies": "id.svg",
    "Ecuador": "ec.svg",
    "Egypt": "eg.svg",
    "El Salvador": "sv.svg",
    "England": "gb-eng.svg",
    "Finland": "fi.svg",
    "France": "fr.svg",
    "Germany": "de.svg",
    "Ghana": "gh.svg",
    "Greece": "gr.svg",
    "Hungary": "hu.svg",
    "Iceland": "is.svg",
    "India": "in.svg",
    "Iran": "ir.svg",
    "Iraq": "iq.svg",
    "Israel": "il.svg",
    "Italy": "it.svg",
    "Japan": "jp.svg",
    "Mexico": "mx.svg",
    "Morocco": "ma.svg",
    "Netherlands": "nl.svg",
    "New Zealand": "nz.svg",
    "Nigeria": "ng.svg",
    "North Korea": "kp.svg",
    "North Macedonia": "mk.svg",
    "Norway": "no.svg",
    "Panama": "pa.svg",
    "Paraguay": "py.svg",
    "Peru": "pe.svg",
    "Poland": "pl.svg",
    "Portugal": "pt.svg",
    "Qatar": "qa.svg",
    "Republic of Ireland": "ie.svg",
    "Romania": "ro.svg",
    "Russia": "ru.svg",
    "Saudi Arabia": "sa.svg",
    "Senegal": "sn.svg",
    "Serbia": "rs.svg",
    "Serbia and Montenegro": "cs.svg",  # Comme la Yougoslavie
    "Slovakia": "sk.svg",
    "Slovenia": "si.svg",
    "South Africa": "za.svg",
    "South Korea": "kr.svg",
    "Soviet Union": "su.svg",  # Hypothétique code
    "Spain": "es.svg",
    "Sweden": "se.svg",
    "Switzerland": "ch.svg",
    "Trinidad and Tobago": "tt.svg",
    "Tunisia": "tn.svg",
    "Turkey": "tr.svg",
    "Ukraine": "ua.svg",
    "United Arab Emirates": "ae.svg",
    "United States": "us.svg",
    "Uruguay": "uy.svg",
    "Venezuela": "ve.svg",
    "Wales": "gb-wls.svg",
    "Zaire": "zr.svg",  # ou "cd.svg" (RDC actuelle)
    "Yugoslavia": "yu.svg",  # Hypothétique
}

# Création du dossier destination s’il n’existe pas
os.makedirs(DST_DIR, exist_ok=True)

# Traitement
for team, svg_file in NATIONAL_TEAMS_FLAG_MAP.items():
    src_path = os.path.join(SRC_DIR, svg_file)
    dst_path = os.path.join(DST_DIR, f"{team}.svg")
    if os.path.exists(src_path):
        shutil.copy(src_path, dst_path)
        print(f"✅ {team}: copied from {svg_file}")
    else:
        print(f"⚠️ {team}: MISSING {svg_file}")

