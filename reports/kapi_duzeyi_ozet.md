# Kapı düzeyi CSS simülasyonu — kısa özet

Bu dosya `experiments/make_report.py` tarafından sonuç dosyalarından üretilir; her sayının yanında deney kimliği vardır.

Kaynak deney: `gate_level_css-20261015T201001Z-DESKTOP-RR5J4T0-ffe8a2b77f` (durum **PASS**).

## Ne çalıştı

- **Z25, kapı düzeyi kodlayıcı (Düzen B)**: her j için referansla en kötü sadakat 1 (sapma < 10⁻¹⁵); L ve ancilla |0⟩'a döndü; sızıntı 0.
- **Z25, tam döngü (Düzen B, ortak ancilla + sıfırlama)**: 300 çalışma (tüm (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele süperpozisyon girdileri), min sadakat 1 − 2.0e-15, 21 tel.
- **Z25, tam döngü (Düzen B, ayrı ancilla kayıtları)**: 130 çalışma (örneklenen 40/125 (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele süperpozisyon girdileri), min sadakat 1 − 2.2e-15, 24 tel.
- **Z25, tam döngü (Düzen A)**: 300 çalışma (tüm (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele süperpozisyon girdileri), min sadakat 1 − 9.0e-14, 20 tel.
- **Z25, negatif kontrol**: X(e), e ∈ ε∖{0} → tüm sendromlar 0 ve ⟨ψ₀|X(e)|ψ₀⟩ = 0 (Önerme 5 karşı-örneği devrede).
- **Z25, Z(e) okuması**: 5/5 farklı sendrom; (ε−ε)∩C₁^⊥H = {0}: evet — denklik sağlanıyor.
- **Z65, kapı düzeyi kodlayıcı (Düzen B)**: her j için referansla en kötü sadakat 1 (sapma < 10⁻¹⁵); L ve ancilla |0⟩'a döndü; sızıntı 0.
- **Z65, tam döngü (Düzen B, ortak ancilla + sıfırlama)**: 130 çalışma (örneklenen 40/845 (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele süperpozisyon girdileri), min sadakat 1 − 1.8e-15, 21 tel.
- **Z65, negatif kontrol**: X(e), e ∈ ε∖{0} → tüm sendromlar 0 ve ⟨ψ₀|X(e)|ψ₀⟩ = 0 (Önerme 5 karşı-örneği devrede).
- **Z65, Z(e) okuması**: 5/5 farklı sendrom; (ε−ε)∩C₁^⊥H = {0}: evet — denklik sağlanıyor.
- **Z85, kapı düzeyi kodlayıcı (Düzen B)**: her j için referansla en kötü sadakat 1 (sapma < 10⁻¹⁵); L ve ancilla |0⟩'a döndü; sızıntı 0.
- **Z85, tam döngü (Düzen B, ortak ancilla + sıfırlama)**: 80 çalışma (örneklenen 30/425 (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele süperpozisyon girdileri), min sadakat 1 − 2.4e-15, 26 tel.
- **Z85, negatif kontrol**: X(e), e ∈ ε∖{0} → tüm sendromlar 0 ve ⟨ψ₀|X(e)|ψ₀⟩ = 0 (Önerme 5 karşı-örneği devrede).
- **Z85, Z(e) okuması**: 17/17 farklı sendrom; (ε−ε)∩C₁^⊥H = {0}: evet — denklik sağlanıyor.

## Ne çalışmadı / yapılmadı

- Tüm adımlar geçti.
- `lightning.qubit` üzerinde PennyLane-yerel MCM (tree-traversal) faz kestiriminden sonra sayısal gürültü dalında çöküyor; asıl motor kesin segmentli simülasyon, yerel MCM (`default.qubit`) ile çapraz doğrulandı.
- Düzen A için kapı düzeyi kodlayıcı yok (Möttönen ile yükleme).
- Tam döngü tüm T_X × T_Z hata çiftleri üzerinde yalnızca şu varyantlarda: Z25 3_cycle_B_reuse, Z25 3_cycle_A. Örneklemeli: Z25 3_cycle_B: 40/125; Z65 3_cycle_B_reuse: 40/845; Z85 3_cycle_B_reuse: 30/425 çift (her biri iki sırada). Z₃₂₅ tam döngü: genişlik nedeniyle yapılmadı.
- Gürültü yalnızca kod-kapasitesi modelinde (kodlanmış duruma bir kez gürültü, ardından ideal kurtarma); sendrom devresinin kendisi gürültüsüz kabul edildi (devre düzeyi / hataya dayanıklı gürültü yapılmadı).

## Gürültü (adım 6)

Deney `noise_layouts-20261016T005404Z-DESKTOP-RR5J4T0-a65fa71371` (kapı düzeyi kaynak: `gate_level_css-20261015T201001Z-DESKTOP-RR5J4T0-ffe8a2b77f`; adımlar 1–5 geçenler: Z25, Z65, Z85).

| kod | dim | K | p | **kod: birim-kayma** | kodlamasız K-qudit (birim-kayma) | kodlamasız halka qudit'i (birim-kayma) | kod: qudit depolarizasyon | kodlamasız K-qudit depol. |
|---|---|---|---|---|---|---|---|---|
| Z25 | 625 | 5 | 0.001 | 1.00e-06 | 0.002 | 0.00399 | 9.60e-04 | 0.001 |
| Z25 | 625 | 5 | 0.01 | 1.00e-04 | 0.0199 | 0.0394 | 0.0096 | 0.01 |
| Z25 | 625 | 5 | 0.1 | 0.01 | 0.19 | 0.344 | 0.096 | 0.1 |
| Z65 | 4225 | 5 | 0.001 | 0 | 0.002 | 0.00399 | 9.60e-04 | 0.001 |
| Z65 | 4225 | 5 | 0.01 | 0 | 0.0199 | 0.0394 | 0.0096 | 0.01 |
| Z65 | 4225 | 5 | 0.1 | 0 | 0.19 | 0.344 | 0.096 | 0.1 |
| Z85 | 7225 | 17 | 0.001 | 1.00e-06 | 0.002 | 0.00399 | 9.97e-04 | 0.001 |
| Z85 | 7225 | 17 | 0.01 | 1.00e-04 | 0.0199 | 0.0394 | 0.00997 | 0.01 |
| Z85 | 7225 | 17 | 0.1 | 0.01 | 0.19 | 0.344 | 0.0997 | 0.1 |

Birim-kayma modeli: her X- ve Z-koordinatı (gerçel/sanal) bağımsız olarak p olasılıkla ±1 kayar. Kodlamasız K-qudit: aynı model, bir X ve bir Z koordinatı (LER = 1 − (1−p)²). Depolarizasyonda qudit düzeyinde avantaj ihmal edilebilir düzeydedir: LER = p·(1 − (N_X·N_Z − 1)/(d² − 1)); Z25 ve Z65'te ≈ 0.96·p, Z85'te ≈ 0.997·p (kod d² Pauli'nin yalnızca N_X·N_Z tanesini düzeltir; rastgele Pauli'lerin çoğu birim kayma değildir).

Monte Carlo (p = 0.05) kesin değere karşı:

| kod | cihaz | deneme | MC LER | kesin | kesin %95 GA içinde | s |
|---|---|---|---|---|---|---|
| Z25 | cpu | 40000 | 0.002 | 0.0025 | ✗ | 0.643 |
| Z25 | cuda | 40000 | 0.002 | 0.0025 | ✗ | 0.317 |
| Z65 | cpu | 20000 | 0 | 0 | ✓ | 2.5 |
| Z65 | cuda | 20000 | 0 | 0 | ✓ | 0.233 |
| Z85 | cpu | 20000 | 0.00255 | 0.0025 | ✓ | 4.43 |
| Z85 | cuda | 20000 | 0.00255 | 0.0025 | ✓ | 0.503 |

Bu tablodaki çalıştırma durumu (PASS) yalnızca çalıştırmanın tamamlandığını gösterir; istatistiksel kontrol GA sütunu ve aşağıdaki bağımsız tohum takibidir.

Z25 satırında kesin değer %95 GA'nın hemen dışında kaldı (CPU ve GPU aynı tohumu kullandığı için tek bir örnek). Bağımsız tohumlarla takip (`mc_seed_check-20261016T011645Z-DESKTOP-RR5J4T0-08a0c41aff`): 10 tohum × 40 000 deneme, birleşik LER 0.00256 vs kesin 0.0025 (z = 0.73), kesin değer birleşik GA içinde; 10 tohumun 10'unda GA kesin değeri içeriyor → istatistiksel dalgalanma, simülatörde yanlılık yok.

**Birim-kayma desenleri ve depolarizasyon için düzeltilebilir Pauli sayıları** (`qudit_depolarizing_mc-20261016T014151Z-DESKTOP-RR5J4T0-b47fcc1ffb`):

| kod | d = \|R\| | X-desen düzeltilen | düzeltilemeyen X-kaymaları | Z-desen düzeltilen | düzeltilemeyen Z-kaymaları | N_X | N_Z |
|---|---|---|---|---|---|---|---|
| Z25 | 625 | 5/9 | (-1, -1) (-1, 1) (1, -1) (1, 1) | 9/9 | — | 125 | 125 |
| Z65 | 4225 | 9/9 | — | 9/9 | — | 845 | 845 |
| Z85 | 7225 | 5/9 | (-1, -1) (-1, 1) (1, -1) (1, 1) | 9/9 | — | 425 | 425 |

Z65'te birim-kayma LER'i tam olarak 0'dır, çünkü 9 X-kayma deseninin ve 9 Z-kayma deseninin hepsi düzeltilir. Z25 ve Z85'te Z-desenlerinin 9'u, X-desenlerinin 5'i düzeltilir; düzeltilemeyen 4 desen (±1, ±1)'dir ve her birinin olasılığı p²/4 olduğundan LER = p².

Qudit depolarizasyon Monte Carlo'su kesin değere karşı (vuruş = Pauli uygulanan deneme; koşullu test: başarısızlık \| vuruş ~ Binom(vuruş, 1 − (N_X·N_Z − 1)/(d² − 1))):

| kod | p | tohum | deneme | vuruş | başarısız | MC LER | %95 GA | kesin | GA içinde | koşullu p-değeri | cihaz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Z25 | 0.05 | 1548870650 | 40000 | 2049 | 1965 | 0.0491 | [0.047, 0.0513] | 0.048 | ✓ | 0.821 | cuda |
| Z25 | 0.2 | 654150503 | 40000 | 8011 | 7683 | 0.192 | [0.188, 0.196] | 0.192 | ✓ | 0.648 | cuda |
| Z65 | 0.05 | 1337111886 | 40000 | 2019 | 1935 | 0.0484 | [0.0463, 0.0505] | 0.048 | ✓ | 0.691 | cuda |
| Z65 | 0.2 | 1416426816 | 40000 | 7993 | 7660 | 0.192 | [0.188, 0.195] | 0.192 | ✓ | 0.441 | cuda |
| Z85 | 0.05 | 1471706967 | 40000 | 2046 | 2043 | 0.0511 | [0.0489, 0.0533] | 0.0498 | ✓ | 0.181 | cuda |
| Z85 | 0.2 | 2974996551 | 40000 | 7972 | 7947 | 0.199 | [0.195, 0.203] | 0.199 | ✓ | 0.703 | cuda |

Geçme ölçütü: her satırda koşullu binom p-değeri > 0.05 / satır sayısı (Bonferroni); aksi halde çalıştırma FAIL olarak işaretlenir. Koşulsuz %95 GA sütunu raporlanır ama ölçüt değildir (6 satırda en az bir GA ıskası ~%26 olasılıkla beklenir). Ölçüt ikinci çalıştırmanın verisi incelendikten sonra eklendi; en küçük koşullu p-değeri 0.18 olduğundan karar bu seçime duyarlı değildir. Bu çalıştırmada eşik 0.00833, en küçük koşullu p-değeri 0.181, durum **PASS**.

Depolarizasyon Monte Carlo'su (her (kod, p) için bağımsız tohum) kesin formülle uyumludur. İlk çalıştırma tüm kodlar için aynı tohumu kullanmıştı; p = 0.2'de üç kodun ortak vuruş sayısı beklenenden ~2σ fazlaydı ve Z25 ile Z65'te kesin değer %95 GA'nın hemen dışında kaldı. Bu tek bir ortak dalgalanmadır, simülatör hatası değildir; o çalıştırma silinmedi. İlk çalıştırma: `qudit_depolarizing_mc-20261016T012657Z-DESKTOP-RR5J4T0-0f77349380` (2/6 satırda kesin değer GA dışında; o sırada geçme ölçütü yoktu ve durum PASS olarak yazıldı).

| kanal | p | ring layout A (10 q) | ring layout B (12 q) | no QEC minimal (3 q) | no QEC same register A (10 q, strict) | no QEC same register B (12 q, strict) | no QEC layout B, label digit only (12 q) | [[5,1,3]] x 3 (15 q) |
|---|---|---|---|---|---|---|---|---|
| bit_flip | 0.001 | 0.00904 | 0.00797 | 0.003 | 0.00996 | 0.0119 | 0.003 | 2.77e-05 |
| bit_flip | 0.01 | 0.087 | 0.0771 | 0.0297 | 0.0956 | 0.114 | 0.0297 | 0.00272 |
| bit_flip | 0.1 | 0.606 | 0.56 | 0.271 | 0.651 | 0.718 | 0.271 | 0.21 |
| phase_flip | 0.001 | 0.0088 | 0.00689 | 0.00256 | 0.00892 | 0.00256 | 0.00256 | 2.99e-05 |
| phase_flip | 0.01 | 0.0842 | 0.0666 | 0.0254 | 0.0853 | 0.0254 | 0.0254 | 0.00294 |
| phase_flip | 0.1 | 0.552 | 0.481 | 0.234 | 0.558 | 0.234 | 0.234 | 0.225 |
| depolarizing | 0.001 | 0.00896 | 0.00839 | 0.00285 | 0.00961 | 0.00882 | 0.00285 | 2.85e-05 |
| depolarizing | 0.01 | 0.0863 | 0.0809 | 0.0283 | 0.0924 | 0.085 | 0.0283 | 0.00279 |
| depolarizing | 0.1 | 0.6 | 0.574 | 0.259 | 0.633 | 0.602 | 0.259 | 0.21 |
| amplitude_damping | 0.001 | 0.00385 | 0.00209 | 1.00e-03 | 0.00399 | 1.00e-03 | 1.00e-03 | 7.22e-06 |
| amplitude_damping | 0.01 | 0.038 | 0.0207 | 0.00999 | 0.0393 | 0.00999 | 0.00999 | 7.16e-04 |
| amplitude_damping | 0.1 | 0.329 | 0.194 | 0.099 | 0.335 | 0.099 | 0.099 | 0.0645 |
| phase_damping | 0.001 | 0.00221 | 0.00173 | 6.40e-04 | 0.00224 | 6.40e-04 | 6.40e-04 | 1.87e-06 |
| phase_damping | 0.01 | 0.0219 | 0.0172 | 0.0064 | 0.0222 | 0.0064 | 0.0064 | 1.87e-04 |
| phase_damping | 0.1 | 0.2 | 0.161 | 0.0642 | 0.203 | 0.0642 | 0.0642 | 0.0186 |

Düzen B (12 kubit) GPU'da complex64 ile hesaplandı; p = 0.01'de CPU complex128 ile en büyük fark 1.47e-07.

**Sızıntı, Düzen A ve Düzen B** (aynı çalıştırma, `qubit_level.csv`):

| kanal | p | sızıntı: ring layout A (10 q) | sızıntı: ring layout B (12 q) | LER: ring layout A (10 q) | LER: ring layout B (12 q) |
|---|---|---|---|---|---|
| bit_flip | 0.001 | 0.00136 | 0.003 | 0.00904 | 0.00797 |
| bit_flip | 0.01 | 0.0134 | 0.0297 | 0.087 | 0.0771 |
| bit_flip | 0.1 | 0.12 | 0.271 | 0.606 | 0.56 |
| phase_flip | 0.001 | 0 | 0 | 0.0088 | 0.00689 |
| phase_flip | 0.01 | 0 | 0 | 0.0842 | 0.0666 |
| phase_flip | 0.1 | 0 | 0 | 0.552 | 0.481 |
| depolarizing | 0.001 | 9.06e-04 | 0.002 | 0.00896 | 0.00839 |
| depolarizing | 0.01 | 0.00899 | 0.0199 | 0.0863 | 0.0809 |
| depolarizing | 0.1 | 0.0834 | 0.187 | 0.6 | 0.574 |
| amplitude_damping | 0.001 | 0 | 0 | 0.00385 | 0.00209 |
| amplitude_damping | 0.01 | 0 | 0 | 0.038 | 0.0207 |
| amplitude_damping | 0.1 | 0 | 0 | 0.329 | 0.194 |
| phase_damping | 0.001 | 0 | 0 | 0.00221 | 0.00173 |
| phase_damping | 0.01 | 0 | 0 | 0.0219 | 0.0172 |
| phase_damping | 0.1 | 0 | 0 | 0.2 | 0.161 |

Sızıntı = gürültüden sonra, temel girdiler üzerinden ortalama, geçerli halka-elemanı seviyelerinin dışındaki popülasyon (kurtarma bunu kaybeder). Gürültüsüz devrede sızıntı yoktur: Düzen B kodlayıcısının sızıntısı 0'dır (adım 2) ve tam döngülerde min F ≥ 1 − 10⁻¹² olduğundan döngü sonundaki sızıntı ≤ 1 − F. Gürültülü sızıntı kanaldan gelir; Düzen B'de geçerli seviye oranı daha düşüktür (A: (25/32)² ≈ 0.61, B: (5/8)⁴ ≈ 0.15).

Kodlamasız referanslar: *minimal* = 5 seviye 3 kubitte; *aynı kayıt (strict)* = lojik j, kodun kaydında tek taban durumu |t_j⟩ olarak saklanır ve kayıttaki her değişiklik hata sayılır; *etiket rakamı* = Düzen B kaydında yalnızca etiket rakamı okunur (diğer kubitler boşta) — bu, minimal referansla aynı sonucu verir (beklenen; doğrulama). Deney `noise_layouts-20261016T005404Z-DESKTOP-RR5J4T0-a65fa71371`, süre 22 dk.

## Notlar

- Karakter χ kodda tek yerde (`GaussianRing.trace_convention`); alternatif Tr = 2a ile aynı kapı düzeyi döngü de geçti (`gate_level_css_2re-*`, teknik rapor Bölüm 5.7).
- Devre operatörleri yoğun matris olarak kurulmadı (yalnızca ≤ 625 boyutlu bağımsız kontroller ve rakam başına küçük QubitUnitary blokları). **İstisna**: adım 6'daki kubit düzeyi gürültü, kesin değerlendirme için tam kaydın yoğunluk matrisiyle (Düzen A: 1024, Düzen B: 4096 boyut) hesaplandı — bu bir operatör değil durum gösterimidir.
- Düzen B devre şemaları: `figures/circuits/splitB_*.png`; ayrıntılar: teknik rapor Bölüm 8.6.
