# SNOCKS Meta Ads – Naming Convention

Ad-Namen folgen einer strukturierten Naming Convention mit `_` als Trennzeichen. Die ersten 7 Felder sind bei allen Ads identisch. Ab Position 8 variiert das Schema je nach `Creative Source`.

---

## Pflichtfelder (Positionen 1–7)

```
{Product}_{CreativeID}_{ContentType}_{AdType}_{CreativeCluster}_{In/Ex}_{CreativeSource}
```

| # | Feld | Werte |
|---|------|-------|
| 1 | **Product** | `Socken`, `Leggings`, `Ankle`, `ShapePanty`, `Boxer` |
| 2 | **Creative ID** | `CR042`, `CR2466`, `CR5243` |
| 3 | **Content Type** | `Video`, `Image` |
| 4 | **Ad Type** | `LinkAd` |
| 5 | **Creative Cluster** | `VoiceOver`, `Head`, `Testimonial`, `Product`, `UGC` |
| 6 | **In/Exclusion** | `in` (Inclusion), `ex` (Exclusion) |
| 7 | **Creative Source** | Bestimmt das Schema – siehe unten |

---

## PL / EG / SP

Position 8 beginnt immer mit einem dieser drei Kürzel:

| Kürzel | Bedeutung | Beispiel |
|--------|-----------|---------|
| `PL` | Product Launch | `PL-AS001-Petrol` |
| `EG` | Evergreen | `EG` |
| `SP` | Special | `SP` |

Bei Schema 2 (CreativeTeam) kann das PL-Feld zusätzlich eine **Farbe** enthalten:
`PL-{Placement}-{Farbe}` → z.B. `PL-AS001-Petrol` → Farbe: `Petrol`

---

## Schema 2 – CreativeTeam (aktiv)

> Dies ist das aktuell verwendete Schema. Nur CreativeTeam-Ads werden in die Datenbank synchronisiert.

**Creative Source:** `CreativeTeam`, `MT`, `SM`, `DCO`, `TeamPaid`, `MIT`, `M28`, `Other`, `addictive`, `stronger`

| # | Feld | Beschreibung |
|---|------|-------------|
| 8 | **PL/EG/SP** | `PL-`, `EG` oder `SP` – kann Farbe via `-` enthalten |
| 9 | **Test IDs** | A/B-Test Kennzeichnung |
| 10 | **Visual CT** | Visual-Kürzel der Agentur |
| 11 | **Creator Cluster** | Kürzel für die Creator-Kategorie |
| 12 | **Gender** | `M` (Male), `F` (Female), `D` (Diverse), `U` (Unisex) |
| 13 | **Text Edit** | Text-Edit Kürzel |
| 14 | **Text Align** | Text-Ausrichtung Kürzel |
| 15 | **Image Type** | Bildtyp-Kürzel *(nur Image)* |
| 16 | **Copy Cluster** | Copy-Kategorie |
| 17 | **Element** | Element-Kürzel |
| 18 | **Launch Year+Week** | z.B. `2024W12` |
| 19 | **Original Creative ID** | Referenz auf das Original-Creative |
| 20 | **Additional Infos** | Zusatzinformationen |
| 21 | **Zusatzfeld** | Weiteres optionales Feld |
| 22 | **Free Text** | Freitext |
| 23 | **Ad Group Number** | Nummer der Ad Group |

**Beispiel:**
```
Ankle_CR2130_Image_LinkAd_Head_in_CreativeTeam_PL-AS001-Petrol
  │     │      │      │     │   │      │         │        │
Produkt  ID  Content  Ad  Cluster In/Ex Source   PL    Farbe(Petrol)
```

---

## Schema 1 – Interne Creatives (nicht aktiv)

**Creative Source:** `Katrin`, `Claudio`, `Katrin+Claudio`, `CFC`, `CFK`, `CFS`, `CFZ`, `CFP`, `IN`, `CFF`, `CFN`

| # | Feld | Beschreibung |
|---|------|-------------|
| 8 | **PL/EG/SP** | `PL-`, `EG` oder `SP` Kürzel |
| 9 | **Color** | Farbvariante |
| 10 | **Element** | Element-Kürzel |
| 11 | **CR-Kürzel** | Creative-Kürzel |
| 12 | **Creative Tag** | Tag für das Creative |
| 13 | **Format** | `FormatVideo` oder `FormatFoto` |
| 14 | **Hook** | Hook-Kürzel *(nur Video)* |
| 15 | **Text** | Text-Kürzel *(nur Video)* |
| 16 | **Visual** | Visual-Kürzel *(nur Video)* |
| 17 | **Angle** | Winkel / Perspektive |
| 18 | **Gender** | `M`, `F`, `D`, `U` |
| 19 | **Test IDs** | A/B-Test Kennzeichnung |
| 20 | **Launch Year+Week** | z.B. `2024W12` |
| 21 | **Original Creative ID** | Referenz auf das Original-Creative |
| 22 | **Additional Infos** | Zusatzinformationen |
| 23 | **Free Text** | Freitext |
| – | **AI** | Flag `AI` kann an beliebiger Stelle stehen |
| 24 | **Ad Group Number** | Nummer der Ad Group |

---

## Schema 3 – Fallback (nicht aktiv)

Für alle Creative Sources, die weder Schema 1 noch Schema 2 zugeordnet werden können. Es werden nur PL/EG/SP und Test IDs extrahiert, der Rest landet in `raw_suffix`.

---

## AI-Flag

Das Kürzel `AI` kann an **beliebiger Position** im Ad-Namen stehen und wird positionsunabhängig erkannt. Es setzt das Datenbankfeld `is_ai = true`.

---

## Datenbankfelder (Supabase)

Die geparsten Felder landen in der Tabelle `parsed_ad_dimensions`. Join mit Performance-Daten über `ad_name_raw`:

```sql
SELECT d.*, m.spend, m.revenue, m.roas, m.first_date, m.last_date
FROM parsed_ad_dimensions d
JOIN creative_metrics m ON d.ad_name_raw = m.ad_name_raw
```
