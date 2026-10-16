# Çalışma Özeti — ε-Kuantum Hata Düzeltme Kodları (R_Q) Yeniden Üretimi

**Tarih:** 15 Ekim 2026 · **Makine:** DESKTOP-RR5J4T0 (RTX 5060 Ti 16 GB, Ryzen 7 7700X, 63 GB RAM; Windows 10 + WSL2 Ubuntu)
**İncelenen makale:** Güzeltepe & Aytaç, *ε-Quantum error correction codes over the ring R_Q*, FFA 117 (2027) 102881

Bu dosya ne yaptığımızı ve ne bulduğumuzu tek sayfada anlatır. Tüm ayrıntı, sayılar ve kanıtlar:
**[reports/teknik_rapor.md](reports/teknik_rapor.md)** (13 bölüm + 3 ek; Ek C: inceleme sonrası değişen ifadeler).
Kapı düzeyi simülasyonun kısa özeti: **[reports/kapi_duzeyi_ozet.md](reports/kapi_duzeyi_ozet.md)**.

---

## 1. Ne yaptık? (adım adım)

| Faz | Ne yapıldı | Sonuç |
|---|---|---|
| **0 — Envanter** | Klasörde 2 dosya bulundu: makale PDF'i + `epsilon codes.py`. İkisi de değiştirilmeden `original_source/` altına kopyalandı (SHA-256 kayıtlı). Ortam kuruldu (Python 3.12, PennyLane 0.45.1, torch 2.11 CUDA 12.8). | ✅ |
| **1 — Orijinal kod** | Yazarların kodu olduğu gibi çalıştırıldı; makaledeki örnekler onların koduyla test edildi. | ✅ Örnek 8: y = 11+8i → **e = 8+4i, c = 3+4i** doğru |
| **2 — Bağımsız cebir** | Z_q[i] halkaları, idealler, Hermitian dual, koset ayrışımı ve decoder sıfırdan yazıldı; her şey eleman eleman sayılarak (exhaustive) doğrulandı. | ✅ \|C1\|, \|C2\|, K değerlerinin hepsi doğru |
| **3 — AWGN (Şekil 1–3)** | Makaledeki SER grafikleri GPU'da yeniden simüle edildi; makale figürleriyle yan yana kondu. | ⚠️ Eğriler yeniden üretildi, ama "kodlama kazancı" yorumu yanlış |
| **4 — Pauli/stabilizer** | Genelleştirilmiş X(u), Z(v) operatörleri ve Teorem 4'ün stabilizer kodu 105 625 boyuta kadar matris kurmadan doğrulandı. | ✅ Kod boyutu K doğru |
| **5 — Önerme 5 + devreler** | Makalenin "farklı hatalar farklı sendrom verir" iddiası test edildi; PennyLane'de gerçek kuantum devreleri kuruldu (Windows CPU + WSL2 GPU). | ❌ **Önerme 5, makalenin X-tipi okumasında yanlış**; Z-tipi okumada koşullu ((ε−ε) ∩ C₁^⊥H = {0}), genel değil |
| **6 — Gürültü** | Bit-flip, faz-flip, depolarizasyon, genlik ve faz sönümü altında halka kodu standart kodlarla karşılaştırıldı. | ⚠️ İkili kubit gömmesinde (10/12 kubit) kodlamasızdan kötü — gömmeye özgü, karşılaştırma kaynak bakımından adil değil; kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde belirgin şekilde iyi (Z₂₅, p = 0.01: LER 1.0×10⁻⁴, kodlamasız K = 5 qudit 1.99×10⁻²) |
| **7 — Üç makine** | Senin kararınla iptal edildi; her şey bu makinede yapıldı. | — |
| **8 — Rapor + testler** | Türkçe teknik rapor, 149 otomatik test (135 PASS, 14 FAIL), tek komutla tekrar çalıştırma (`run_all.py`). | ✅ |

---

## 2. En önemli bulgular

1. **Makalenin cebirsel kısmı doğru.** Halka hesapları, ideal boyutları, koset decoder ve Teorem 4'teki stabilizer kodu sayısal olarak doğrulandı.
2. **Önerme 5 (makalenin kuantum iddiası) X-tipi okumada yanlış.** Makalenin hata modelinde (X(e), e ∈ ε ⊂ C2) bütün hatalar **sıfır sendrom** üretiyor. Bunlar tespit edilemeyen **lojik hatalar**: kodlanmış bilgiyi bozuyorlar ama ölçümde görünmüyorlar. *Makalenin seçtiği bu hata kümesi için* hiçbir kurtarma işlemi yoktur (Knill–Laflamme koşulu ihlal ediliyor); aynı stabilizer doğru hata kümesiyle düzeltme yapıyor. Z-tipi okumada (hatalar Z(e)) önerme, (ε−ε) ∩ C₁^⊥H = {0} koşulu altında doğru — makalenin üç örneğinde sağlanıyor, genel değil: makalenin kendi ayarında bile karşı-örnek var (Z₂₅[i], C₁ = ⟨10−5i⟩ ⊂ C₂ = ⟨2−i⟩: 25 temsilci, 1 farklı sendrom); C₁^⊥H ⊆ C₁ yeterli koşul. Beş kodda sayısal olarak, PennyLane devrelerinde de (29 kubite kadar) gösterildi.
3. **Tanım 6'daki dual hatalı.** Doğrusu C^⊥H = Ann(σ(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (beş halkadaki tüm ideallerde doğrulandı); Tanım 6 yalnızca Ann(α) = ⟨α⟩ iken doğru (ör. Z₂₅'te ⟨5⟩), makale örneklerinin hiçbir üretecinde değil. Örnek 6–7'deki basılı koşul (z·σ(α₂) ≡ 0) doğru. Lemma 1 hiçbir tek tanımla tutarlı değil (doğru dual ile (1) yanlış, (2)–(3) doğru). Tablo 1–2'deki Z₉ satırı hatalı (Z₉ zaten makalenin hipotezi dışında: 3 ≡ 3 mod 4).
4. **AWGN "kodlama kazancı" farklı iletim hızlarının karşılaştırılmasından geliyor.** Aynı hızdaki 128-QAM ile kıyaslanınca makalenin kodlu sistemi **2.5–2.9 dB daha kötü**.
5. **Yazarların kodunda bir hata var** (`hermitian_dual` iki kez uygulanınca yanlış sonuç). Düzeltilmiş sürüm ayrı tutuldu; makale sonuçlarını **etkilemediği ölçüldü**.
6. **Fiziksel kuantum hata düzeltme:** Makalenin X(ε) hata kümesiyle mümkün değil. Aynı stabilizer, doğru seçilmiş hata kümesiyle (ayrı etiketli alternatif tasarım) kapı düzeyinde çalışıyor: kodlayıcı + sıralı sendrom ölçümü + kurtarma ile sadakat 1.0 (Z₂₅ için tüm 125 hata çifti, iki ölçüm sırası). Gürültü altında: ikili kubit gömmesinde kodlamasızdan kötü — ama bu gömmeye özgü (bit-flip'lerin çoğu halkada büyük bir sıçrama, kod ise birim kaymalara göre tasarlanmış) ve 10/12 kubitle 3 kubiti karşılaştırmak kaynak bakımından adil değil; aynı kayıtla kodlamasız referans da raporlandı. Kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde Z₂₅ kodu p = 0.01'de LER = 1.0×10⁻⁴ (kodlamasız: 1.99×10⁻²).

---

## 3. GPU ve WSL

- Windows'ta PennyLane'in GPU cihazı (`lightning.gpu`) kurulamıyor; **WSL2 Ubuntu'ya kurduk** ve doğruladık.
- GPU, CPU'ya göre büyük devrelerde **~13–14× hızlı** (tek hassasiyette ~25×). Örnek: 24 kubitlik devre 46 s → 3.3 s.
- Windows'ta çalıştıramadığımız devreler GPU'da çalıştı: Z₃₂₅ X-sendromu (29 kubit, 8/8 doğru) ve Z₈₅ tam hata düzeltme döngüsü (26 kubit, sadakat 1.0).
- Diğer GPU işleri (AWGN, yoğunluk matrisi, Monte Carlo) PyTorch ile: 8–26× hızlanma.

---

## 4. Devre şemaları (PennyLane, Z₂₅[i])

Aşağıdaki şemalar Phase 5'te gerçekten simüle edilen devrelerin kendisidir (`experiments/draw_circuits.py`).
Tel adları: **re0–re4** = x = a + bi'nin gerçel kısmı a (re0 en anlamlı bit), **im0–im4** = sanal kısım b,
**sZ** = Z-sendrom ancilla'sı (mod 5), **sX** = X-sendrom ancilla'sı (Z₂₅ Fourier kaydı), **w0, w1** = `qml.Adder` yardımcı kubitleri.

**Bir hata düzeltme turunun genel yapısı:**

![Bir QEC turunun blok şeması](figures/circuits/qec_cycle_block.png)

**X(u) kapısı** — halka elemanı ekleme = gerçel ve sanal kayıtlara iki modüler toplama (mod 25):

![X(3+4i) kapısı](figures/circuits/gate_X_3p4i.png)

Tek bir `qml.Adder`'ın içi — QFT tabanlı modüler toplayıcı: önce kavramsal üç blok, sonra kapı düzeyine yakın açılım
(tam açıldığında tek bir Adder 178 temel kapıdır; bir sendrom turunda bunlardan onlarca vardır):

![Adder açılımı: QFT, PhaseAdder, QFT†](figures/circuits/gate_X_adder_decomposed.png)

![Adder kapı düzeyi açılımı](figures/circuits/gate_X_adder_gatelevel.png)

**Z(v) kapısı** — yalnızca tek-kubit faz kapıları (yoğun matris yok):

![Z(10+5i) kapısı](figures/circuits/gate_Z_10p5i.png)

**Z-tipi sendrom çıkarımı** — her veri biti, sendrom ancilla'sına kontrollü bir modüler toplama yapar:

![Z-tipi sendrom](figures/circuits/syndrome_Z.png)

**X-tipi sendrom çıkarımı** — faz kestirimi (U = 25 boyutlu Fourier dönüşümü, yalnızca ancilla üzerinde):

![X-tipi sendrom](figures/circuits/syndrome_X.png)

**Önerme 5 karşı-örneği** — lojik durum hazırlanır, ε'nin bir elemanı X(2+i) uygulanır, sendrom ölçülür:
ölçüm **olasılık 1 ile 000** verir (hata görünmez), oysa veri artık farklı bir lojik durumdur.

![Önerme 5 karşı-örneği](figures/circuits/prop5_counterexample.png)

---

## 5. Önemli grafikler

**Şekil 3 — makale (solda) ve bizim yeniden kurulumumuz (sağda).** Turuncu eğri, aynı hızdaki (7 bit) kodsuz
128-QAM: makalenin "kodlu" sisteminden (mavi) belirgin şekilde daha iyi.

![Şekil 3 karşılaştırması](figures/awgn_fig3_side_by_side.png)

**Gürültü altında halka kodu (mavi) ve diğer kodlar (ikili kubit gömmesi, Düzen A)** — bu gömmede her kanalda halka kodu
kodlamasızdan (gri) kötü, [[5,1,3]] (yeşil) en iyisi. Bu sonuç ikili gömmeye özgüdür; qudit düzeyi birim-kayma gürültüsünde
sıralama terstir (bkz. bulgu 6, teknik rapor Bölüm 9):

![Gürültü karşılaştırması](figures/noise_qubit_level_LER.png)

---

## 6. Yapılamayanlar

- **Z₃₂₅ tam hata düzeltme döngüsü:** 36 kubit gerekiyor, 16 GB karta sığmıyor (orta-devre ölçüm + sıfırlamayla 29 kubite iner, denenmedi).
- **Z₈₅/Z₃₂₅ için kubit düzeyinde gürültü:** Yoğunluk matrisleri çok büyük.
- **Kapı düzeyinde kodlayıcı (Düzen A):** Yok; Düzen A'da lojik durumlar genel durum hazırlamayla yüklendi. Düzen B'de (split koordinatlar) kapı düzeyi kodlayıcı var ve doğrulandı.
- **Makale grafiklerinin birebir aynısı:** Yazarların simülasyon kodu ve parametreleri yayımlanmadığı için mümkün değil; hepsi bağımsız yeniden kurulum.

---

## 7. Dosyalar nerede?

| Ne | Nerede |
|---|---|
| Teknik rapor (tam) | `reports/teknik_rapor.md` |
| Bu özet | `CALISMA_OZETI.md` |
| PDF sürümleri | `reports/CALISMA_OZETI.pdf`, `reports/teknik_rapor.pdf` |
| Devre şemaları (PNG) | `figures/circuits/` (`experiments/draw_circuits.py` ile yeniden çizilir) |
| Grafikler (makale figürleriyle yan yana dahil) | `figures/` |
| Tüm deney sonuçları (CSV, JSON, ortam bilgisi) | `results/<kategori>/<deney-kimliği>/` |
| Test sonuçları (PASS/FAIL listesi) | `results/tests/test_report.json` |
| Yazarların orijinal kodu (dokunulmadı) | `original_source/` |
| Hatası düzeltilmiş kopya + fark dosyası | `original_source_fixed/` |
| Kaynak kod | `src/epsqec/` |
| Deney betikleri / ayarlar | `experiments/`, `configs/` |
| WSL GPU kurulumu | `wsl/setup_wsl_gpu.sh` |

## 8. Tekrar çalıştırmak

```powershell
cd C:\Users\bedrhan94\Desktop\PennyLane\epsilon_qec_research
.venv\Scripts\python.exe run_all.py --list            # tüm adımları göster
.venv\Scripts\python.exe run_all.py                   # Windows tarafını baştan sona çalıştır
.venv\Scripts\python.exe run_all.py --phases W        # WSL2 GPU devreleri
.venv\Scripts\python.exe experiments\make_report.py   # raporu sonuçlardan yeniden üret
```

**Testler:** 135 PASS, 14 FAIL (matematiksel iddia testleri 33 PASS / 13 FAIL; uygulama testleri 102 PASS / 1 FAIL). 13 matematiksel FAIL: 5'i makalenin sağlanmayan iddiaları, 6'sı makalenin birbiriyle çelişen dual tanımları (Tanım 6), 2'si makalenin kendi hipotezi dışındaki Z₉ tablo satırı. 1 uygulama FAIL'i yazarların kodundaki hatadan. Bizim kodumuzun testlerinin hepsi geçiyor.
