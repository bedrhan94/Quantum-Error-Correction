"""Changes made to reports/teknik_rapor.template.md after the second-author review (2026-10-15).

Each entry: (id, review item, section, OLD text (exact, as it stood), NEW text, reason).
experiments/apply_review_changes.py applies them (failing loudly if an OLD text is not found) and
writes reports/degisiklikler.json; make_report renders the same list as Ek C.  OLD = "" marks a new
paragraph inserted after the anchor given in `after`.
"""

CHANGES = [
    {
        "id": "C01", "madde": "A1", "bolum": "0 (özet, satır 3)",
        "eski": "| 3 | Tanım 6: C^⊥H := ⟨σ(α)⟩ | **Örnek 6–7 ile çelişkili**: bu tanımla örneklerdeki dual-içerme sağlanmıyor ve Teorem 4 stabilizerleri komütatif değil (kod uzayı 0 boyutlu) | Phase 2, Phase 4; 5 `definition_consistency` testi |",
        "yeni": "| 3 | Tanım 6: C^⊥H := ⟨σ(α)⟩ | **Hatalı tanım.** Doğru dual: C^⊥H = Ann(σ(α)) = σ(Ann(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (Z[i]'de) — q ∈ {25, 65, 85, 125, 325} için tüm idealler (9/16/16/16/36) ve q başına 300 rastgele üreteçle doğrulandı. Tanım 6 yalnızca Ann(α) = ⟨α⟩ iken doğru (bu halkalarda tek durum: Z25'te ⟨5⟩); makale örneklerinin **α₂** üreteçlerinde de **α₁** üreteçlerinde de doğru değil. Tanım 6 ile örneklerdeki dual-içerme sağlanmaz ve Teorem 4 stabilizerleri komütatif olmaz (kod uzayı 0 boyutlu) | `review_checks`; `test_closed_form_*`, `test_definition6_*`; 5 `definition_consistency` testi |",
        "neden": "Kapalı form ve Tanım 6'nın örtüştüğü durumlar eklendi; 'örneklerde geçersiz' ifadesi α₁ ve α₂ için ayrı ayrı kontrol edildi.",
    },
    {
        "id": "C02", "madde": "A2", "bolum": "0 (özet, satır 4)",
        "eski": "| 4 | Lemma 1 (1)–(3) (Tanım 6 ile, yazıldığı gibi) | (1) doğru; **(2) ve (3) yanlış**. Gerçek tümleyenle (2)–(3) doğru, (1) yanlış → tek bir tanım altında birlikte doğru değil | Phase 2 `lemma1`; 2 `paper_claim` + 1 `definition_consistency` testi |",
        "yeni": "| 4 | Lemma 1 (1)–(3) | Doğru dual (Ann) ile: **(1) yanlış** (α birim ⇒ C = R, C^⊥H = {0}), **(2) ve (3) doğru**. Tanım 6 ile (yazıldığı gibi): (1) doğru, (2) ve (3) yanlış → tek bir tanım altında üçü birlikte doğru değil | Phase 2 `lemma1`; 2 `paper_claim` + 1 `definition_consistency` testi |",
        "neden": "Doğru dual altındaki durum öne alındı.",
    },
    {
        "id": "C03", "madde": "A4", "bolum": "0 (özet, satır 5)",
        "eski": "| 5 | Tablo 1–2'deki Z9 satırı (\\|C2^⊥H\\| = 3, K = 1) | **Hatalı** (hesaplanan: 1 ve 3) | 2 `paper_claim` testi |",
        "yeni": "| 5 | Tablo 1–2'deki Z9 satırı (\\|C2^⊥H\\| = 3, K = 1) | **Hatalı** (hesaplanan: 1 ve 3). Not: Z9 makalenin kendi hipotezinin dışındadır (3 ≡ 3 mod 4; makale de \"yalnızca gösterim için\" der); satır yine de kendi içinde tutarsız | 2 `paper_claim` + `outside_hypothesis` testi (sınıf güncellendi) |",
        "neden": "Z9'un hipotez dışında olduğu notu ve FAIL sınıfı güncellemesi.",
    },
    {
        "id": "C04", "madde": "A7, B4", "bolum": "0 (özet, satır 9)",
        "eski": "| 9 | Teorem 4: stabilizer kodu, boyut K | **Doğrulandı** (gerçek dual ile; 3 bağımsız boyut hesabı). Dual-içerme hipotezi bu yapı için gereksiz | Phase 4, Phase 4 ek |",
        "yeni": "| 9 | Teorem 4: stabilizer kodu, boyut K | **Doğrulandı** — R_Q-alt-modülleri için (makalenin Tanım 4'ündeki \"additive code\" = temel ideal), gerçek dual ile, 3 bağımsız boyut hesabı. Dual-içerme hipotezi bu yapı için gereksiz (hata değil, fazla varsayım). Genel toplamsal (Z_q-alt-grup) kodlarda \\|C\\|\\|C^⊥H\\| = \\|R\\|ⁿ bozulur (karşı-örnek C = Z_q·1: \\|C^⊥H\\| = 1); orada Hermitian dual yerine **sol iz duali** {v : Tr⟨v,c⟩_H = 0} gerekir | Phase 4, Phase 4 ek, `review_checks` B4 |",
        "neden": "Hipotezin 'gereksiz' olduğunun hata değil fazla varsayım olduğu; teoremin geçerli olduğu kod sınıfı ve toplamsal kod karşı-örneği.",
    },
    {
        "id": "C05", "madde": "A5, B1", "bolum": "0 (özet, satır 10)",
        "eski": "| 10 | **Önerme 5**: farklı ε temsilcileri farklı sendrom üretir | **Çürütüldü** (makalenin X(e) hata modeli için): C2'nin tüm elemanları sıfır sendrom üretir ve lojik operatördür | Phase 5 (sayısal + PennyLane), 3 `paper_claim` testi |",
        "yeni": "| 10 | **Önerme 5**: farklı ε temsilcileri farklı sendrom üretir | **X-tipi okumada çürütüldü** (makalenin Tanım 10 / Remark 4 / Örnek 8 okuması, hatalar X(e), e ∈ ε ⊂ C2): sendrom çekirdeği C2, X(ε) lojik operatör. **Z-tipi okumada** (hatalar Z(e)) koşula bağlı: \\|ε\\| farklı sendrom ⟺ (ε−ε) ∩ C₁^⊥H = {0}; makalenin üç örneğinde sağlanıyor, genel değil (Z5[i]⁴ karşı-örneği; tüm geçerli ideal çiftleri üzerinde denklik Bölüm 8.2'de) | Phase 5 (sayısal + PennyLane), `zreading_condition`, 3 `paper_claim` testi |",
        "neden": "Bölüm 8.2'nin Z-okuması sonucu özete taşındı.",
    },
    {
        "id": "C06", "madde": "B1, B2", "bolum": "0 (özet, satır 13)",
        "eski": "| 13 | Fiziksel kuantum hata düzeltme (makalenin ε çerçevesiyle) | **Uygulanamaz** (ε hataları tespit edilemeyen lojik hatalardır). Ayrı etiketli alternatif tasarımla gerçek sendrom+recovery çalışıyor ama kubit gömmede kodlamasızdan kötü | Phase 5–6 |",
        "yeni": "| 13 | Fiziksel kuantum hata düzeltme (makalenin ε çerçevesiyle) | **X-tipi okuma için yanlış**: makalenin seçtiği X(ε) hata kümesi tespit edilemeyen lojik hatalardır; *bu hata kümesi için* hiçbir kurtarma yoktur (Knill–Laflamme). **Z-tipi okumada** (ε−ε) ∩ C₁^⊥H = {0} koşulu altında çalışıyor, ama genel değil (Z5[i]⁴). Aynı stabilizer, doğru hata kümesiyle (R/C2 ve R/C1^⊥H transversalleri) kapı düzeyi devrede (kodlayıcı dahil) sadakat 1.0 ile düzeltme yapıyor (Bölüm 8.3, 8.6) | Phase 5–6, `gate_level_css` |",
        "neden": "'Uygulanamaz' ifadesinin kapsamı X okumasıyla ve makalenin seçtiği hata kümesiyle sınırlandı.",
    },
    {
        "id": "C07", "madde": "B3", "bolum": "0 (özet, yeni satır 14)",
        "eski": "",
        "after": "| 13 | Fiziksel kuantum hata düzeltme (makalenin ε çerçevesiyle) |",
        "after_line": True,
        "yeni": "| 14 | (Makalede yok) gürültü altında davranış | Kod-kapasitesi modeli. **Qudit düzeyinde**, kodun tasarlandığı birim-kayma gürültüsünde Z25 kodu p = 0.01'de LER = 1.0×10⁻⁴ (aynı modelde kodlamasız K = 5 qudit: 1.99×10⁻²; K-qudit depolarizasyonunda kodlamasız LER = p = 10⁻²). **İkili kubit gömmesinde** (Düzen A: 10 kubit, Düzen B: 12 kubit) kod kodlamasızdan kötü: tek bir bit-flip halka elemanında büyük bir sıçramadır (ör. a'nın en anlamlı biti ±16), kod ise birim kaymalara göre tasarlanmıştır — sonuç gömmeye özgüdür. 10/12 kubitlik kodla 3 kubitlik kodlamasızın karşılaştırması kaynak bakımından adil değildir; aynı kayıt ve kubit sayısıyla kodlamasız referans da raporlandı (Bölüm 9) | Phase 6, `noise_layouts` |",
        "neden": "Gürültü sonucunun gömmeye özgü olduğu, karşılaştırmanın adilliği ve qudit düzeyi sonuç özete eklendi.",
    },
    {
        "id": "C08", "madde": "B1, B2, B3", "bolum": "0 (kısa sonuç)",
        "eski": "Kısa sonuç: Makalenin **cebirsel çekirdeği** (halka, idealler, boyutlar, koset decoder, Teorem 4 kodu)\nsayısal olarak doğru; **kuantum hata düzeltme iddiası** (Önerme 5, Örnek 8 \"Quantum context\",\nRemark 4) matematiksel olarak geçerli değil; **AWGN kodlama kazancı** yorumu eşit hız karşılaştırmasında\ngeçerliliğini yitiriyor.",
        "yeni": "Kısa sonuç: Makalenin **cebirsel çekirdeği** (halka, idealler, boyutlar, koset decoder, Teorem 4 kodu)\nsayısal olarak doğru; Tanım 6'daki dual hatalı (doğrusu ⟨σ(q/δ)⟩). **Kuantum hata düzeltme iddiası**\n(Önerme 5, Örnek 8 \"Quantum context\", Remark 4) makalenin **X-tipi okumasıyla** geçerli değil; **Z-tipi okumada**\n(ε−ε) ∩ C₁^⊥H = {0} koşulu altında geçerli, ama genel değil. Teorem 4'ün stabilizer kodu, doğru hata kümesiyle\nkapı düzeyinde (kodlayıcı, sıralı sendrom ölçümü, kurtarma) sadakat 1.0 ile çalışıyor. Gürültü altında ikili kubit\ngömmesinde kodlamasızdan kötü, qudit düzeyi birim-kayma gürültüsünde ise belirgin şekilde iyi. **AWGN kodlama\nkazancı** yorumu eşit hız karşılaştırmasında geçerliliğini yitiriyor.",
        "neden": "Özet maddeleriyle tutarlı hale getirildi.",
    },
    {
        "id": "C09", "madde": "A1, A3", "bolum": "5.1",
        "eski": "**5.1 Tanım 6 ↔ Örnek 6–7.** Tanım 6, C^⊥H := ⟨σ(α)⟩ der; Örnek 6–7 ise C2^⊥H = {z : z·σ(α₂) = 0} (gerçek\nannihilator) hesaplar. Karşı-örnek (Z25[i]): c = 2+i ∈ C2, v = σ(2+i) = 2−i ∈ ⟨σ(α₂)⟩, ⟨c, v⟩_H = (2+i)² = 3+4i ≠ 0.\nTanım 6 ile |C2|·|C2^⊥H| = 125·125 ≠ 625 ve ⟨σ(α₂)⟩ ⊄ C1 (Z85, Z325'te de).",
        "yeni": "**5.1 Tanım 6 ↔ Örnek 6–7.** Tanım 6, C^⊥H := ⟨σ(α)⟩ der; Örnek 6–7 ise C2^⊥H = {z : z·σ(α₂) = 0} (gerçek\nannihilator) hesaplar. Karşı-örnek (Z25[i]): c = 2+i ∈ C2, v = σ(2+i) = 2−i ∈ ⟨σ(α₂)⟩, ⟨c, v⟩_H = (2+i)² = 3+4i ≠ 0.\nTanım 6 ile |C2|·|C2^⊥H| = 125·125 ≠ 625 ve ⟨σ(α₂)⟩ ⊄ C1 (Z85, Z325'te de).\n\n**Doğru dual (kapalı form).** C = ⟨α⟩ için C^⊥H = Ann(σ(α)) = σ(Ann(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (Z[i]'de;\n`hermitian_dual_closed_form`). Tanım 6 ile ancak Ann(α) = ⟨α⟩ iken örtüşür.\n\nREVIEW_A1_TABLE\n\n**Makaledeki basılı koşul (A3).** Makale PDF'inde (kelimesi kelimesine; eşlenik çizgisi PDF görüntüsünde açıkça\nbasılı, düz metin çıkarımında kayboluyor):\n\n* Örnek 6, Adım 4 (s. 14): \"C₂^⊥H = {z ∈ R₃₂₅ : z ᾱ₂ ≡ 0 (mod 325)}\" (ᾱ₂: α₂ üzerinde eşlenik çizgisi) — yani **z·σ(α₂) ≡ 0**;\n* Örnek 7, Adım 3 (s. 15): \"C₂^⊥H = {z ∈ R₂₅ : z (2 + i)‾ ≡ 0 (mod 25)}\" (çizgi (2 + i)'nin tamamının üzerinde) — yani **z·σ(2+i) ≡ 0**.\n\nBasılı koşul **doğrudur** (z·α₂ ≡ 0 değil). Kontrol: (10+5i)(2−i) = 25 ≡ 0 ama (10+5i)(2+i) = 15+20i ≢ 0 (mod 25);\n(75+50i)(3−2i) ≡ 0 ama (75+50i)(3+2i) = 125+300i ≢ 0 (mod 325). Çizgisiz okunan küme gerçek dualden farklıdır\n(`test_printed_condition_with_conjugate_is_the_true_dual`). Dolayısıyla A3 bir makale hatası değildir; hata\nyalnızca Tanım 6'dadır.\n\n![Örnek 6, Adım 4 (PDF s. 14, büyütülmüş)](../figures/paper_extracted/ex6_step4.png)\n\n![Örnek 7, Adım 3 (PDF s. 15, büyütülmüş)](../figures/paper_extracted/ex7_step3.png)",
        "neden": "Kapalı form, Tanım 6 örtüşme listesi ve basılı koşulun kelimesi kelimesine kontrolü eklendi.",
    },
    {
        "id": "C10", "madde": "A2", "bolum": "5.2",
        "eski": "**5.2 Lemma 1 hiçbir tek tanım altında tutarlı değil** (`lemma1`, tüm α ∈ R için q ∈ {5, 13, 25, 65, 85}; Z325 için tüm 36 ideal):",
        "yeni": "**5.2 Lemma 1 hiçbir tek tanım altında tutarlı değil** — doğru dual ile (1) yanlış, (2)–(3) doğru (`lemma1`, tüm α ∈ R için q ∈ {5, 13, 25, 65, 85}; Z325 için tüm 36 ideal):",
        "neden": "Doğru dual altındaki sonuç başlığa taşındı.",
    },
    {
        "id": "C11", "madde": "A4", "bolum": "5.3",
        "eski": "**5.3 Tablo 1–2, Z9 satırı.** C1 = ⟨3⟩, C2 = Z9: C2'nin dualı {0} (boyut 1; Tablo 1: 3); Teorem 4 formülü K = 9/3 = 3 (Tablo 2: K = 1).",
        "yeni": "**5.3 Tablo 1–2, Z9 satırı.** C1 = ⟨3⟩, C2 = Z9: C2'nin dualı {0} (boyut 1; Tablo 1: 3); Teorem 4 formülü K = 9/3 = 3 (Tablo 2: K = 1).\nZ9 makalenin hipotezinin dışındadır: 9'un tek asal böleni 3 ≡ 3 (mod 4) (makalenin Tablo 1 notu da Z9'un Gauss tamsayı\nhalkası olmadığını, yalnızca gösterim için verildiğini söyler). Satır yine de kendi içinde tutarsızdır; ilgili iki FAIL\nsilinmedi, sınıfı \"mathematical (paper table entry; case outside the paper's own hypothesis)\" olarak güncellendi.",
        "neden": "Hipotez dışı notu ve FAIL sınıfı güncellemesi.",
    },
    {
        "id": "C12", "madde": "A7, B4", "bolum": "5.4",
        "eski": "`phase4_supplement-20261015T005904Z-DESKTOP-RR5J4T0-84a7d8adef`. Dual-içerme koşulu bu yapı için gereksizdir.",
        "yeni": "`phase4_supplement-20261015T005904Z-DESKTOP-RR5J4T0-84a7d8adef`. Dual-içerme koşulu bu yapı için gereksizdir — bu bir\nhata değil, fazla bir varsayımdır.\n\n**Teoremin geçerli olduğu kod sınıfı (B4).** Teorem 4 \"additive codes\" der; makalenin Tanım 4'ü \"additive code\"u\ntemel ideal (dolayısıyla R_Q-alt-modülü) olarak tanımlar ve teorem bu sınıfta doğrudur. Genel toplamsal kodlarda\n(Z_q-alt-grupları) |C||C^⊥H| = |R|ⁿ geçerli değildir:\n\nREVIEW_B4_TABLE\n\nModül olmayan kodlarda doğru dual, komütasyon eşleşmesinin dualidir: **sol iz duali** {v : Tr⟨v, c⟩_H = 0 ∀c ∈ C}.\nMakalenin izi Tr(a+bi) = a+b σ-değişmez olmadığından (Tr(σ t) = a−b) sağ iz duali {y : Tr⟨c, y⟩_H = 0} komütatif\nbir grup vermez. R_Q-alt-modüllerinde üç dual (Hermitian, sol iz, sağ iz) çakışır (`test_trace_sides_agree_for_ideals`).",
        "neden": "A7 ifadesi netleştirildi; B4 karşı-örneği ve teoremin kod sınıfı eklendi.",
    },
    {
        "id": "C13", "madde": "A5, A6", "bolum": "5.5",
        "eski": "**5.5 Önerme 5'in ispatındaki hata.** İspat \"sıfır sendrom ⇒ operatör tüm stabilizerlerle komütatif ⇒ e_i − e_j ∈ C1\"\nder. Komütasyon C1'e değil **normalizatöre** (C2^⊥H)^⊥H = C2'ye üyeliği verir. ε ⊂ C2 olduğundan e_i − e_j ∈ C2 her zaman\nsıfır sendrom üretir. Aynı karışıklık Remark 4'te (\"artık hata C1'dedir\") ve Örnek 8 \"Quantum context\" paragrafında vardır;\nTeorem 4'ün kendi 4. adımı X(C2)/X(C1)'in **lojik operatörler** olduğunu söyler. Ayrıntı ve sayısal kanıt: Bölüm 8.",
        "yeni": "**5.5 Önerme 5'in ispatındaki hata (X-tipi okuma).** İspat \"sıfır sendrom ⇒ operatör tüm stabilizerlerle komütatif ⇒ e_i − e_j ∈ C1\"\nder. X(e) hataları için komütasyon C1'e değil **normalizatöre** (C2^⊥H)^⊥H = C2'ye üyeliği verir. ε ⊂ C2 olduğundan e_i − e_j ∈ C2\nher zaman sıfır sendrom üretir. Aynı karışıklık Örnek 8 \"Quantum context\" paragrafında vardır; Teorem 4'ün kendi 4. adımı\nX(C2)/X(C1)'in **lojik operatörler** olduğunu söyler. Z(e) okumasında ise sendrom çekirdeği C1^⊥H'dir ve sonuç\n(ε−ε) ∩ C1^⊥H = {0} koşuluna bağlıdır (Bölüm 8.2). Ayrıntı ve sayısal kanıt: Bölüm 8.\n\n**Remark 4 (A6).** \"Artık hata C1'dedir, dolayısıyla zararsızdır\" ifadesi yanlıştır. Doğru başarı koşulu:\nX tarafında artık e − ê ∈ **C1** (X-stabilizer grubu), Z tarafında artık f − f̂ ∈ **C2^⊥H** (Z-stabilizer grubu).\nSendrom eşitliği X tarafında yalnızca e − ê ∈ C2'yi, Z tarafında f − f̂ ∈ C1^⊥H'yi garanti eder; aradaki fark\n(C2/C1 ve C1^⊥H/C2^⊥H) lojik operatörlerdir.",
        "neden": "X okumasıyla sınırlandı; Remark 4 için doğru başarı koşulu yazıldı.",
    },
    {
        "id": "C14", "madde": "C2", "bolum": "5.7 (yeni)",
        "eski": "",
        "after": "Z[i]/(5) (= Z5[i]) veya Z[i]/((2+i)²) = Z[i]/(3+4i). Her ikisi de ayrı varyant olarak simüle edildi.",
        "yeni": "\n**5.7 Karakter konvansiyonu (C2).** Makaleden kelimesi kelimesine (s. 10–11): \"We fix a faithful additive character\nχ : R_Q → ℂ×, χ(t) = exp(2πi/q · Tr(t)), where Tr : R_Q → ℤ_q is a non-degenerate ℤ_q-linear map\"; Tanım 8:\n\"X(u)|x⟩ := |x + u⟩, Z(v)|x⟩ := χ(⟨v, x⟩_H)|x⟩\"; Remark 3: \"A concrete non-degenerate trace is obtained by setting\nTr(a + bi) = (a + b) mod q\". Bu çalışmanın kullandığı faz exp(2πi[(c+d)a + (d−c)b]/q) (v = c+di, x = a+bi) tam olarak\nTr(v·σ(x)) = (c+d)a + (d−c)b ile **makalenin konvansiyonudur** (farklı değil). Karakter kodda tek bir yerde\n(`GaussianRing.trace`) sabitlenmiştir; alternatif Tr = 2·Re (χ = ω^(2Re)) ile Bölüm 4–5 kontrolleri tekrarlandı:\n\nREVIEW_C2_TABLE\n\nModüller için her iki iz aynı duali verir; kapı düzeyi devrelerde faz kestirimi çekirdeği ω^(+jk) ile ölçülen değer\ns = Tr⟨f, u'⟩·p^f/q olarak **aynı Tr ile** yorumlanır (çözücü tablosu da aynı `trace` ile kurulur), bu yüzden\nkonvansiyon değişince çekirdeğin ω^(2jk) olması gerekmez; tutarlılık `test_X_Z_gates_match_reference_and_commutation[2re-*]`\ntestiyle devre düzeyinde de doğrulandı.",
        "neden": "Tanım 8 / Remark 3 aynen aktarıldı; konvansiyon karşılaştırması eklendi.",
    },
    {
        "id": "C15", "madde": "B2", "bolum": "8.1",
        "eski": "* X(e), e ∈ ε∖{0}, kod uzayını terk etmez ve lojik bir kaydırmadır: ⟨ψ₀|X(e)|ψ₀⟩ = 0. Knill–Laflamme koşulu\n  {X(e) : e ∈ ε} için ihlal edilir (sapma √K: Z25'te 2.236, Z85'te 4.123) → **hiçbir kurtarma işlemi bu hata\n  kümesini düzeltemez** (yalnızca bu decoder değil).",
        "yeni": "* X(e), e ∈ ε∖{0}, kod uzayını terk etmez ve lojik bir kaydırmadır: ⟨ψ₀|X(e)|ψ₀⟩ = 0. Knill–Laflamme koşulu\n  {X(e) : e ∈ ε} için ihlal edilir (sapma √K: Z25'te 2.236, Z85'te 4.123) → **makalenin seçtiği X(ε) hata kümesi için\n  hiçbir kurtarma işlemi yoktur** (yalnızca bu decoder değil). Bu, kodun kusuru değildir: aynı stabilizer, doğru hata\n  kümesiyle sadakat 1.0 ile düzeltme yapar (8.3; kapı düzeyinde 8.6).",
        "neden": "'Hiçbir kurtarma' ifadesi makalenin X(ε) hata kümesiyle sınırlandı.",
    },
    {
        "id": "C16", "madde": "B1, C1", "bolum": "8.2",
        "eski": "(ör. (ε − ε) ∩ C1^⊥H = {0}) bağlıdır; (iii) Remark 4'teki \"artık C1'de, dolayısıyla zararsız\" sonucu bu okumada da\ngeçersizdir (Z(C1) stabilizer grubunda değildir).",
        "yeni": "(ör. (ε − ε) ∩ C1^⊥H = {0}) bağlıdır; (iii) Remark 4'teki \"artık C1'de, dolayısıyla zararsız\" sonucu bu okumada da\ngeçersizdir (Z(C1) stabilizer grubunda değildir).\n\n**Koşulun sistematik testi (C1).** q ∈ {25, 65, 85, 125, 325} için Teorem 4 hipotezlerini sağlayan **tüm** ideal çiftleri\n(C1 ⊊ C2, C2^⊥H ⊆ C1) ve Z5[i]⁴ üzerinde, dört ε seçimiyle \"(ε−ε) ∩ C1^⊥H = {0} ⟺ Z(ε) \\|ε\\| farklı sendrom üretir\"\ndenkliği test edildi (sendromlar C1 üreteçlerine karşı gerçek Tr⟨e, u_k⟩_H değerleri; koşul C1^⊥H koset etiketleriyle,\nküçük durumlarda doğrudan fark kümesiyle):\n\nZREADING_TABLE",
        "neden": "Z-okuması koşulunun tüm geçerli çiftlerde testi eklendi.",
    },
    {
        "id": "C17", "madde": "—", "bolum": "8.4",
        "eski": "* **Kodlama (önemli kısıt)**: Lojik durumlar tüm kayıt üzerinde `qml.StatePrep` ile **genlik yükleme** yoluyla\n  hazırlandı (Z325'te 2²⁴ genlik). Bu bir kapı-düzeyi kodlayıcı değildir; simülatörde ayrıştırılmadan yüklendi.\n  Yapılandırılmış (aritmetik) bir kodlayıcı devresi **yazılmadı/çalıştırılmadı (NOT RUN)**. Kapı düzeyinde olan\n  kısımlar: Pauli hataları X(u)/Z(v), sendrom çıkarımı ve kurtarma. Aşağıdaki \"yoğun üniter kullanılmadı\" ifadesi\n  yalnızca bu kısımlar için geçerlidir.",
        "yeni": "* **Kodlama (önemli kısıt — bu bölüm, Düzen A)**: Bu bölümdeki deneylerde lojik durumlar tüm kayıt üzerinde\n  `qml.StatePrep` ile **genlik yükleme** yoluyla hazırlandı (Z325'te 2²⁴ genlik); bu bir kapı-düzeyi kodlayıcı değildir.\n  Kapı düzeyi kodlayıcı daha sonra **Düzen B** (split koordinatlar) için yazıldı ve doğrulandı (Bölüm 8.6); Düzen A\n  için kapı düzeyi kodlayıcı yoktur. Bu bölümde kapı düzeyinde olan kısımlar: Pauli hataları X(u)/Z(v), sendrom\n  çıkarımı ve kurtarma.",
        "neden": "Kapı düzeyi kodlayıcı Düzen B'de eklendi; ifade güncellendi.",
    },
    {
        "id": "C18", "madde": "—", "bolum": "8.6 (yeni)",
        "eski": "",
        "after": "PHASE5_GPU\n",
        "yeni": "\n### 8.6 Kapı düzeyi CSS simülasyonu — Düzen A ve Düzen B (kodlayıcı, sıralı sendrom, kurtarma)\n\nGATE_LEVEL_SECTION\n",
        "neden": "İkinci isteğin (kapı düzeyi spesifikasyon) sonuçları.",
    },
    {
        "id": "C19", "madde": "B3", "bolum": "9",
        "eski": "**Gürültü modeli: kod-kapasitesi.** Her fiziksel kubite bir kez bağımsız tek-kubit kanal uygulanır; kodlama,\nsendrom çıkarımı ve kurtarma idealdir. Kapı sayıları ayrıca raporlanır (aşağıda) — gürültülü kapılar modellenmedi.\nTüm karşılaştırmalar **aynı lojik kapasitede (K = 5)**:",
        "yeni": "**Gürültü modeli: kod-kapasitesi.** Her fiziksel kubite bir kez bağımsız tek-kubit kanal uygulanır; kodlama,\nsendrom çıkarımı ve kurtarma idealdir. Kapı sayıları ayrıca raporlanır (aşağıda) — gürültülü kapılar modellenmedi.\n\n**Karşılaştırmanın kapsamı (B3).** (i) 10 kubitlik halka kodunu 3 kubitlik kodlamasız sistemle karşılaştırmak kaynak\nbakımından adil değildir; bu yüzden aşağıda aynı kayıt ve aynı kubit sayısıyla kodlamasız referanslar da verildi.\n(ii) İkili gömmede tek bir bit-flip, halka elemanında büyük bir sıçramadır (Düzen A: a'nın en anlamlı biti ±16;\nDüzen B: bir rakam içinde ±4); kod ise birim kaymalara (±1, ±i) göre tasarlanmıştır. \"Halka kodu kodlamasızdan\nkötü\" sonucu bu gömmeye özgüdür. (iii) Kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde sonuç terstir:\n\nQUDIT_SUMMARY_TABLE\n\nTüm karşılaştırmalar **aynı lojik kapasitede (K = 5)**:",
        "neden": "Adillik, gömmeye özgüllük ve qudit düzeyi sonuç eklendi.",
    },
    {
        "id": "C20", "madde": "B3", "bolum": "9 (yeni tablo)",
        "eski": "",
        "after": "![Kubit düzeyi gürültü: lojik hata oranı, dört kod, K = 5](../figures/noise_qubit_level_LER.png)\n",
        "yeni": "\n**Düzen A ve Düzen B, aynı kayıtla kodlamasız referanslar** (`noise_layouts`; yalnızca kapı düzeyi adımlar 1–5'in\ngeçtiği kodlar için çalıştırıldı):\n\nNOISE_LAYOUTS_TABLE\n",
        "neden": "Düzen A/B ve eşit kaynaklı kodlamasız referanslar.",
    },
    # ------------------------------------------------------------------ generated text (make_report.py)
    {
        "id": "C21", "madde": "—", "bolum": "11", "file": "experiments/make_report.py",
        "eski": "* **Kapı-düzeyi kodlayıcı (encoder)**: yazılmadı; lojik durumlar `qml.StatePrep` ile genlik yüklenerek hazırlandı (Bölüm 8.4).",
        "yeni": "* **Kapı-düzeyi kodlayıcı (encoder)**: Düzen B (split koordinatlar) için yazıldı ve her j için referansla sadakat 1.0 doğrulandı (Bölüm 8.6). Düzen A (ikili a, b kayıtları) için kapı düzeyi kodlayıcı **yok** (NOT RUN); Düzen A deneylerinde giriş/çıkış genel bir kapı düzeyi durum hazırlama (Möttönen) ile yüklendi.",
        "neden": "Kodlayıcı Düzen B'de eklendi.",
    },
    {
        "id": "C22", "madde": "B1, C1", "bolum": "12 (madde 2)", "file": "experiments/make_report.py",
        "eski": "2. **Önerme 5'in düzeltilmiş biçimi** (ayrı çalışma olarak): X-hataları için doğru ifade \"sendrom ⇔ e + C2 kosetini belirler\" (çekirdek C2), Z-hataları için \"sendrom ⇔ f + C1^⊥H\" — halka ideallerinin hangi koşulunda (C1^⊥H ⊆ C1 gibi) ε-kümesinin faz hataları için düzeltilebilir olduğu ispatlanmalı ve genel n için test edilmeli (altyapı hazır: `phase5_prop5.py`, bölüm B).",
        "yeni": "2. **Önerme 5'in düzeltilmiş biçimi** (ayrı çalışma olarak): X-hataları için doğru ifade \"sendrom ⇔ e + C2 kosetini belirler\" (çekirdek C2), Z-hataları için \"sendrom ⇔ f + C1^⊥H\". Z-okumasındaki \"(ε−ε) ∩ C1^⊥H = {0} ⟺ |ε| farklı sendrom\" denkliği n = 1'de q ∈ {25, 65, 85, 125, 325} için tüm geçerli ideal çiftlerinde ve Z5[i]⁴'te sayısal olarak doğrulandı (Bölüm 8.2); kalan iş: koşulun ideal üreteçleri cinsinden kapalı bir karakterizasyonu ve ispatı, ayrıca ε'nin Z-hataları için *düzeltilebilir* (yalnızca ayırt edilebilir değil: f − f̂ ∈ C2^⊥H) olduğu durumların sınıflandırılması.",
        "neden": "C1 testi tamamlandı; kalan iş yeniden tanımlandı.",
    },
    {
        "id": "C23", "madde": "B3", "bolum": "12 (madde 3)", "file": "experiments/make_report.py",
        "eski": "3. **Adil fiziksel karşılaştırma**: kubit gömmesinde halka kodları kodlamasızdan kötü; anlamlı bir avantaj için ya doğal qudit donanımı (d = 25 veya 625 seviyeli sistem; ör. trapped-ion/süperiletken qudit) için gerçekçi bir gürültü modeli (yakın-komşu seviye geçişleri ≈ birim-kayma modeli) ya da Gray-kodu benzeri, tek-bit hatalarını birim kaymaya eşleyen bir gömme gerekir. Gereken: gömme seçimini parametrize eden yeni bir `RingRegisterLayout`.",
        "yeni": "3. **Adil fiziksel karşılaştırma**: ikili kubit gömmelerinde (Düzen A ve B) halka kodu kodlamasızdan kötü; qudit düzeyi birim-kayma gürültüsünde iyi. Anlamlı bir avantaj için ya doğal qudit donanımı (d = 25 veya 625 seviyeli sistem; ör. trapped-ion/süperiletken qudit) için gerçekçi bir gürültü modeli (yakın-komşu seviye geçişleri ≈ birim-kayma modeli) ya da tek-bit hatalarını birim kaymaya eşleyen (Gray-kodu benzeri) bir rakam gömmesi gerekir. Düzen B'nin rakam yapısı (`SplitLayout`) bu tür bir gömme için hazır başlangıç noktasıdır.",
        "neden": "Düzen B eklendi; gürültü sonucunun kapsamı.",
    },
    # ------------------------------------------------------------------ summary file
    {
        "id": "S01", "madde": "B1", "bolum": "Özet dosyası, tablo (Faz 5)", "file": "CALISMA_OZETI.md",
        "eski": "| ❌ **Önerme 5 yanlış** |",
        "yeni": "| ❌ **Önerme 5, makalenin X-tipi okumasında yanlış**; Z-tipi okumada koşullu ((ε−ε) ∩ C₁^⊥H = {0}), genel değil |",
        "neden": "Kapsam X okumasıyla sınırlandı.",
    },
    {
        "id": "S02", "madde": "B3", "bolum": "Özet dosyası, tablo (Faz 6)", "file": "CALISMA_OZETI.md",
        "eski": "| ❌ Halka kodu hiçbir noktada kodlamasızdan iyi değil |",
        "yeni": "| ⚠️ İkili kubit gömmesinde (10/12 kubit) kodlamasızdan kötü — gömmeye özgü, karşılaştırma kaynak bakımından adil değil; kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde belirgin şekilde iyi (Z₂₅, p = 0.01: LER 1.0×10⁻⁴, kodlamasız K = 5 qudit 1.99×10⁻²) |",
        "neden": "Gürültü sonucunun kapsamı ve qudit düzeyi sonuç.",
    },
    {
        "id": "S03", "madde": "B1, B2", "bolum": "Özet dosyası, bulgu 2", "file": "CALISMA_OZETI.md",
        "eski": "2. **Önerme 5 (makalenin kuantum iddiası) yanlış.** Makalenin hata modelinde (X(e), e ∈ C2) bütün hatalar **sıfır sendrom** üretiyor. Bunlar tespit edilemeyen **lojik hatalar**: kodlanmış bilgiyi bozuyorlar ama ölçümde görünmüyorlar. Hiçbir kurtarma işlemi bunları düzeltemez (Knill–Laflamme koşulu ihlal ediliyor). Beş kodda sayısal olarak, PennyLane devrelerinde de (24 kubite kadar) gösterildi.",
        "yeni": "2. **Önerme 5 (makalenin kuantum iddiası) X-tipi okumada yanlış.** Makalenin hata modelinde (X(e), e ∈ ε ⊂ C2) bütün hatalar **sıfır sendrom** üretiyor. Bunlar tespit edilemeyen **lojik hatalar**: kodlanmış bilgiyi bozuyorlar ama ölçümde görünmüyorlar. *Makalenin seçtiği bu hata kümesi için* hiçbir kurtarma işlemi yoktur (Knill–Laflamme koşulu ihlal ediliyor); aynı stabilizer doğru hata kümesiyle düzeltme yapıyor. Z-tipi okumada (hatalar Z(e)) önerme, (ε−ε) ∩ C₁^⊥H = {0} koşulu altında doğru — makalenin üç örneğinde sağlanıyor, genel değil (Z₅[i]⁴ karşı-örneği). Beş kodda sayısal olarak, PennyLane devrelerinde de (29 kubite kadar) gösterildi.",
        "neden": "X/Z okumaları ayrıldı; 'hiçbir kurtarma' kapsamı sınırlandı.",
    },
    {
        "id": "S04", "madde": "A1, A3, A4", "bolum": "Özet dosyası, bulgu 3", "file": "CALISMA_OZETI.md",
        "eski": "3. **Makalede birbiriyle çelişen tanımlar var.** Tanım 6'daki dual ile Örnek 6–7'de hesaplanan dual farklı; Lemma 1 hiçbir tek tanımla tutarlı değil; Tablo 1–2'deki Z₉ satırı hatalı.",
        "yeni": "3. **Tanım 6'daki dual hatalı.** Doğrusu C^⊥H = Ann(σ(α)) = ⟨σ(q/δ)⟩, δ = gcd(α, q) (beş halkadaki tüm ideallerde doğrulandı); Tanım 6 yalnızca Ann(α) = ⟨α⟩ iken doğru (ör. Z₂₅'te ⟨5⟩), makale örneklerinin hiçbir üretecinde değil. Örnek 6–7'deki basılı koşul (z·σ(α₂) ≡ 0) doğru. Lemma 1 hiçbir tek tanımla tutarlı değil (doğru dual ile (1) yanlış, (2)–(3) doğru). Tablo 1–2'deki Z₉ satırı hatalı (Z₉ zaten makalenin hipotezi dışında: 3 ≡ 3 mod 4).",
        "neden": "A1, A3, A4 bulguları.",
    },
    {
        "id": "S05", "madde": "B3", "bolum": "Özet dosyası, bulgu 6", "file": "CALISMA_OZETI.md",
        "eski": "6. **Fiziksel kuantum hata düzeltme:** Makalenin yöntemiyle mümkün değil. Ayrı etiketli bir alternatif tasarımla (aynı stabilizer, doğru seçilmiş hata kümesi) gerçek sendrom ölçümü + kurtarma çalışıyor (sadakat 1.0). Ama 10 kubite gömülünce gürültüye karşı kodlamasız 3 kubitten bile kötü; standart [[5,1,3]] kodu birkaç mertebe daha iyi.",
        "yeni": "6. **Fiziksel kuantum hata düzeltme:** Makalenin X(ε) hata kümesiyle mümkün değil. Aynı stabilizer, doğru seçilmiş hata kümesiyle (ayrı etiketli alternatif tasarım) kapı düzeyinde çalışıyor: kodlayıcı + sıralı sendrom ölçümü + kurtarma ile sadakat 1.0 (Z₂₅ için tüm 125 hata çifti, iki ölçüm sırası). Gürültü altında: ikili kubit gömmesinde kodlamasızdan kötü — ama bu gömmeye özgü (tek bit-flip halkada büyük sıçrama, kod ise birim kaymalara göre tasarlanmış) ve 10/12 kubitle 3 kubiti karşılaştırmak kaynak bakımından adil değil; aynı kayıtla kodlamasız referans da raporlandı. Kodun tasarlandığı qudit düzeyi birim-kayma gürültüsünde Z₂₅ kodu p = 0.01'de LER = 1.0×10⁻⁴ (kodlamasız: 1.99×10⁻²).",
        "neden": "Gürültü sonucunun kapsamı, kapı düzeyi sonuç.",
    },
    {
        "id": "S06", "madde": "B3", "bolum": "Özet dosyası, grafik açıklaması", "file": "CALISMA_OZETI.md",
        "eski": "**Gürültü altında halka kodu (mavi) ve diğer kodlar** — her kanalda halka kodu kodlamasızdan (gri) kötü,\n[[5,1,3]] (yeşil) en iyisi:",
        "yeni": "**Gürültü altında halka kodu (mavi) ve diğer kodlar (ikili kubit gömmesi, Düzen A)** — bu gömmede her kanalda halka kodu\nkodlamasızdan (gri) kötü, [[5,1,3]] (yeşil) en iyisi. Bu sonuç ikili gömmeye özgüdür; qudit düzeyi birim-kayma gürültüsünde\nsıralama terstir (bkz. bulgu 6, teknik rapor Bölüm 9):",
        "neden": "Gömmeye özgüllük.",
    },
    {
        "id": "S07", "madde": "—", "bolum": "Özet dosyası, yapılamayanlar", "file": "CALISMA_OZETI.md",
        "eski": "- **Kapı düzeyinde kodlayıcı devresi:** Yazılmadı; lojik durumlar doğrudan yüklendi.",
        "yeni": "- **Kapı düzeyinde kodlayıcı (Düzen A):** Yok; Düzen A'da lojik durumlar genel durum hazırlamayla yüklendi. Düzen B'de (split koordinatlar) kapı düzeyi kodlayıcı var ve doğrulandı.",
        "neden": "Kodlayıcı Düzen B'de eklendi.",
    },
    # ------------------------------------------------------------------ second round (independent review of the update)
    {
        "id": "C24", "madde": "B1, C1", "bolum": "0 (özet, satır 10)",
        "eski": "genel değil (Z5[i]⁴ karşı-örneği; tüm geçerli ideal çiftleri üzerinde denklik Bölüm 8.2'de)",
        "yeni": "genel değil — makalenin kendi ayarında (n = 1, Teorem 4 hipotezleri) bile: Z25[i]'de C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩ (K = 25) için 25 temsilci yalnızca 1 farklı sendrom verir. C1^⊥H ⊆ C1 ise koşul her zaman sağlanır (yeterli koşul; 481/481 durum), değilse çoğunlukla sağlanmaz (16/282). Bağımsız yeniden kurulum Z5[i]⁴'te 21 transversalin hiçbirinde sağlanmaz (Bölüm 8.2)",
        "neden": "Genelleme iddiası makalenin kendi ayarındaki bir karşı-örneğe dayandırıldı; Z5[i]⁴'ün bağımsız yeniden kurulum olduğu belirtildi.",
    },
    {
        "id": "C25", "madde": "B1, C1", "bolum": "0 (özet, satır 13)",
        "eski": "ama genel değil (Z5[i]⁴)",
        "yeni": "ama genel değil (makalenin kendi ayarında karşı-örnek: Z25[i], C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩; yeterli koşul C1^⊥H ⊆ C1)",
        "neden": "Karşı-örnek makalenin kendi ayarından seçildi.",
    },
    {
        "id": "C26", "madde": "B3", "bolum": "0 (özet, satır 14)",
        "eski": "tek bir bit-flip halka elemanında büyük bir sıçramadır (ör. a'nın en anlamlı biti ±16)",
        "yeni": "bit-flip'lerin çoğu halka elemanında büyük bir sıçramadır (ör. a'nın en anlamlı biti ±16; yalnızca en düşük bitler düzeltilebilir ±1/±i kaymasıdır)",
        "neden": "'Tek bit-flip' ifadesi abartılıydı: en düşük bitin çevrilmesi birim kaymadır.",
    },
    {
        "id": "C27", "madde": "B3", "bolum": "9",
        "eski": "(ii) İkili gömmede tek bir bit-flip, halka elemanında büyük bir sıçramadır (Düzen A: a'nın en anlamlı biti ±16;\nDüzen B: bir rakam içinde ±4)",
        "yeni": "(ii) İkili gömmede bit-flip'lerin çoğu halka elemanında büyük bir sıçramadır (Düzen A: a'nın en anlamlı biti ±16; yalnızca\na ve b'nin en düşük bitleri ±1/±i kaymasıdır; Düzen B: bir rakam içinde ±1, ±2, ±4 ya da geçersiz seviye)",
        "neden": "'Tek bit-flip' ifadesi abartılıydı.",
    },
    {
        "id": "C28", "madde": "C1", "bolum": "12 (madde 2)", "file": "experiments/make_report.py",
        "eski": "(Bölüm 8.2); kalan iş: koşulun ideal üreteçleri cinsinden kapalı bir karakterizasyonu ve ispatı, ayrıca ε'nin Z-hataları için *düzeltilebilir* (yalnızca ayırt edilebilir değil: f − f̂ ∈ C2^⊥H) olduğu durumların sınıflandırılması.",
        "yeni": "(Bölüm 8.2). Hata kümesi tam olarak Z(ε) ise ayırt edilebilirlik düzeltilebilirliğe denktir (tanımlanan hatanın tersi uygulanır, artık 0; Knill–Laflamme), bu yüzden bu kısım açık değildir. C1^⊥H ⊆ C1 yeterli koşuldur (fark e_i − e_j ∉ C1 ⊇ C1^⊥H; 481/481 durumda sağlandı) ama gerekli değildir (16 durumda C1^⊥H ⊄ C1 iken de sağlanıyor). Kalan iş: koşulun ideal üreteçleri ve ε seçimi cinsinden gerekli-yeterli bir karakterizasyonu.",
        "neden": "Düzeltilebilirlik kısmı açık değil; yeterli koşul eklendi.",
    },
    {
        "id": "C29", "madde": "D", "bolum": "Ek A",
        "eski": ".venv\\Scripts\\python.exe experiments\\bench_cpu_gpu.py\n.venv\\Scripts\\python.exe -m pytest -q\n```",
        "yeni": ".venv\\Scripts\\python.exe experiments\\bench_cpu_gpu.py\n# ikinci yazar incelemesi ve kapı düzeyi spesifikasyon\n.venv\\Scripts\\python.exe experiments\\review_checks.py          # A1, A3, A4, B4, C2   (~15 s)\n.venv\\Scripts\\python.exe experiments\\zreading_condition.py     # C1, tüm geçerli çiftler (~7 dk)\n.venv\\Scripts\\python.exe experiments\\gate_level_css.py         # adımlar 1-5, Z25/Z65/Z85 (~4.7 sa, CPU)\n.venv\\Scripts\\python.exe experiments\\gate_level_css.py --config gate_level_css_2re.toml   # C2, Tr = 2a (~2 dk)\n.venv\\Scripts\\python.exe experiments\\noise_layouts.py          # adım 6 (adımlar 1-5 geçtiyse; ~22 dk)\n.venv\\Scripts\\python.exe experiments\\mc_seed_check.py ; .venv\\Scripts\\python.exe experiments\\qudit_depolarizing_mc.py\n.venv\\Scripts\\python.exe experiments\\apply_review_changes.py   # degisiklikler.py -> şablon/özet (Ek C)\n.venv\\Scripts\\python.exe run_all.py --phases W   # WSL2 lightning.gpu adımları\n.venv\\Scripts\\python.exe -m pytest -q\n.venv\\Scripts\\python.exe experiments\\draw_circuits.py ; .venv\\Scripts\\python.exe experiments\\make_report.py ; .venv\\Scripts\\python.exe experiments\\make_pdf.py\n```",
        "neden": "Yeni deneylerin komutları ve çalışma süreleri eklendi.",
    },
    # ------------------------------------------------------------------ third round (statements in make_report.py)
    {
        "id": "C30", "madde": "B3", "bolum": "9 (qudit düzeyi özet)", "file": "experiments/make_report.py",
        "eski": "Depolarizasyonda qudit düzeyinde de avantaj yoktur (kod, birim kaymaları düzeltir; rastgele Pauli'lerin çoğu birim kayma değildir).",
        "yeni": "Depolarizasyonda qudit düzeyinde avantaj ihmal edilebilir düzeydedir: LER = p·(1 − (N_X·N_Z − 1)/(d² − 1)); Z25 ve Z65'te ≈ 0.96·p, Z85'te ≈ 0.997·p (kod d² Pauli'nin yalnızca N_X·N_Z tanesini düzeltir; rastgele Pauli'lerin çoğu birim kayma değildir).",
        "neden": "'Avantaj yok' kesin değildi: LER ≈ 0.96·p (Z25, Z65), ≈ 0.997·p (Z85); formül ve depolarizasyon Monte Carlo'su eklendi.",
    },
    {
        "id": "C31", "madde": "C1", "bolum": "8.2", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "C1^⊥H ⊆ C1 yeterli koşuldur: ε, C2/C1'in bir transversali olduğundan i ≠ j için e_i − e_j ∉ C1 ⊇ C1^⊥H, dolayısıyla (ε−ε) ∩ C1^⊥H = {0}. Gerekli değildir: C1^⊥H ⊄ C1 olan bazı durumlarda da koşul sağlanır.",
        "neden": "Yeterli koşul, gerekçesi ve pairs.csv'den hesaplanan istatistik eklendi.",
    },
    {
        "id": "C32", "madde": "B1, C1", "bolum": "8.2", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Makalenin kendi ayarında (n = 1, Teorem 4 hipotezleri) karşı-örnek: Z25[i]'de C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩ (K = 25). Burada C1^⊥H = C2 (ve C2^⊥H = C1); ε ⊂ C2 olduğundan ε − ε ⊂ C1^⊥H, yani her Z(e) tüm X-tipi üreteçlerle değişir ve sendromu 0'dır. Bu çift için Z-okuması hiçbir ε seçiminde sağlanmaz.",
        "neden": "Karşı-örnek makalenin kendi ayarından; C1^⊥H = C2 yapısal açıklaması doğrulandı.",
    },
    {
        "id": "C33", "madde": "spec §5 (StatePrep yok)", "bolum": "8.6", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Segmentli motor, her orta-devre ölçümünden sonra çökmüş (ve gerekiyorsa sıfırlanmış) durumu bir sonraki segmentin başında `qml.StatePrep` ile yeniden yükler. Bu bir simülasyon kontrol noktasıdır, kodlayıcı değildir (kodlayıcı tamamen kapı düzeyidir); PennyLane-yerel MCM çapraz kontrolünde StatePrep yoktur ve iki motor aynı dağılımı verir.",
        "neden": "Segmentli motorun StatePrep kontrol noktası açıkça belirtildi (kodlayıcı ile karıştırılmasın).",
    },
    {
        "id": "C34", "madde": "spec §4 (sızıntı)", "bolum": "9 (kubit düzeyi)", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Sızıntı = gürültüden sonra, temel girdiler üzerinden ortalama, geçerli halka-elemanı seviyelerinin dışındaki popülasyon (kurtarma bunu kaybeder). Gürültüsüz devrede sızıntı yoktur: Düzen B kodlayıcısının sızıntısı 0'dır (adım 2) ve tam döngülerde min F ≥ 1 − 10⁻¹² olduğundan döngü sonundaki sızıntı ≤ 1 − F. Gürültülü sızıntı kanaldan gelir; Düzen B'de geçerli seviye oranı daha düşüktür (A: (25/32)² ≈ 0.61, B: (5/8)⁴ ≈ 0.15).",
        "neden": "Düzen A/B sızıntı tablosu ve gürültüsüz sızıntı sınırı eklendi.",
    },
    {
        "id": "C35", "madde": "B3", "bolum": "9 (qudit düzeyi özet)", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Z65'te birim-kayma LER'i tam olarak 0'dır, çünkü 9 X-kayma deseninin ve 9 Z-kayma deseninin hepsi düzeltilir. Z25 ve Z85'te Z-desenlerinin 9'u, X-desenlerinin 5'i düzeltilir; düzeltilemeyen 4 desen (±1, ±1)'dir ve her birinin olasılığı p²/4 olduğundan LER = p².",
        "neden": "Z65'te LER = 0 sonucu desen sayılarıyla açıklandı (qudit_depolarizing_mc, unit_shift_patterns.csv).",
    },
    {
        "id": "C36", "madde": "spec §6 (qudit depolarizasyon MC)", "bolum": "9 (qudit düzeyi özet)", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Depolarizasyon Monte Carlo'su (her (kod, p) için bağımsız tohum) kesin formülle uyumludur. İlk çalıştırma tüm kodlar için aynı tohumu kullanmıştı; p = 0.2'de üç kodun ortak vuruş sayısı beklenenden ~2σ fazlaydı ve Z25 ile Z65'te kesin değer %95 GA'nın hemen dışında kaldı. Bu tek bir ortak dalgalanmadır, simülatör hatası değildir; o çalıştırma silinmedi.",
        "neden": "Depolarizasyon için Monte Carlo eklendi; ilk çalıştırmadaki ortak tohum sorunu raporlandı.",
    },
    {
        "id": "C37", "madde": "spec §7 (PASS/FAIL)", "bolum": "9 (qudit düzeyi özet)", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Geçme ölçütü: her satırda koşullu binom p-değeri > 0.05 / satır sayısı (Bonferroni); aksi halde çalıştırma FAIL olarak işaretlenir. Koşulsuz %95 GA sütunu raporlanır ama ölçüt değildir (6 satırda en az bir GA ıskası ~%26 olasılıkla beklenir). Ölçüt ikinci çalıştırmanın verisi incelendikten sonra eklendi; en küçük koşullu p-değeri 0.18 olduğundan karar bu seçime duyarlı değildir.",
        "neden": "Depolarizasyon MC'sine açık geçme ölçütü eklendi; önceki sürüm her sonucu PASS olarak yazıyordu.",
    },
    {
        "id": "C38", "madde": "spec §7 (PASS/FAIL)", "bolum": "9 (qudit düzeyi özet)", "file": "experiments/make_report.py",
        "eski": "",
        "yeni": "Bu tablodaki çalıştırma durumu (PASS) yalnızca çalıştırmanın tamamlandığını gösterir; istatistiksel kontrol GA sütunu ve aşağıdaki bağımsız tohum takibidir.",
        "neden": "noise_layouts'taki MC tablosunda PASS durumunun anlamı açıklandı (Z25 satırı GA dışında iken durum PASS).",
    },
    {
        "id": "S09", "madde": "D", "bolum": "Özet dosyası, tablo (Faz 8)", "file": "CALISMA_OZETI.md",
        "eski": "Türkçe teknik rapor, 106 otomatik test, tek komutla tekrar çalıştırma (`run_all.py`).",
        "yeni": "Türkçe teknik rapor, 149 otomatik test (135 PASS, 14 FAIL), tek komutla tekrar çalıştırma (`run_all.py`).",
        "neden": "Test sayısı güncellendi.",
    },
    {
        "id": "S10", "madde": "D", "bolum": "Özet dosyası, test özeti", "file": "CALISMA_OZETI.md",
        "eski": "**Testler:** 92 PASS, 14 FAIL. FAIL'lerin 13'ü makaledeki yanlış iddialardan, 1'i yazarların kodundaki hatadan geliyor.",
        "yeni": "**Testler:** 135 PASS, 14 FAIL (matematiksel iddia testleri 33 PASS / 13 FAIL; uygulama testleri 102 PASS / 1 FAIL). 13 matematiksel FAIL: 5'i makalenin sağlanmayan iddiaları, 6'sı makalenin birbiriyle çelişen dual tanımları (Tanım 6), 2'si makalenin kendi hipotezi dışındaki Z₉ tablo satırı. 1 uygulama FAIL'i yazarların kodundaki hatadan.",
        "neden": "Test sayıları ve yeni FAIL sınıfları.",
    },
    {
        "id": "S11", "madde": "B1, C1", "bolum": "Özet dosyası, bulgu 2", "file": "CALISMA_OZETI.md",
        "eski": "genel değil (Z₅[i]⁴ karşı-örneği)",
        "yeni": "genel değil: makalenin kendi ayarında bile karşı-örnek var (Z₂₅[i], C₁ = ⟨10−5i⟩ ⊂ C₂ = ⟨2−i⟩: 25 temsilci, 1 farklı sendrom); C₁^⊥H ⊆ C₁ yeterli koşul",
        "neden": "Karşı-örnek makalenin kendi ayarından seçildi.",
    },
    {
        "id": "S12", "madde": "B3", "bolum": "Özet dosyası, bulgu 6", "file": "CALISMA_OZETI.md",
        "eski": "(tek bit-flip halkada büyük sıçrama, kod ise birim kaymalara göre tasarlanmış)",
        "yeni": "(bit-flip'lerin çoğu halkada büyük bir sıçrama, kod ise birim kaymalara göre tasarlanmış)",
        "neden": "'Tek bit-flip' ifadesi abartılıydı.",
    },
    {
        "id": "S08", "madde": "D", "bolum": "Özet dosyası, giriş", "file": "CALISMA_OZETI.md",
        "eski": "**[reports/teknik_rapor.md](reports/teknik_rapor.md)** (720 satır, 13 bölüm + 2 ek).",
        "yeni": "**[reports/teknik_rapor.md](reports/teknik_rapor.md)** (13 bölüm + 3 ek; Ek C: inceleme sonrası değişen ifadeler).\nKapı düzeyi simülasyonun kısa özeti: **[reports/kapi_duzeyi_ozet.md](reports/kapi_duzeyi_ozet.md)**.",
        "neden": "Yeni ek ve kısa özet.",
    },
]
