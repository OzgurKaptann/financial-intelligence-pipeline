# 24 - İlk Hafta Uygulama Planı

## Amaç

İlk hafta sonunda çalışan bir iskelet görmek istiyoruz. Hedef, projeyi mükemmelleştirmek değil; pipeline'ın omurgasını ayağa kaldırmak.

## Gün 1: Repo ve Dokümantasyon

Yapılacaklar:

- Repo oluştur.
- README.md ekle.
- CLAUDE.md ekle.
- Klasör yapısını oluştur.
- Docs dosyalarını ekle.

Çıktı:

- Temiz GitHub başlangıcı.

## Gün 2: Synthetic Data

Yapılacaklar:

- 3 şirket belirle.
- 2 dönem belirle.
- 8 finansal metrik için synthetic veri üret.
- CSV oluştur.

Çıktı:

```text
data/synthetic/synthetic_financial_metrics.csv
```

## Gün 3: SQLite Schema

Yapılacaklar:

- dim_company
- dim_period
- dim_metric
- fact_document_source
- fact_financial_metric
- fact_risk_keyword

Çıktı:

```text
sql/01_schema.sql
```

## Gün 4: Data Loader

Yapılacaklar:

- CSV oku.
- Required columns validate et.
- SQLite database oluştur.
- Dimension ve fact tablolarına yükle.

Çıktı:

```text
data/final/financial_intelligence.sqlite
```

## Gün 5: KPI SQL

Yapılacaklar:

- Pivot model oluştur.
- Revenue growth hesapla.
- Margin metriklerini hesapla.
- Debt/cash oranlarını hesapla.

Çıktı:

```text
sql/03_financial_kpis.sql
```

## Gün 6: Mart Table ve Export

Yapılacaklar:

- mart_company_financial_performance oluştur.
- CSV olarak export et.

Çıktı:

```text
data/final/mart_company_financial_performance.csv
```

## Gün 7: Validation + Executive Summary

Yapılacaklar:

- validation.py yaz.
- validation_report.md üret.
- executive_summary.md üret.

Çıktı:

```text
reports/validation_report.md
reports/executive_summary.md
```

## İlk Hafta Sonu Kontrol Soruları

- Veri nereden geliyor?
- Her şirket/dönem için 8 metrik var mı?
- SQL modeli çalışıyor mu?
- Final mart tablo dashboard'a hazır mı?
- Validation report anlamlı mı?
- Executive summary gerçekten metriklere dayanıyor mu?

## Disiplin Notu

İlk hafta PDF extraction, OCR, AI agent, cloud, dbt, Docker gibi şeylere girme. Bunlar seni iyi göstermez; çalışan omurgayı geciktirir.

Önce çalışan basit sistem. Sonra güçlendirme.
