# Buradan Başla

Bu dosya projenin Türkçe yön haritasıdır. GitHub vitrini için ana dokümanlar İngilizce tutulabilir; ama senin geliştirme sürecinde ne yaptığını kaybetmemen için bu dosya özellikle Türkçe yazıldı.

## Projenin Net Tanımı

Bu proje, dağınık finansal dokümanları alıp analiz edilebilir veri varlığına dönüştüren uçtan uca bir analytics engineering projesidir.

Yani sadece dashboard değil. Sadece Python notebook değil. Sadece Claude ile yazılmış kod değil.

Doğru konumlandırma şudur:

> Finansal dokümanlardan karar alınabilir analitik çıktı üreten AI destekli veri pipeline'ı.

## Senin İçin Neden Doğru Proje?

Geçmişinde finans, ERP, nakit akışı, ödeme takibi, raporlama ve operasyon var. Hedefinde SQL, Python, BI ve analytics engineering var. Bu proje iki tarafı birleştiriyor.

Bu seni sıradan CSV analizi yapan adaylardan ayırır çünkü gerçek iş problemine dokunur:

- veri temiz gelmez,
- metrik tanımı belirsizdir,
- finansal raporlarda aynı kavram farklı isimlerle geçer,
- doküman kaynaklı hatalar olur,
- yönetici teknik tablo değil karar özeti ister.

## İlk Büyük Tuzak

Projeye doğrudan PDF extraction ile başlama.

Bu hata seni boğar. Önce synthetic sample data ile pipeline'ı kur. Sistem çalışsın. Sonra gerçek dokümana geç.

Doğru sıra:

1. Repo yapısını kur.
2. Synthetic finansal veri oluştur.
3. SQLite schema kur.
4. CSV verisini SQLite'a yükle.
5. SQL ile KPI üret.
6. Dashboard-ready mart tablo oluştur.
7. Executive summary üret.
8. Validation report üret.
9. Sonra gerçek PDF/Excel entegrasyonuna geç.

## MVP Kapsamı

MVP kapsamını büyütme:

- 3 şirket
- 2 dönem
- 8 finansal metrik
- SQLite
- Python
- SQL
- 1 final mart tablo
- 1 dashboard spec
- 1 executive summary
- 1 validation report

Bundan fazlası ilk sprintte ego tuzağıdır.

## Görüşmede Anlatacağın Cümle

> Bu projede finansal verinin temiz CSV olarak gelmediği gerçekçi bir senaryoyu ele aldım. Önce doküman veya synthetic kaynaklardan metrikleri standartlaştırdım, sonra SQL ile finansal KPI modelini kurdum, en sonunda dashboard-ready mart tablo ve yönetici özeti ürettim. Odak noktam sadece görselleştirme değil, verinin kaynaktan karara kadar izlenebilir olmasıydı.

## Bitmiş Sayılma Kriteri

Bu proje şu sorulara net cevap veriyorsa bitmiştir:

- Veriyi nereden aldın?
- Hangi metrikleri çıkardın?
- Her metriğin tanımı ne?
- SQL modeli nasıl çalışıyor?
- Revenue growth nasıl hesaplandı?
- Margin metrikleri nasıl hesaplandı?
- Veri kalitesini nasıl kontrol ettin?
- Dashboard hangi karar sorularına cevap veriyor?
- Executive summary neye dayanarak üretildi?

Bu sorulara cevap veremiyorsan proje vitrinde güzel görünse bile seni görüşmede zor durumda bırakır.

## Sert Gerçek

Claude sana kod yazabilir. Ama projeyi sen anlamazsan bu repo sana değer katmaz. Bu projeyi iş görüşmesinde satacak kişi Claude değil, sensin.

O yüzden her dosyayı çalıştır, her SQL sorgusunu anla, her metriğin mantığını kendi cümlenle anlatabilecek seviyeye gel.
