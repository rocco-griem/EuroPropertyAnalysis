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

## Decision (confirmed 2026-07-10, revised 2026-07-11 after actual fetching)

**9 of the original 10 target capitals are included in V1: London, Paris, Berlin, Madrid,
Amsterdam, Vienna, Warsaw, Prague, Budapest.**

- **Madrid** is included via **Tinsa IMIE Local Markets**. Unlike every other city here, this is a
  **private, appraisal-based series**, not an official transaction-based statistic — flagged via
  `City.data_quality_note` and surfaced in the dashboard (see M7a).
- **Lisbon is excluded.** Actually fetching its data revealed the problem was worse than the
  initial "unconfirmed depth" flag suggested: INE Portugal's municipal breakout is fragmented
  across at least three incompatible methodology vintages with real gaps between them —
  "Methodology 2018" (Q1 2016 – Q3 2021), "Methodology 2022" (Q4 2019 – Q4 2023), and a further
  methodology continuing into 2024–2025 under yet another indicator code. INE's own published
  reports show only snapshot medians (charts), not a downloadable reconciled long series. There is
  no clean 2015–2024 series without splicing three incompatible vintages together — a worse
  asymmetry than Madrid's single, if private, consistent series. Confirmed with the user
  (2026-07-11): exclude rather than splice or truncate.
- **Berlin and Prague** required manual Excel downloads (vdp Research quarterly press-release
  file; ČSÚ quarterly release attachment) rather than a clean bulk API, but both had complete,
  single-methodology 2015–2024 coverage once located — see the fetch notes below.

## Fetched city-level data (committed to `data/raw/city_property_index.csv`)

Long format (`city, year, index_value`), 2015–2024, 9 cities × 10 years (90 rows), fetched
2026-07-11. Annual figures are the average of that year's quarterly (or monthly, for London)
values from each source below. Levels are in each source's native unit/base year — irrelevant,
since the pipeline rebases every series to 100 at the start year itself.

| City | Actual source used | Endpoint / file |
|---|---|---|
| London | Land Registry UK HPI, `region=london`, monthly `housePriceIndex`, averaged to annual | `landregistry.data.gov.uk/data/ukhpi/region/london/month/{YYYY-MM}.json` |
| Paris | INSEE series `010567013` (Paris apartments, Notaires-INSEE, base 2015=100) via INSEE's SDMX API (no auth needed) | `api.insee.fr/series/BDM/V1/data/SERIES_BDM/010567013` |
| Amsterdam | CBS table `85792NED`, region `GM0363` (Amsterdam municipality), `PrijsindexVerkoopprijzen_1` | `opendata.cbs.nl/ODataApi/odata/85792NED/TypedDataSet?$filter=RegioS eq 'GM0363'` |
| Vienna | OeNB isaweb report 6.6, CSV export, "Real estate price index, Vienna, 2000=100" — requires a session GET then a POST with a `zeitElementeList[0].vonJahrSelected`/`bisJahrSelected` year range to the `downloadResult` endpoint (the default view only shows the last ~3 years) | `oenb.at/isawebstat/stabfrage/downloadResult?lang=EN&exportTyp=CSV&report=6.6` |
| Budapest | MNB's actual house-price-index workbook (distinct from a similarly-named housing-wealth workbook found first) — sheet `1.1`, Budapest column, quarterly since 1990 | `statisztika.mnb.hu/timeseries/MNB_lakasarindex_2025Q2.xlsx` |
| Warsaw | NBP `ceny_mieszkan.xlsx`, sheet "Rynek wtórny" (secondary/existing-stock market), "Ceny transakcyjne" (transaction prices, not offer prices) section, Warszawa column | `static.nbp.pl/dane/rynek-nieruchomosci/ceny_mieszkan.xlsx` |
| Berlin | vdp Research's free full-history regional workbook (not the paid product — a link buried on the vdp property-price-index page, not discoverable by URL-guessing), sheet "Berlin", annual (`JD`) rows, "Owner Occupied Housing" total index | `pfandbrief.de/wp-content/uploads/.../vdp_Immobilienpreisindex_Regional_QI2003-QI2026-1.xlsx` |
| Prague | ČSÚ's quarterly release attachment (linked from the product page, not a stable URL — refetch by finding the current release's attachment links), "Indices of Realized Prices of Second-hand Flats", Praha column, base 2010=100 | `csu.gov.cz/docs/107508/.../01400725q1s.xlsx` (path changes per release) |
| Madrid | Tinsa's own public price-history page embeds the full quarterly series (2001–present) directly in the page's JS chart config — no PDF-by-PDF collection needed | `tinsa.es/en/precio-vivienda/comunidad-madrid/madrid/` (regex-extracted from `data: [...]` / `categories: [...]` in the page source) |

No missing years for any city — verified programmatically at fetch time. The one-off fetch script
used to produce this CSV was not committed (kept in scratch) since it's an acquisition tool, not
part of the reusable pipeline — M7d's `csv_loader` is the actual reusable ingestion code.

## Rental values — Deloitte Property Index (committed to `data/raw/city_rental_per_sqm.csv`)

Average monthly residential **rent in EUR/m²** per capital, long format (`city, year,
rental_eur_sqm`), 9 cities × 2016–2024 (81 rows), read 2026-07-22 from the "Average Monthly Rent
(EUR/m²)" chart in each annual **Deloitte Property Index** report. Each edition reports the prior
calendar year, so rent years 2016–2024 come from editions 2017–2025. Rent-year **2015 is not
available** — Deloitte's cross-city rent comparison chart began with the 6th edition (2017); the
rental series therefore starts in 2016 (the property index still runs from 2015).

| Rent year | Deloitte edition (PDF) | Chart label |
|---|---|---|
| 2016 | 6th ed., July 2017 | rent = the circled €/m² above each yield bar |
| 2017 | 7th ed., Sept 2018 | "Average Monthly Asking Rent per sq m in EUR, 2017" |
| 2018 | 8th ed., July 2019 | "Average Monthly Rent per sq m in EUR, 2018" |
| 2019 | 9th ed., July 2020 | "Average Monthly Rent (EUR/sqm)" |
| 2020 | 10th ed., July 2021 | "Average Monthly Rent (EUR/sqm)" |
| 2021 | 11th ed., Aug 2022 | "Average Monthly Rent (EUR/sqm)" |
| 2022 | 12th ed., Aug 2023 | "Average Monthly Rent (EUR/sqm)" |
| 2023 | 13th ed., Aug 2024 | "Average Monthly Rent (EUR/sqm), 2023" |
| 2024 | 14th ed., Aug 2025 | "Average Monthly Rent per sqm in EUR, 2024" |

Archive: `https://www.deloitte.com/cz-sk/en/Industries/real-estate/research/property-index-archive.html`

**London** is the **mean of the inner and outer London figures** where both are published; for
2018 Deloitte gave a single "London" figure (20.1), and for 2024 only "London (outer)" (23.8) was
listed, so those years use the single published value.

**Caveats (why the rental series is flagged as _indicative_):**
- Deloitte's rent methodology and chart labels shift across editions — "average monthly rent" vs.
  "average monthly **asking** rent" — and early editions note contracted-rent effects (e.g. Berlin
  reads low in 2017–2018 because long-standing contracted rents sat well below asking rents). So
  year-on-year moves in the early years, and fine cross-city gaps, are not perfectly comparable.
- Values are already in EUR in the source (Deloitte converts), so no FX layer is applied here even
  though London/Warsaw/Prague/Budapest transact in non-euro currencies.
- Unlike the property/income series, rent is stored as an **absolute €/m² level**, not a rebased
  index — it is shown as published, and "rent CAGR" is computed over the years actually present.
