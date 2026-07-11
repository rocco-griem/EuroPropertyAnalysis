# Data Sources

Researched at the M7 data-discovery milestone (2026-07-10). All 10 target capitals were
attempted; findings are documented city-by-city below before any exclusion is decided, per the
locked project rule that a national-level series is never substituted for missing city data.

Realistic committed window: **2015–2024** (2025 annual data is not yet published for almost any
of these series at time of writing).

## National-level series (used for every included city)

These three series are needed per *country*, for the capital-vs-national benchmark and for
affordability pressure. **UK is a hard break**: Eurostat's coverage for the UK stops around
2019–2020 (post-Brexit) across HPI, HICP, and labour cost data, so London uses ONS/Land Registry
for all three instead of Eurostat. The other 9 countries use Eurostat consistently, which keeps
one harmonised methodology across them.

### National House Price Index (HPI)

| Country | Source / dataset | Coverage | Access |
|---|---|---|---|
| FR, DE, ES, PT, NL, AT, PL, CZ, HU | Eurostat `prc_hpi_a` (annual, 2015=100) | 2015–2024 | REST API `.../data/prc_hpi_a?format=JSON&geo=XX`; also Data Browser CSV export |
| UK | ONS / HM Land Registry UK House Price Index | 1995–present, monthly | Bulk CSV ("UK House Price Index: data downloads"); SPARQL/API at `landregistry.data.gov.uk` |

### CPI / inflation

| Country | Source / dataset | Coverage | Access |
|---|---|---|---|
| FR, DE, ES, PT, NL, AT, PL, CZ, HU | Eurostat `prc_hicp_aind` (HICP annual index) | 1996–2024 | REST API `.../data/prc_hicp_aind?format=JSON&geo=XX&coicop=CP00&unit=INX_A_AVG` |
| UK | ONS CPI/CPIH time series | 1988/1996–present | CSV/API at `ons.gov.uk/economy/inflationandpriceindices/` |

### Income / wages

| Country | Source / dataset | Coverage | Access |
|---|---|---|---|
| **All 10 countries, including the UK** | OECD "Average annual wages" (`AV_AN_WAGE`), national currency, current prices (`PRICE_BASE=V`) — preferred over Eurostat's Labour Cost Index (includes employer contributions, not a true wage measure) | 2015–2024 confirmed for every country during actual fetching | SDMX CSV API: `sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_EARNINGS@AV_AN_WAGE,1.0/{ISO3}..........?format=csv&startPeriod=2015` |

Simplification found during sourcing (not assumed at the discovery-research stage): OECD's wage
series is independent of Eurostat's EU-aggregation, so it still reports the UK past 2020 — no need
for a separate ONS Average Weekly Earnings fetch for income specifically. HPI and CPI still need
the Eurostat/ONS split below since Eurostat's *own* HPI/CPI datasets do drop UK coverage.

All Eurostat, ONS, and OECD series above are freely redistributable in a public repo with
attribution (Eurostat copyright notice; ONS/gov.uk Open Government Licence v3; OECD terms permit
reuse with attribution) — no paywalls or registration required.

## Fetched national data (committed to `data/raw/`)

`data/raw/national_property_index.csv`, `national_inflation_index.csv`, `national_income_index.csv`
— long format (`country, year, value`), 2015–2024, 10 countries × 10 years each (100 rows), fetched
2026-07-10:

- **Property index**: Eurostat `prc_hpi_a`, `purchase=TOTAL`, `unit=I15_A_AVG` for the 9 EU
  countries; UK value is the annual average of the Land Registry UK HPI monthly `housePriceIndex`
  (`landregistry.data.gov.uk/data/ukhpi/region/united-kingdom/month/{YYYY-MM}.json`) — note the
  Land Registry index's own base year isn't 2015, which doesn't matter since the pipeline rebases
  every series to 100 at the start year itself.
- **CPI**: Eurostat `prc_hicp_aind`, `unit=INX_A_AVG`, `coicop=CP00` for the 9 EU countries; UK
  from ONS series `D7BT` (`ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23/data`).
- **Income**: OECD `AV_AN_WAGE` as above, for all 10 countries uniformly (national currency:
  EUR for the 6 Eurozone countries, PLN/CZK/HUF/GBP for Poland/Czechia/Hungary/UK).

No missing years for any country in any series — verified programmatically at fetch time.

## City-level property price index availability

| City | Country | City-level data? | Source | Coverage | Access | Confidence | Notes |
|------|---------|---|--------|----------|--------|---|-------|
| London | United Kingdom | **Yes** | ONS / HM Land Registry, UK HPI — London region | Monthly since 1995 | Bulk CSV + API | High | Repeat-sales/hedonic, all registered sold transactions |
| Paris | France | **Yes** | INSEE / Notaires-INSEE, Paris apartments series | Quarterly, long series | Free CSV/Excel ("séries chronologiques") | High | Notarial deed transaction prices, quality-adjusted |
| Amsterdam | Netherlands | **Yes** | CBS + Kadaster, "Bestaande koopwoningen" (85792NED) — Amsterdam is one of the G4 cities reported | Quarterly since 1995 | Free CSV/OData bulk | High | Repeat-sales/hedonic from full land-registry transaction register |
| Vienna | Austria | **Yes** | OeNB Residential Property Price Index — explicit Vienna vs. rest-of-Austria split | Quarterly since 1986 | Free Excel/CSV | High | Hedonic, condos (93%) + houses (7%) weighted |
| Budapest | Hungary | **Yes** | MNB House Price Index — explicit Budapest breakdown | Quarterly since 2001 | Free Excel/CSV bulk | High | Property-transfer-duty transaction data, hedonic-adjusted |
| Warsaw | Poland | **Yes** | NBP BaRN database — 17-city breakdown incl. Warsaw | Quarterly since Q3 2006 | Free bulk Excel | Medium-high | Survey-based (agent/developer reports), hedonic-adjusted |
| Berlin | Germany | **Yes, partial** | vdp Research Top-7-Cities index (Berlin reported individually); Bundesbank city indicators (bulwiengesa) as cross-check | Quarterly since ~2004–05 | Free quarterly press-release PDFs; full raw series is a **paid** vdpResearch product | Medium | Mortgage-lending transaction data, hedonic; needs manual extraction from PDFs |
| Prague | Czechia | **Yes, city = region** | ČSÚ (Czech Statistical Office) "Indexy realizovaných cen bytů" — Prague reported as its own kraj (region), which is coterminous with the city | Quarterly since 2008, base 2015=100 | Free via Public Database (VDB) | Medium | Cadastre (ČÚZK) transaction records; "city-level" only because Prague's kraj boundary = city boundary (same situation as Vienna/Berlin as city-states) |
| Lisbon | Portugal | **Yes, unconfirmed depth** | INE Portugal, "Estatísticas de Preços da Habitação ao Nível Local" — Lisboa reported | Quarterly; national series since 2009, **municipal breakout start year not yet confirmed against 2015** | Manual PDF/Excel per quarter; no single bulk file found | Medium | Tax-authority transaction data, median €/m² by municipality (not a smoothed index) — must verify historical files actually reach 2015 before committing to this source |
| Madrid | Spain | **Borderline / no** | No official *sale-price* index at city level — INE's IPV is Comunidad Autónoma-level only (INE's municipal IPVA measures *rental*, not sale, prices). Only private-sector alternative: Tinsa IMIE Local Markets, which breaks out "Madrid capital" | Quarterly since 2001 | **Manual only** (web reports), no bulk download | Medium | **Appraisal-based, not transaction-based** — a different methodology from every other city above; not an official statistic |

## Decision (confirmed 2026-07-10)

**All 10 target capitals are included in V1.**

- **Madrid** is included via **Tinsa IMIE Local Markets**. Unlike every other city here, this is a
  **private, appraisal-based series**, not an official transaction-based statistic — the dashboard
  and methodology page must flag this asymmetry explicitly (`data_quality_flag` /
  `is_proxy`-style caveat at the data-model level, plus a visible note in the UI).
- **Berlin, Prague, and Lisbon** are included despite requiring manual PDF/Excel extraction rather
  than a clean API or bulk CSV. **Lisbon's municipal breakout must be verified to actually reach
  back to 2015** before its CSV is committed — if the local series turns out to start later, it
  should be dropped (or its start year adjusted) at that point rather than assumed now.
