# ε-Kuantum Hata Düzeltme Kodları (R_Q halkası) — Bağımsız Yeniden Üretim ve Kuantum Devre Uygulanabilirliği

**Teknik rapor** · 15 Ekim 2026 · Tek makine: DESKTOP-RR5J4T0 (RTX 5060 Ti 16 GB, Ryzen 7 7700X, 63 GB RAM) —
Windows 10 + aynı makinede WSL2 Ubuntu 26.04 (yalnızca `lightning.gpu` devreleri için)

İncelenen çalışma: M. Güzeltepe, N. Aytaç, *ε-Quantum error correction codes over the ring R_Q*,
Finite Fields and Their Applications 117 (2027) 102881, doi:10.1016/j.ffa.2026.102881.

Bu rapordaki her sayı `results/` altındaki bir deney kimliğine (experiment id), bir pytest testine
(`results/tests/test_report.json`) veya açıkça yazılmış bir matematiksel gerekçeye dayanır.
Kimlikler `<ad>-<UTC zaman damgası>-<makine>-<config hash>` biçimindedir.

---

## 0. Yönetici özeti

| # | Makaledeki iddia / sonuç | Durum | Dayanak |
|---|---|---|---|
| 1 | \|C1\|, \|C2\|, K = \|C2\|/\|C1\| (Z25[i]: 25/125/5, Z85[i]: 85/1445/17, Z325[i]: 1625/8125/5) | **Doğrulandı** (eleman sayımıyla) | Phase 1, Phase 2, `test_sizes_by_enumeration_match_paper` |
| 2 | C1 ⊆ C2 ve C2^⊥H ⊆ C1 (Örnek 6–7, Tablo 1) | **Doğrulandı** — yalnızca dual *gerçek ortogonal tümleyen* olarak alındığında | Phase 2 |
| 3 | Tanım 6: C^⊥H := ⟨σ(α)⟩ | **Hatalı tanım.** Doğru dual: C^⊥H = Ann(σ(α)) = σ(Ann(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (Z[i]'de) — q ∈ {25, 65, 85, 125, 325} için tüm idealler (9/16/16/16/36) ve q başına 300 rastgele üreteçle doğrulandı. Tanım 6 yalnızca Ann(α) = ⟨α⟩ iken doğru (bu halkalarda tek durum: Z25'te ⟨5⟩); makale örneklerinin **α₂** üreteçlerinde de **α₁** üreteçlerinde de doğru değil. Tanım 6 ile örneklerdeki dual-içerme sağlanmaz ve Teorem 4 stabilizerleri komütatif olmaz (kod uzayı 0 boyutlu) | `review_checks`; `test_closed_form_*`, `test_definition6_*`; 5 `definition_consistency` testi |
| 4 | Lemma 1 (1)–(3) | Doğru dual (Ann) ile: **(1) yanlış** (α birim ⇒ C = R, C^⊥H = {0}), **(2) ve (3) doğru**. Tanım 6 ile (yazıldığı gibi): (1) doğru, (2) ve (3) yanlış → tek bir tanım altında üçü birlikte doğru değil | Phase 2 `lemma1`; 2 `paper_claim` + 1 `definition_consistency` testi |
| 5 | Tablo 1–2'deki Z9 satırı (\|C2^⊥H\| = 3, K = 1) | **Hatalı** (hesaplanan: 1 ve 3). Not: Z9 makalenin kendi hipotezinin dışındadır (3 ≡ 3 mod 4; makale de "yalnızca gösterim için" der); satır yine de kendi içinde tutarsız | 2 `paper_claim` + `outside_hypothesis` testi (sınıf güncellendi) |
| 6 | ε-decoder: Örnek 8 (y = 11+8i → e = 8+4i, c = 3+4i), Örnek 5 | **Doğrulandı** (orijinal kod + bağımsız kod) | Phase 1, `test_example8_y_11_8i` |
| 7 | Koset ayrışımı, ayrıklık, kapsama, tekil decode | **Doğrulandı** (tüm R üzerinde exhaustive) | Phase 1–2 |
| 8 | Decode karmaşıklığı O(\|ε\|) | **Üyelik testi sayısı olarak doğru**, ama ön-hesaplama/bellek gizli; \|ε\|'dan bağımsız O(1) bir doğrudan yöntem var | Phase 2 `scaling` |
| 9 | Teorem 4: stabilizer kodu, boyut K | **Doğrulandı** — R_Q-alt-modülleri için (makalenin Tanım 4'ündeki "additive code" = temel ideal), gerçek dual ile, 3 bağımsız boyut hesabı. Dual-içerme hipotezi bu yapı için gereksiz (hata değil, fazla varsayım). Genel toplamsal (Z_q-alt-grup) kodlarda \|C\|\|C^⊥H\| = \|R\|ⁿ bozulur (karşı-örnek C = Z_q·1: \|C^⊥H\| = 1); orada Hermitian dual yerine **sol iz duali** {v : Tr⟨v,c⟩_H = 0} gerekir | Phase 4, Phase 4 ek, `review_checks` B4 |
| 10 | **Önerme 5**: farklı ε temsilcileri farklı sendrom üretir | **X-tipi okumada çürütüldü** (makalenin Tanım 10 / Remark 4 / Örnek 8 okuması, hatalar X(e), e ∈ ε ⊂ C2): sendrom çekirdeği C2, X(ε) lojik operatör. **Z-tipi okumada** (hatalar Z(e)) koşula bağlı: \|ε\| farklı sendrom ⟺ (ε−ε) ∩ C₁^⊥H = {0}; makalenin üç örneğinde sağlanıyor, genel değil — makalenin kendi ayarında (n = 1, Teorem 4 hipotezleri) bile: Z25[i]'de C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩ (K = 25) için 25 temsilci yalnızca 1 farklı sendrom verir. C1^⊥H ⊆ C1 ise koşul her zaman sağlanır (yeterli koşul; 481/481 durum), değilse çoğunlukla sağlanmaz (16/282). Bağımsız yeniden kurulum Z5[i]⁴'te 21 transversalin hiçbirinde sağlanmaz (Bölüm 8.2) | Phase 5 (sayısal + PennyLane), `zreading_condition`, 3 `paper_claim` testi |
| 11 | Şekil 1–2 (kodsuz SER) | **Nitel olarak yeniden üretildi** (bağımsız yeniden kurulum) | Phase 3 |
| 12 | Şekil 3 "kodlama kazancı" | Eğri **yeniden üretildi**; ancak kazanç **farklı iletim hızlarının** karşılaştırılmasından geliyor. Eşit hızda (128-QAM) koset decoder ~2.5–2.9 dB **kötü** | Phase 3 |
| 13 | Fiziksel kuantum hata düzeltme (makalenin ε çerçevesiyle) | **X-tipi okuma için yanlış**: makalenin seçtiği X(ε) hata kümesi tespit edilemeyen lojik hatalardır; *bu hata kümesi için* hiçbir kurtarma yoktur (Knill–Laflamme). **Z-tipi okumada** (ε−ε) ∩ C₁^⊥H = {0} koşulu altında çalışıyor, ama genel değil (makalenin kendi ayarında karşı-örnek: Z25[i], C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩; yeterli koşul C1^⊥H ⊆ C1). Aynı stabilizer, doğru hata kümesiyle (R/C2 ve R/C1^⊥H transversalleri) kapı düzeyi devrede (kodlayıcı dahil) sadakat 1.0 ile düzeltme yapıyor (Bölüm 8.3, 8.6) | Phase 5–6, `gate_level_css` |
| 14 | (Makalede yok) gürültü altında davranış | Kod-kapasitesi modeli. **Qudit düzeyinde**, kodun tasarlandığı birim-kayma gürültüsünde Z25 kodu p = 0.01'de LER = 1.0×10⁻⁴ (aynı modelde kodlamasız K = 5 qudit: 1.99×10⁻²; K-qudit depolarizasyonunda kodlamasız LER = p = 10⁻²). **İkili kubit gömmesinde** (Düzen A: 10 kubit, Düzen B: 12 kubit) kod kodlamasızdan kötü: bit-flip'lerin çoğu halka elemanında büyük bir sıçramadır (ör. a'nın en anlamlı biti ±16; yalnızca en düşük bitler düzeltilebilir ±1/±i kaymasıdır), kod ise birim kaymalara göre tasarlanmıştır — sonuç gömmeye özgüdür. 10/12 kubitlik kodla 3 kubitlik kodlamasızın karşılaştırması kaynak bakımından adil değildir; aynı kayıt ve kubit sayısıyla kodlamasız referans da raporlandı (Bölüm 9) | Phase 6, `noise_layouts` |

Kısa sonuç: Makalenin **cebirsel çekirdeği** (halka, idealler, boyutlar, koset decoder, Teorem 4 kodu)
sayısal olarak doğru; Tanım 6'daki dual hatalı (doğrusu ⟨σ(q/δ)⟩). **Kuantum hata düzeltme iddiası**
(Önerme 5, Örnek 8 "Quantum context", Remark 4) makalenin **X-tipi okumasıyla** geçerli değil; **Z-tipi okumada**
(ε−ε) ∩ C₁^⊥H = {0} koşulu altında geçerli, ama genel değil. Teorem 4'ün stabilizer kodu, doğru hata kümesiyle
kapı düzeyinde (kodlayıcı, sıralı sendrom ölçümü, kurtarma) sadakat 1.0 ile çalışıyor. Gürültü altında ikili kubit
gömmesinde kodlamasızdan kötü, qudit düzeyi birim-kayma gürültüsünde ise belirgin şekilde iyi. **AWGN kodlama
kazancı** yorumu eşit hız karşılaştırmasında geçerliliğini yitiriyor.

---

## 1. Kaynak dosya envanteri

Çalışma klasöründe bulunan dosyaların tamamı (başka dosya, veri, notebook, MATLAB/Sage kodu **yok**):

| Dosya | Boyut | SHA-256 | Açıklama |
|---|---|---|---|
| `epsilon codes.py` | 10 211 B | `eb593509…f7029e1ca2e` | Yazarların Python kodu (tek dosya) |
| `1-s2.0-S1071579726000924-main.pdf` | 1 555 547 B | `1481e809…70e97a13747c`* | Makale, 22 sayfa |

\* Tam hash'ler: `results/original/phase1_original-20261015T001749Z-DESKTOP-RR5J4T0-d3f0ec9876/results.json`.

Her iki dosya `original_source/` altına **değiştirilmeden** kopyalandı (hash'ler aynı; `test_original_file_unchanged`).
Ek A'daki listeler (s. 21–22) elle `original_source/paper/appendix_A_transcribed.py` dosyasına aktarıldı
(yazar dosyası değildir; yalnızca karşılaştırma için).

**Kaynakta bulunmayan / eksik olanlar**

1. AWGN/SER simülasyon kodu (Şekil 1–3) — yalnızca Ek A.2'deki `gaussian_modulo` fonksiyonu basılmış; sembol
   sayısı, tohum, takımyıldız eşlemesi, normalizasyon ve alıcı yayımlanmamış.
2. Hermitian dual n = 1 için hiç hesaplanmıyor (`hermitian_dual` yalnızca n = 2) → dual-içerme koşulu
   yazar kodunda doğrulanmıyor.
3. Z5[i]⁴ örneğinin (Remark 8) üreteçleri verilmemiş; `search_css_pairs` yalnızca n = 2 ve tek üreteçli modüller arıyor.
4. Kuantum kısmı (Pauli operatörleri, stabilizer, sendrom) için hiçbir kod yok.
5. `random` modülü tohumlanmıyor (sonuç %100 başarı olduğundan çıktıyı etkilemiyor).

**Ortam sapmaları**: Bu makinedeki GPU "RTX 5060 8 GB" değil **RTX 5060 Ti 16 GB**'dir. Kullanıcı kararıyla
üç-makineli Phase 7 iptal edildi; tüm deneyler bu makinede çalıştırıldı. `pennylane-lightning-gpu` ve
cuQuantum (`custatevec-cu12`) native Windows için dağıtılmadığından orada kurulamadı (pip çıktısı ile
doğrulandı); Windows tarafında GPU hızlandırması PyTorch 2.11 + CUDA 12.8 (sm_120 desteği doğrulandı) ile yapıldı.
Kullanıcının önerisiyle **aynı makinedeki WSL2 Ubuntu 26.04** içinde `pennylane-lightning-gpu 0.45.0` kuruldu
(`wsl/setup_wsl_gpu.sh`, Python 3.12.13, aynı paket sürümleri); Blackwell (sm_120) üzerinde `lightning.qubit` ile
aynı durumu ürettiği doğrulandı (`wsl/verify_wsl_gpu.py`: sadakat 1.0 / complex64'te 0.999998). Windows'ta
genişlik nedeniyle çalıştırılamayan devreler orada GPU'da koşturuldu (Bölüm 8.5).

---

## 2. Makale denklemleri ↔ kod eşleştirmesi

| Makale | Yazar kodu (`epsilon codes.py`) | Bağımsız uygulama (`src/epsqec/…`) |
|---|---|---|
| Tanım 3: Z_q[i], i² = −1 | `GaussianInteger` (+, −, ×, conjugate) | `ring/gaussian.py: GaussianRing` (vektörize) |
| Tanım 4: I(α) = {αr} | `GaussianCodeN._generate_elements` (tüm r üzerinden) | `ideals/code.py: AdditiveCode.principal` (bitmap) |
| Tanım 5: ⟨x,y⟩_H = Σ x_j σ(y_j) | `GaussianVector.hermitian_inner_product` | `GaussianRing.hermitian` |
| Tanım 6: C^⊥H := ⟨σ(α)⟩ | — (uygulanmamış) | `hermitian_dual_def6` |
| Örnek 6–7'deki dual {z : z·σ(α₂) = 0} | `hermitian_dual` (yalnız n = 2, tek üreteç) | `hermitian_dual` (gerçek tümleyen, her n) |
| Teorem 2–3: koset ayrışımı | `find_epsilon`, `find_epsilon_canonical`, `verify_epsilon` | `decoder/coset.py` (greedy, katlar, `check_transversal`) |
| Tanım 10 / Ek A.1: ε-decoder | `decode(y, eps, C1)` | `decoder/epsilon_decoder.py` (3 üyelik oracle'ı, sayaçlı) |
| Ek A.2: `gaussian_modulo` | — (yalnız makalede) | `simulation/constellations.py` + torch sürümü |
| Tanım 8: X(u), Z(v), χ, Tr | — | `stabilizer/pauli.py: QuditSpace` (matris-içermeyen) |
| Teorem 4: S = ⟨X(C1), Z(C2^⊥H)⟩, K | — | `stabilizer/code.py: RingCSSCode` |
| Önerme 5 / Remark 4: sendrom | — | `RingCSSCode.zsyn/xsyn/measure_state_syndrome` |
| (Kuantum devre) | — | `pl_circuits/ring_circuits.py` (PennyLane) |

---

## 3. Phase 1 — Orijinal kodun çalıştırılması (exact reproduction)

Deney: `phase1_original-20261015T001749Z-DESKTOP-RR5J4T0-d3f0ec9876` · Komut: `python experiments/phase1_original.py`

* `epsilon codes.py` doğrudan iki kez çalıştırıldı (çıktılar `results/original/original_run_{1,2}.txt`, birebir aynı, ~0.74 s).
* Yazar sınıflarıyla üretilen C1, C2 kümeleri bağımsız sayımla **eleman eleman aynı** (3 halka).
* ε kümeleri: yazar kodunun `find_epsilon_canonical`'ı **{0, iα₂, 2iα₂, …}** üretir (ör. Z25[i]: {0, 24+2i, 23+4i, 22+6i, 21+8i});
  bu makaledeki Örnek 7 kümesi {0, α₂, …, 4α₂} ve Örnek 4 kümesi {0, 10, 10i, 15i, −20i} ile **aynı değildir**, fakat
  hepsi geçerli transversaldir (bağımsız `check_transversal`: ayrıklık + kapsama + |ε| = indeks).
* **Örnek 8**: y = 11+8i, ε = {0, 2+i, 4+2i, 6+3i, 8+4i} → yazar `decode` ve Ek A `decode`: **e = 8+4i, c = 3+4i** ✓.
* **Örnek 5**: y = 2+i, ε = Örnek 4 → **e = 15i, c = 2+11i** (= 12i(3+4i)) ✓.
* Yazar `decode` ile **R'nin tüm elemanları** üzerinde exhaustive decode: Z25 (625), Z85 (7225), Z325 (105 625) — yanlış,
  çoklu veya eksik çözüm **0**; C2 dışındaki sözcükler doğru şekilde `None`. Ek A sürümü ile yazar sürümü her sözcükte aynı.
* `run_simulation` (sabit tohumla) 5000/5000 başarı verir; ancak hatalar **yalnızca ε'dan** çekildiği ve C1+e
  ayrışımı tanım gereği tekil olduğu için bu oran yapısal olarak %100'dür (bilgi taşımayan bir test).

**Yazar kodunda bulunan hata (sessizce düzeltilmedi):** `GaussianCodeN.hermitian_dual()` dönen nesnenin
`.generator` alanını sıfır vektör bırakıyor; dualin duali alınınca tüm uzay döner (Z5[i]², C: 25 eleman →
çift dual: 625; doğru değer 25). Ana akışta kullanılmadığı için makale sonuçlarını etkilemez.
Test: `test_original_hermitian_dual_twice_returns_C` → **FAIL** (sınıf: implementation (original source)).
**Düzeltilmiş sürüm ayrı tutuldu**: `original_source_fixed/epsilon_codes_fixed.py` (5 satırlık değişiklik,
`hermitian_dual_fix.diff`: ortogonallik yalnızca `.generator`'a değil kodun tüm elemanlarına karşı test edilir).
**Etki ölçümü** (`phase1_fixed_impact-20261015T082424Z-DESKTOP-RR5J4T0-5402557e8c`): yazarların `__main__`
çıktısı (makale örnekleri) düzeltilmiş sürümde **bayt bayt aynı**; n = 2 dualleri her iki sürümde bağımsız
uygulamayla aynı; çift dual düzeltilmiş sürümde doğru (25), orijinalde yanlış (625). Yani hata makalenin
yayımlanmış sonuçlarını etkilemiyor. Orijinal dosyanın hash'i değişmedi (`test_original_left_untouched`).
Diğer gizli riskler: `max_elements=10**7`'de sessiz kesme; `search_css_pairs` K'yı |C1|/|C2^⊥| ile hesaplar
(Teorem 4'teki |C2|/|C1| ile yalnızca |C1|² = |R|ⁿ olduğunda çakışır); O(q⁸) arama.

---

## 4. Phase 2 — Bağımsız cebirsel doğrulama

Deney: `phase2_algebra-20261015T002351Z-DESKTOP-RR5J4T0-37dbf23676` (PASS, 119 s)

**Halka aksiyomları**: q ∈ {5, 13, 25, 85} için tüm çiftler üzerinde (değişme, σ'nın çarpımsallığı, normun
çarpımsallığı, iz eşlemesinin dejenere olmaması), q ∈ {5, 13, 25} için tüm üçlüler üzerinde (birleşme, dağılma)
exhaustive kontrol; birimler: norm kriteri = çarpım tablosu (q ≤ 85), Euler formülü ile aynı (Z25: 400 birim).

**İdealler ve dualler (tamamı eleman üretilerek):**

| Halka | \|C1\| | \|C2\| | K | \|C2^⊥H\| gerçek | \|⟨σ(α₂)⟩\| (Tanım 6) | \|C2^⊥\| Öklid | C2^⊥H ⊆ C1 | Tanım-6 ⊆ C1 |
|---|---:|---:|---:|---:|---:|---:|:-:|:-:|
| Z25[i] | 25 | 125 | 5 | 5 | 125 | 5 | ✓ | ✗ |
| Z85[i] | 85 | 1445 | 17 | 5 | 1445 | 5 | ✓ | ✗ |
| Z325[i] | 1625 | 8125 | 5 | 13 | 8125 | 13 | ✓ | ✗ |

* Boyutlar makaleyle aynı; makalenin |⟨α⟩| = q²/N(α) formülü bu örneklerde doğru sonuç verir çünkü α | q
  (genel doğru formül q²/N(gcd(α, q)); ikisi de sayımla karşılaştırıldı).
* Makalede basılı dual üreteçleri doğru: ⟨10+5i⟩ (Z25) ve ⟨75+50i⟩ (Z325) gerçek duale eşit.
* Gerçek dual: |C2|·|C2^⊥H| = |R|, (C2^⊥H)^⊥H = C2, iz-duali = Hermitian dual (her üç halkada).
* **Öklid duali** (eşleniksiz) C1'in alt kümesi değildir → makalenin Hermitian (eşlenikli) form seçimi gerçekten gereklidir.

**Z5[i]⁴ (Remark 8) — bağımsız yeniden kurulum**: makale üreteç vermediği için rastgele arama ile
|C2| = 5⁶, |C1| = 5⁴, |C2^⊥H| = 25, C2^⊥H ⊆ C1 ⊆ C2 sağlayan bir çift 5 denemede bulundu (üreteçler
`configs/phase4_stabilizer.toml`). Bu yapılandırma makaledekiyle aynı olmak zorunda değildir.

**Koset decoder (bağımsız):** tüm transversaller (greedy/Teorem 2, katlar, yazar kanonik, makaledeki basılı
kümeler) geçerli; tüm R üzerinde exhaustive decode: Z25 125/125, Z85 1445/1445, Z325 8125/8125 tekil ve doğru;
C2 dışındaki 500 / 5780 / 97 500 sözcük reddedildi; geçersiz ε (Z25'te C1 içinde bir fark) "non_unique" olarak yakalandı.

**Karmaşıklık (O(|ε|) iddiası):** Her decode 1 + |ε| üyelik testi yapar (Ek A sürümü tüm ε'yu tarar).
Ölçüm (`decoder_scaling.csv`, 4000 decode/nokta, Python):

| Aile | \|ε\| | \|C1\| | bitmap µs | Python-set µs | cebirsel µs | doğrudan bölüm-eşlemesi µs |
|---|---:|---:|---:|---:|---:|---:|
| A (q = 5p) | 13 | 65 | 58.5 | 29.1 | 28.4 | 0.94 |
| A | 53 | 265 | 221.8 | 109.4 | 106.0 | 0.99 |
| A | 197 | 985 | 816.4 | 398.3 | 387.6 | 1.11 |
| B (\|ε\| = 5) | 5 | 65 → 985 | ~26 | ~13.5 | ~13.2 | ~1.0 |

Doğrusal uyum (Aile A): ~2.0 µs/ε-elemanı (set/cebirsel), r² = 0.9999. (Bitmap'in Python setinden yavaş olması
algoritmik değil, test başına numpy çağrı yükünden kaynaklanır.)

Exhaustive decode sayaçları (tüm y ∈ R; her oracle'da aynı sonuç; süre en iyi 3 tekrar, Python):

DECODE_TABLE

 Yani **test sayısı olarak O(|ε|)
doğru**, fakat (i) her testin sabit maliyeti bir ön-hesaplamaya dayanır: bitmap O(q²ⁿ) bellek/zaman,
Python seti O(|C1|) bellek + O(|R|) üretim; bellek gerektirmeyen cebirsel test yalnızca temel idealler için
mümkündür (x ∈ ⟨α⟩ ⇔ gcd(α, q) | x, Z[i]'de bölünebilirlik); (ii) aynı koset etiketini **|ε|'dan bağımsız**
O(1) aritmetikle veren doğrudan yöntem vardır (C2/C1 ≅ Z[i]/(π) ≅ Z_N(π)), bu nedenle O(|ε|) en iyi değildir.
(Doğrudan yöntem makalenin bir sonucu değildir; karşılaştırma tabanıdır.)

---

## 5. Matematiksel tutarsızlıklar ve karşı-örnekler

**5.1 Tanım 6 ↔ Örnek 6–7.** Tanım 6, C^⊥H := ⟨σ(α)⟩ der; Örnek 6–7 ise C2^⊥H = {z : z·σ(α₂) = 0} (gerçek
annihilator) hesaplar. Karşı-örnek (Z25[i]): c = 2+i ∈ C2, v = σ(2+i) = 2−i ∈ ⟨σ(α₂)⟩, ⟨c, v⟩_H = (2+i)² = 3+4i ≠ 0.
Tanım 6 ile |C2|·|C2^⊥H| = 125·125 ≠ 625 ve ⟨σ(α₂)⟩ ⊄ C1 (Z85, Z325'te de).

**Doğru dual (kapalı form).** C = ⟨α⟩ için C^⊥H = Ann(σ(α)) = σ(Ann(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (Z[i]'de;
`hermitian_dual_closed_form`). Tanım 6 ile ancak Ann(α) = ⟨α⟩ iken örtüşür.

REVIEW_A1_TABLE

**Makaledeki basılı koşul (A3).** Makale PDF'inde (kelimesi kelimesine; eşlenik çizgisi PDF görüntüsünde açıkça
basılı, düz metin çıkarımında kayboluyor):

* Örnek 6, Adım 4 (s. 14): "C₂^⊥H = {z ∈ R₃₂₅ : z ᾱ₂ ≡ 0 (mod 325)}" (ᾱ₂: α₂ üzerinde eşlenik çizgisi) — yani **z·σ(α₂) ≡ 0**;
* Örnek 7, Adım 3 (s. 15): "C₂^⊥H = {z ∈ R₂₅ : z (2 + i)‾ ≡ 0 (mod 25)}" (çizgi (2 + i)'nin tamamının üzerinde) — yani **z·σ(2+i) ≡ 0**.

Basılı koşul **doğrudur** (z·α₂ ≡ 0 değil). Kontrol: (10+5i)(2−i) = 25 ≡ 0 ama (10+5i)(2+i) = 15+20i ≢ 0 (mod 25);
(75+50i)(3−2i) ≡ 0 ama (75+50i)(3+2i) = 125+300i ≢ 0 (mod 325). Çizgisiz okunan küme gerçek dualden farklıdır
(`test_printed_condition_with_conjugate_is_the_true_dual`). Dolayısıyla A3 bir makale hatası değildir; hata
yalnızca Tanım 6'dadır.

![Örnek 6, Adım 4 (PDF s. 14, büyütülmüş)](../figures/paper_extracted/ex6_step4.png)

![Örnek 7, Adım 3 (PDF s. 15, büyütülmüş)](../figures/paper_extracted/ex7_step3.png)

**5.2 Lemma 1 hiçbir tek tanım altında tutarlı değil** — doğru dual ile (1) yanlış, (2)–(3) doğru (`lemma1`, tüm α ∈ R için q ∈ {5, 13, 25, 65, 85}; Z325 için tüm 36 ideal):

| Özellik | Gerçek tümleyen | Tanım 6 |
|---|---|---|
| (1) gcd(N(α), q) = 1 ⇒ σ(C^⊥H) = C | **yanlış** (1/1; α birim ⇒ C = R, C^⊥H = {0}) | doğru (her durumda) |
| (2) \|C\|·\|C^⊥H\| = q² | doğru (0 ihlal) | **yanlış** (ör. Z325: 30/36 ideal) |
| (3) C1 ⊆ C2 ⇒ C2^⊥H ⊆ C1^⊥H | doğru (0 ihlal) | **yanlış** (Z325: 288/288 içerme çifti) |

**5.3 Tablo 1–2, Z9 satırı.** C1 = ⟨3⟩, C2 = Z9: C2'nin dualı {0} (boyut 1; Tablo 1: 3); Teorem 4 formülü K = 9/3 = 3 (Tablo 2: K = 1).
Z9 makalenin hipotezinin dışındadır: 9'un tek asal böleni 3 ≡ 3 (mod 4) (makalenin Tablo 1 notu da Z9'un Gauss tamsayı
halkası olmadığını, yalnızca gösterim için verildiğini söyler). Satır yine de kendi içinde tutarsızdır; ilgili iki FAIL
silinmedi, sınıfı "mathematical (paper table entry; case outside the paper's own hypothesis)" olarak güncellendi.
Remark 8 ise K'yı |C1|/|C2^⊥H| ile verir; iki formül yalnızca |C1|² = |R|ⁿ olduğunda çakışır (Z5[i]⁴'te 625² = 25⁴ olduğu için çakışıyor).

**5.4 Teorem 4'ün hipotezi.** Komütasyon için yalnızca C1 ⊆ C2 yeterlidir. Z25[i]'de C1 = ⟨10−5i⟩ ⊆ C2 = ⟨2+i⟩,
C2^⊥H ⊄ C1 çifti için stabilizerler komütatif ve kod boyutu |C2|/|C1| = 25 (iz formülü, yapısal sayım, yoğun null-space):
`phase4_supplement-20261015T005904Z-DESKTOP-RR5J4T0-84a7d8adef`. Dual-içerme koşulu bu yapı için gereksizdir — bu bir
hata değil, fazla bir varsayımdır.

**Teoremin geçerli olduğu kod sınıfı (B4).** Teorem 4 "additive codes" der; makalenin Tanım 4'ü "additive code"u
temel ideal (dolayısıyla R_Q-alt-modülü) olarak tanımlar ve teorem bu sınıfta doğrudur. Genel toplamsal kodlarda
(Z_q-alt-grupları) |C||C^⊥H| = |R|ⁿ geçerli değildir:

REVIEW_B4_TABLE

Modül olmayan kodlarda doğru dual, komütasyon eşleşmesinin dualidir: **sol iz duali** {v : Tr⟨v, c⟩_H = 0 ∀c ∈ C}.
Makalenin izi Tr(a+bi) = a+b σ-değişmez olmadığından (Tr(σ t) = a−b) sağ iz duali {y : Tr⟨c, y⟩_H = 0} komütatif
bir grup vermez. R_Q-alt-modüllerinde üç dual (Hermitian, sol iz, sağ iz) çakışır (`test_trace_sides_agree_for_ideals`).

**5.5 Önerme 5'in ispatındaki hata (X-tipi okuma).** İspat "sıfır sendrom ⇒ operatör tüm stabilizerlerle komütatif ⇒ e_i − e_j ∈ C1"
der. X(e) hataları için komütasyon C1'e değil **normalizatöre** (C2^⊥H)^⊥H = C2'ye üyeliği verir. ε ⊂ C2 olduğundan e_i − e_j ∈ C2
her zaman sıfır sendrom üretir. Aynı karışıklık Örnek 8 "Quantum context" paragrafında vardır; Teorem 4'ün kendi 4. adımı
X(C2)/X(C1)'in **lojik operatörler** olduğunu söyler. Z(e) okumasında ise sendrom çekirdeği C1^⊥H'dir ve sonuç
(ε−ε) ∩ C1^⊥H = {0} koşuluna bağlıdır (Bölüm 8.2). Ayrıntı ve sayısal kanıt: Bölüm 8.

**Remark 4 (A6).** "Artık hata C1'dedir, dolayısıyla zararsızdır" ifadesi yanlıştır. Doğru başarı koşulu:
X tarafında artık e − ê ∈ **C1** (X-stabilizer grubu), Z tarafında artık f − f̂ ∈ **C2^⊥H** (Z-stabilizer grubu).
Sendrom eşitliği X tarafında yalnızca e − ê ∈ C2'yi, Z tarafında f − f̂ ∈ C1^⊥H'yi garanti eder; aradaki fark
(C2/C1 ve C1^⊥H/C2^⊥H) lojik operatörlerdir.

**5.6 Bölüm 4 metni.** "Z[i]/⟨2+i⟩ ile üretilen 25 elemanlı halka": Z[i]/(2+i) 5 elemanlıdır; 25 elemanlı aday
Z[i]/(5) (= Z5[i]) veya Z[i]/((2+i)²) = Z[i]/(3+4i). Her ikisi de ayrı varyant olarak simüle edildi.
**5.7 Karakter konvansiyonu (C2).** Makaleden kelimesi kelimesine (s. 10–11): "We fix a faithful additive character
χ : R_Q → ℂ×, χ(t) = exp(2πi/q · Tr(t)), where Tr : R_Q → ℤ_q is a non-degenerate ℤ_q-linear map"; Tanım 8:
"X(u)|x⟩ := |x + u⟩, Z(v)|x⟩ := χ(⟨v, x⟩_H)|x⟩"; Remark 3: "A concrete non-degenerate trace is obtained by setting
Tr(a + bi) = (a + b) mod q". Bu çalışmanın kullandığı faz exp(2πi[(c+d)a + (d−c)b]/q) (v = c+di, x = a+bi) tam olarak
Tr(v·σ(x)) = (c+d)a + (d−c)b ile **makalenin konvansiyonudur** (farklı değil). Karakter kodda tek bir yerde
(`GaussianRing.trace`) sabitlenmiştir; alternatif Tr = 2·Re (χ = ω^(2Re)) ile Bölüm 4–5 kontrolleri tekrarlandı:

REVIEW_C2_TABLE

Modüller için her iki iz aynı duali verir; kapı düzeyi devrelerde faz kestirimi çekirdeği ω^(+jk) ile ölçülen değer
s = Tr⟨f, u'⟩·p^f/q olarak **aynı Tr ile** yorumlanır (çözücü tablosu da aynı `trace` ile kurulur), bu yüzden
konvansiyon değişince çekirdeğin ω^(2jk) olması gerekmez; tutarlılık `test_X_Z_gates_match_reference_and_commutation[2re-*]`
testiyle devre düzeyinde de doğrulandı.

---

## 6. Phase 3 — AWGN simülasyonları (Şekil 1–3)

Deney: `phase3_awgn-20261015T003413Z-DESKTOP-RR5J4T0-ae42b10bbd` (GPU, 24.7 s) · Komutlar:
`python experiments/phase3_awgn.py` ve `python experiments/plot_awgn.py`

**Kategori: bağımsız yeniden kurulum (independent reconstruction).** Makale simülasyon kodunu, sembol
sayısını, tohumu ve "R_Q" takımyıldızı/alıcısını yayımlamadığı için hiçbir eğri "exact reproduction" değildir.
Kullanılan parametreler (`configs/phase3_awgn.toml`):

* Es = 1 (iletilen kümenin ortalama enerjisi; düzgün öncül), SNR = Es/N0, karmaşık AWGN σ² = N0/2 boyut başına.
* Her SNR noktası: ≥ 500 hata veya 5·10⁷ sembol; 2·10⁶'lık yığınlar; tohum = 2026 + 1000·eğri + round(1000·SNR).
* %95 Clopper–Pearson güven aralıkları; sıfır hatalı noktalar çizilmez (CSV'de üst sınır vardır).
* Alıcılar: ML (sonlu takımyıldızda en yakın nokta), "halka alıcısı" (Ek A.2: yuvarla + mod w), koset decoder
  (Bölüm 4.2: yuvarla → mod 25 → S = y mod (2+i) → ĉ = y − S).
* Doğrulama: 16/256/1024-QAM simülasyonları kapalı form SER ile güven aralığı içinde uyuşur (`test_16qam_ser_matches_closed_form_cpu`).

**Makale figürleriyle karşılaştırma** (`figures/awgn_fig{1,2,3}_side_by_side.png`; makale figürleri PDF'ten
raster olarak çıkarıldı). Makale değerleri **raster görüntüden göz ile okunmuş yaklaşık değerlerdir (≈), kesin sayı değildir.**

| Nokta | Makale (≈ görsel) | Bu çalışma |
|---|---|---|
| Şekil 1, 16-QAM, 18 dB | ≈ 6×10⁻⁴ | 5.46×10⁻⁴ |
| Şekil 1, 32-QAM, 20 dB | ≈ 2.7×10⁻³ | 2.55×10⁻³ |
| Şekil 1, 25-el. R_Q, 20 dB | ≈ 1.5×10⁻³ | 6.6×10⁻⁴ – 1.05×10⁻³ (varyanta göre) |
| Şekil 1, 25-el. R_Q, 0 dB | ≈ 0.83 | 0.82 (ML) / 0.92 (halka alıcısı) |
| Şekil 2, 256-QAM, 30 dB | ≈ 1.3×10⁻³ | 1.12×10⁻³ |
| Şekil 2, 625-el. Z25[i], 34 dB | ≈ 1.1×10⁻³ | 1.04×10⁻³ (halka) / 9.8×10⁻⁴ (ML) |
| Şekil 2, 1024-QAM, 34 dB | ≈ 1.3×10⁻² | 1.28×10⁻² |
| Şekil 3, kodsuz 625, 30 dB | ≈ 5.3×10⁻² | 5.58×10⁻² |
| Şekil 3, kodlu ⟨2+i⟩, 26 / 28 / 30 dB | ≈ 2.6×10⁻² / 5.7×10⁻³ / 5.7×10⁻⁴ | 2.76×10⁻² / 6.66×10⁻³ / 8.07×10⁻⁴ |

Gözlemler: (i) QAM referansları ve Şekil 2–3 yakın uyumludur; Şekil 3'ün kodlu eğrisinin "halka alıcısı +
koset decoder" ile yakından örtüşmesi, yazarların Ek A.2 tabanlı sert-karar alıcısını kullandığını düşündürür
(çıkarım, kanıt değil). (ii) Şekil 1'de 25 elemanlı eğrinin hangi takımyıldız/alıcıyla üretildiği belirlenemedi;
20 dB'de en yakın varyant bile ~1.4–2.3 kat düşük SER verir. (iii) Şekil 2'de 256-QAM'in 32 dB'de eksen altına
düşmesi, makaledeki sembol sayısının ~3×10⁴'ten az olduğunu düşündürür (bizde 32 dB: 2.77×10⁻⁵, 553 hata).

**Kodlama kazancı denetimi (Şekil 3).** 125 noktalı kodlu küme 6.97 bit/sembol, kodsuz 625 nokta 9.29 bit/sembol
taşır; Şekil 3 farklı hızları aynı Es/N0 ekseninde karşılaştırır. Ek eğriler: aynı 125 noktanın ML ile çözümü ve
eşit hızlı (7 bit) kodsuz çapraz 128-QAM. 125 noktalı kümenin d²min/Es = 0.0481, 128-QAM'in 0.0488'dir (geometrik
olarak eşdeğer). Gereken Es/N0 (log-doğrusal enterpolasyon, `crossings.json`):

| Sistem | bit/sembol | SER 10⁻² | SER 10⁻³ | SER 10⁻⁴ |
|---|---:|---:|---:|---:|
| Kodsuz 625, halka alıcısı | 9.29 | 32.13 dB | — | — |
| Kodlu ⟨2+i⟩, koset decoder | 6.97 | 27.48 dB | 29.81 dB | 31.39 dB |
| Aynı 125 nokta, ML | 6.97 | 25.02 dB | 26.90 dB | 28.28 dB |
| Kodsuz 128-QAM (eşit hız), ML | 7.00 | 25.00 dB | 26.88 dB | 28.22 dB |

Kodsuz 625'e göre "kazanç" 10⁻²'de 4.65 dB (Es/N0) / 3.40 dB (Eb/N0) görünür; ancak eşit hızdaki kodsuz
128-QAM'e göre koset decoder **2.48 dB (10⁻²) – 2.93 dB (10⁻³) daha kötüdür**. Kazanç kodlamadan değil hız
düşüşünden gelir; sert-karar koset decode ise aynı noktaların ML çözümüne göre ~2.9 dB kaybettirir.
Bu deneyler klasik AWGN deneyleridir; kuantum hata düzeltme başarısı olarak yorumlanamaz.

![Şekil 1 karşılaştırması: makale (solda) ve bu çalışma (sağda)](../figures/awgn_fig1_side_by_side.png)

![Şekil 2 karşılaştırması](../figures/awgn_fig2_side_by_side.png)

![Şekil 3 karşılaştırması: eşit hızlı 128-QAM ve aynı 125 noktanın ML çözümü eklenmiş](../figures/awgn_fig3_side_by_side.png)

![Şekil 3 verisi Eb/N0 ekseninde (hız-adil görünüm)](../figures/awgn_fig3_ebn0.png)

---

## 7. Phase 4 — Genelleştirilmiş Pauli ve stabilizer doğrulaması

Deney: `phase4_stabilizer-20261015T003729Z-DESKTOP-RR5J4T0-dd69ad0b68` (PASS, 1126 s). Tüm operatörler
matris-içermeyen biçimde (X: permütasyon indeksi, Z: faz vektörü) uygulandı; yoğun matris yalnızca ≤ 625 boyutta
bağımsız kontrol için kuruldu.

| Kontrol | Z5 (test) | Z25[i] | Z85[i] | Z325[i] | Z5[i]⁴ |
|---|:-:|:-:|:-:|:-:|:-:|
| Hilbert boyutu | 25 | 625 | 7225 | 105 625 | 390 625 |
| X(u) permütasyon / Z(v) birim modül | ✓ | ✓ (tüm u) | ✓ (tüm u) | ✓ (örnek) | ✓ (örnek) |
| Z(v)X(u) = χ(⟨v,u⟩_H) X(u)Z(v) | exhaustive | exhaustive (390 625 çift) | 3000 çift | 3000 çift | 3000 çift |
| Stabilizerler komütatif (C1 × C2^⊥H tüm çiftler) | ✓ | ✓ 125 | ✓ 425 | ✓ 21 125 | ✓ 15 625 |
| \|S\| = \|C1\|·\|C2^⊥H\| (farklı operatör sayısı) | 5 | 125 | 425 | 21 125 | 15 625 |
| Kod boyutu: iz formülü = yapısal = (yoğun) | 5 | 5 = 5 = 5 | 17 | 5 | 25 |
| Lojik durumlar ortonormal, stabilize | ✓ | ✓ | ✓ | ✓ | ✓ |
| P = Σ\|ψ_e⟩⟨ψ_e\| (rastgele vektörlerde) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lojik Z grubu \|C1^⊥H\|/\|C2^⊥H\| | 5 | 5 | 17 | 5 | 25 |

Maksimum sayısal hata ≤ 2×10⁻¹⁶ (komütasyon ilişkisi). Skaler katlı eleman: yalnızca özdeşlik.
**Tanım 6 dualiyle**: Z25'te 3125 çiftin 2800'ü, Z85'te 122 825'in 117 776'sı, Z325'te 13 203 125'in 13 050 000'i
komütatif değildir ve üreteçlerin ortak +1 özuzayı **0 boyutludur** (yapısal sayım; Z25'te yoğun null-space ile de 0).
K = |C2|/|C1| ifadesi yalnızca gerçek dual ile hesaplanan +1 özuzay boyutuna eşittir.

---

## 8. Phase 5 — Önerme 5 ve fiziksel hata düzeltme

Üç kavram ayrı tutuldu: (1) klasik koset üyeliği (Bölüm 4: doğru çalışıyor), (2) stabilizer ölçümüyle fiziksel
hatanın tanımlanması, (3) kodlanmış kuantum bilginin geri kazanılması.

### 8.1 Makalenin okuması: X(e), e ∈ ε ⊂ C2 (Remark 4, Tanım 10, Örnek 8)

Deney: `PHASE5_PROP5_ID`

PHASE5_TABLE

* Sendrom eşlemesinin çekirdeği R üzerinde exhaustive olarak **tam C2'dir** (C1 değil). Dolayısıyla tüm ε
  elemanları **aynı (sıfır) sendromu** üretir; Önerme 5 bu hata modeli için yanlıştır.
* X(e), e ∈ ε∖{0}, kod uzayını terk etmez ve lojik bir kaydırmadır: ⟨ψ₀|X(e)|ψ₀⟩ = 0. Knill–Laflamme koşulu
  {X(e) : e ∈ ε} için ihlal edilir (sapma √K: Z25'te 2.236, Z85'te 4.123) → **makalenin seçtiği X(ε) hata kümesi için
  hiçbir kurtarma işlemi yoktur** (yalnızca bu decoder değil). Bu, kodun kusuru değildir: aynı stabilizer, doğru hata
  kümesiyle sadakat 1.0 ile düzeltme yapar (8.3; kapı düzeyinde 8.6).
* Somut karşı-örnek (Z25[i]): |ψ₀⟩ = |C1⟩ = (1/5)Σ_{u∈C1}|u⟩, E = X(2+i). Tüm stabilizer üreteçleri E|ψ₀⟩ üzerinde
  özdeğer 1 verir (sendrom (0 | 0)), ama E|ψ₀⟩ = |ψ₁⟩ ve ⟨ψ₀|ψ₁⟩ = 0. Test: `test_x_errors_in_C2_are_logical_operators`.

### 8.2 Ek okuma (makalede yok): Z(e), e ∈ ε

X-tipi stabilizerlerle ölçülen Z(f) hatalarının sendrom çekirdeği C1^⊥H'dir (R üzerinde exhaustive doğrulandı).
Makalenin üç örneğinde C1^⊥H ⊆ C1 olduğundan Z(e), e ∈ ε, |ε| farklı sendrom verir ve sendrom C1+e kosetleri
üzerinde sabittir (tablodaki son sütun). Bu, Önerme 5'in **faz hatası** okumasında bu üç örnek için doğru
olabileceğini gösterir. Ancak (i) makale bu okumayı yapmaz; (ii) bağımsız Z5[i]⁴ yapılandırmasında bu okuma da
başarısızdır (25 temsilci için yalnızca 5 farklı sendrom) — yani sonuç genel değildir, ek bir koşula
(ör. (ε − ε) ∩ C1^⊥H = {0}) bağlıdır; (iii) Remark 4'teki "artık C1'de, dolayısıyla zararsız" sonucu bu okumada da
geçersizdir (Z(C1) stabilizer grubunda değildir).

**Koşulun sistematik testi (C1).** q ∈ {25, 65, 85, 125, 325} için Teorem 4 hipotezlerini sağlayan **tüm** ideal çiftleri
(C1 ⊊ C2, C2^⊥H ⊆ C1) ve Z5[i]⁴ üzerinde, dört ε seçimiyle "(ε−ε) ∩ C1^⊥H = {0} ⟺ Z(ε) \|ε\| farklı sendrom üretir"
denkliği test edildi (sendromlar C1 üreteçlerine karşı gerçek Tr⟨e, u_k⟩_H değerleri; koşul C1^⊥H koset etiketleriyle,
küçük durumlarda doğrudan fark kümesiyle):

ZREADING_TABLE

### 8.3 Alternatif tasarım (makalenin sonucu DEĞİL, ayrı deneysel öneri)

Aynı Teorem 4 stabilizer grubu için düzeltilebilir hata kümesi standart CSS mantığıyla seçildi:
X(a), a ∈ T_X (R/C2 transversali, en küçük Lee ağırlığı) ve Z(b), b ∈ T_Z (R/C1^⊥H transversali).
\|T_X\| = \|C2^⊥H\|, \|T_Z\| = \|C1\|. Z25'te T_X = {0, ±1, ±i}.

PHASE5_ALT_TABLE

### 8.4 PennyLane devreleri

Deney: `PHASE5_PL_ID` · cihaz `lightning.qubit` (PennyLane 0.45.1)

* **Kodlama (önemli kısıt — bu bölüm, Düzen A)**: Bu bölümdeki deneylerde lojik durumlar tüm kayıt üzerinde
  `qml.StatePrep` ile **genlik yükleme** yoluyla hazırlandı (Z325'te 2²⁴ genlik); bu bir kapı-düzeyi kodlayıcı değildir.
  Kapı düzeyi kodlayıcı daha sonra **Düzen B** (split koordinatlar) için yazıldı ve doğrulandı (Bölüm 8.6); Düzen A
  için kapı düzeyi kodlayıcı yoktur. Bu bölümde kapı düzeyinde olan kısımlar: Pauli hataları X(u)/Z(v), sendrom
  çıkarımı ve kurtarma.
* **Gömme**: x = a + bi → |a⟩_re|b⟩_im, her kayıt ⌈log₂q⌉ kubit (Z25: 10, Z85: 14, Z325: 18 veri kubiti).
  Görevde önerilen 10/13/17 kubit, yoğun a·q+b kodlamasına karşılık gelir; o kodlamada X(u) ayrışmayan bir
  mod-q² toplamaya dönüştüğü için kullanılmadı.
* **X(u)** = `qml.Adder(c, re, mod=q)` · `qml.Adder(d, im, mod=q)` (2 yardımcı kubit). **Z(v)** = her veri kubitine bir
  `PhaseShift` (faz χ(⟨v,x⟩_H) = exp(2πi[(c+d)a + (d−c)b]/q) bit ağırlıklarına ayrışır). Yoğun üniter kullanılmadı.
* **PennyLane'de hazır olmayanlar**: Z_N Fourier dönüşümü (N ≠ 2ᵏ) → X-sendromu için yalnızca ancilla kaydında
  küçük bir `QubitUnitary` (Z25: 32×32, Z85: 128×128); qudit-üstü (d > 3) cihaz ve genelleştirilmiş Pauli kapıları
  yok (kubit gömmesi gerekli).

**Devre şemaları** (Z25[i]; `experiments/draw_circuits.py`, Phase 5'te simüle edilen aynı `RingCircuits` yöntemleriyle
çizildi; tel adları: re0..re4 = a'nın bitleri, im0..im4 = b'nin bitleri, sZ/sX = sendrom ancilla'ları, w0/w1 = Adder
yardımcı kubitleri):

![Bir QEC turunun blok şeması](../figures/circuits/qec_cycle_block.png)

![X(3+4i) kapısı: iki modüler toplayıcı](../figures/circuits/gate_X_3p4i.png)

![qml.Adder(3, mod 25) açılımı: QFT → PhaseAdder → QFT†](../figures/circuits/gate_X_adder_decomposed.png)

![qml.Adder(3, mod 25) kapı düzeyine yakın açılım (tam açılım 178 kapı)](../figures/circuits/gate_X_adder_gatelevel.png)

![Z(10+5i) kapısı: yalnızca tek-kubit faz kapıları](../figures/circuits/gate_Z_10p5i.png)

![Z-tipi sendrom çıkarımı](../figures/circuits/syndrome_Z.png)

![X-tipi sendrom çıkarımı (faz kestirimi)](../figures/circuits/syndrome_X.png)

![Önerme 5 karşı-örnek devresi](../figures/circuits/prop5_counterexample.png)

PHASE5_PL_TABLE

**Bu fazda kendi kodumda bulunan hata**: ilk çalıştırmada X(u) devresi süperpozisyon girdisinde referanstan 0.18
saptı; neden: kuyruk bağlamında oluşturulan `qml.Adder` ikinci kez `qml.apply` ile kuyruğa eklenmişti (X(2u)).
Referans karşılaştırma testi yakaladı; düzeltildi; FAIL kaydı silinmedi
(`phase5_pennylane-20261015T004245Z-DESKTOP-RR5J4T0-9a87023139`). Sınıf: implementation (this project).

### 8.5 lightning.gpu (cuStateVec) — WSL2 Ubuntu

Windows'ta kurulamayan `pennylane-lightning-gpu` aynı makinedeki WSL2 Ubuntu 26.04 içinde kuruldu
(`wsl/setup_wsl_gpu.sh`; Python 3.12, aynı paket sürümleri, torch 2.11 cu128, custatevec-cu12). Windows'ta
genişlik nedeniyle çalıştırılamayan devreler burada GPU'da koşturuldu; sonuçlar aynı `results/` ağacına yazıldı.
Z325 X-sendromu tek devrede 32 tel gerektirdiği için her X-üreteci ayrı devrede ölçüldü (Pauli hatalı durumlar
ortak özdurum olduğundan her sendrom biti deterministiktir; eşdeğer ölçüm). Büyük döngüde geri besleme koherent
(ancilla kayıtlarına koşullu düzeltme kapıları; ertelenmiş ölçüm ilkesi) uygulandı.

PHASE5_GPU

### 8.6 Kapı düzeyi CSS simülasyonu — Düzen A ve Düzen B (kodlayıcı, sıralı sendrom, kurtarma)

GATE_LEVEL_SECTION

---

## 9. Phase 6 — Gürültü deneyleri

**Gürültü modeli: kod-kapasitesi.** Her fiziksel kubite bir kez bağımsız tek-kubit kanal uygulanır; kodlama,
sendrom çıkarımı ve kurtarma idealdir. Kapı sayıları ayrıca raporlanır (aşağıda) — gürültülü kapılar modellenmedi.

**Karşılaştırmanın kapsamı (B3).** (i) 10 kubitlik halka kodunu 3 kubitlik kodlamasız sistemle karşılaştırmak kaynak
bakımından adil değildir; bu yüzden aşağıda aynı kayıt ve aynı kubit sayısıyla kodlamasız referanslar da verildi.
(ii) İkili gömmede bit-flip'lerin çoğu halka elemanında büyük bir sıçramadır (Düzen A: a'nın en anlamlı biti ±16; yalnızca
a ve b'nin en düşük bitleri ±1/±i kaymasıdır; Düzen B: bir rakam içinde ±1, ±2, ±4 ya da geçersiz seviye); kod ise birim kaymalara (±1, ±i) göre tasarlanmıştır. "Halka kodu kodlamasızdan
kötü" sonucu bu gömmeye özgüdür. (iii) Kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde sonuç terstir:

QUDIT_SUMMARY_TABLE

Tüm karşılaştırmalar **aynı lojik kapasitede (K = 5)**:

| Kod | Fiziksel kubit | Not |
|---|---:|---|
| Halka kodu Z25[i] (Teorem 4 + alternatif kurtarma) | 10 | 625 boyut gömülü 1024'e |
| Standart qudit CSS, Z₆₂₅ (C1 = 25Z, C2 = 5Z, C2^⊥ = 125Z) | 10 | aynı Hilbert boyutu (625) ve K |
| Kodlamasız (5 seviye) | 3 | |
| [[5,1,3]] × 3 (standart kubit stabilizer kodu, 8 seviyeli lojik kayıt) | 15 | |

Metrikler: lojik hata oranı = 1 − F_e (lojik kanalın dolanıklık sadakati), ortalama sadakat (K·F_e+1)/(K+1),
kurtarma başarısı (taban girdiler için ⟨j|çıktı|j⟩ ortalaması), sızıntı (gömülü altuzay dışına çıkan nüfus).
Hesaplar tam yoğunluk matrisi (CPU complex128); 10 kubitlik kodlar GPU'da complex64 ile tekrarlandı.

PHASE6_QUBIT_TABLE

![Kubit düzeyi gürültü: lojik hata oranı, dört kod, K = 5](../figures/noise_qubit_level_LER.png)

**Düzen A ve Düzen B, aynı kayıtla kodlamasız referanslar** (`noise_layouts`; yalnızca kapı düzeyi adımlar 1–5'in
geçtiği kodlar için çalıştırıldı):

NOISE_LAYOUTS_TABLE

PHASE6_QUDIT_TABLE

**Kaynak maliyeti** (bir X- + Z-sendrom turu + bir kurtarma; `qml.transforms.decompose` ile {CNOT, RZ, RY,
RX, PhaseShift, ControlledPhaseShift, H, X, Toffoli, QubitUnitary, …} kapı kümesine ayrıştırılmış):

PHASE6_RES_TABLE

---

## 10. GPU performans ve bellek ölçümleri

PHASE_BENCH

---

## 11. Çalıştırılamayan / kısmen çalıştırılan deneyler

NOT_RUN_LIST

---

## 12. Sonraki deneyler için somut gereksinimler

NEXT_LIST

---

## 13. Test sonuçları

TEST_SUMMARY

---

## Ek A — Yeniden üretilebilir komutlar

```powershell
cd epsilon_qec_research
.venv\Scripts\python.exe run_all.py --list          # tüm adımlar
.venv\Scripts\python.exe experiments\phase1_original.py
.venv\Scripts\python.exe experiments\phase2_algebra.py
.venv\Scripts\python.exe experiments\phase3_awgn.py ; .venv\Scripts\python.exe experiments\plot_awgn.py
.venv\Scripts\python.exe experiments\phase4_stabilizer.py ; .venv\Scripts\python.exe experiments\phase4_supplement.py
.venv\Scripts\python.exe experiments\phase5_prop5.py ; .venv\Scripts\python.exe experiments\phase5_pennylane.py
.venv\Scripts\python.exe experiments\phase6_noise.py ; .venv\Scripts\python.exe experiments\plot_noise.py
.venv\Scripts\python.exe experiments\bench_cpu_gpu.py
# ikinci yazar incelemesi ve kapı düzeyi spesifikasyon
.venv\Scripts\python.exe experiments\review_checks.py          # A1, A3, A4, B4, C2   (~15 s)
.venv\Scripts\python.exe experiments\zreading_condition.py     # C1, tüm geçerli çiftler (~7 dk)
.venv\Scripts\python.exe experiments\gate_level_css.py         # adımlar 1-5, Z25/Z65/Z85 (~4.7 sa, CPU)
.venv\Scripts\python.exe experiments\gate_level_css.py --config gate_level_css_2re.toml   # C2, Tr = 2a (~2 dk)
.venv\Scripts\python.exe experiments\noise_layouts.py          # adım 6 (adımlar 1-5 geçtiyse; ~22 dk)
.venv\Scripts\python.exe experiments\mc_seed_check.py ; .venv\Scripts\python.exe experiments\qudit_depolarizing_mc.py
.venv\Scripts\python.exe experiments\apply_review_changes.py   # degisiklikler.py -> şablon/özet (Ek C)
.venv\Scripts\python.exe run_all.py --phases W   # WSL2 lightning.gpu adımları
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe experiments\draw_circuits.py ; .venv\Scripts\python.exe experiments\make_report.py ; .venv\Scripts\python.exe experiments\make_pdf.py
```

Her çalıştırma `results/<kategori>/<deney-kimliği>/` altında `config.json`, `env.json` (GPU, sürücü, CUDA,
Python, paket sürümleri, tohum), `results.json`, CSV ve `status.json` (PASS/FAIL/ERROR, süre, bellek) üretir.

## Ek B — Tüm deney çalıştırmaları

RUN_INDEX

## Ek C — İnceleme sonrası değişen ifadeler (eski → yeni)

EK_C
