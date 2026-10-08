# dsh-power-loss-split — लाइन-हानि ऊर्जा विभाजन और मूल्यांकन तालिका की जाँच

`dsh-power-loss-split` किसी एक लाइन या ट्रांसफार्मर-क्षेत्र की एक मीटरिंग अवधि की सामग्री पढ़ता है — 供电量, 售电量, दर्ज 线损电量 और 线损率 तथा, सामग्री में हो तो, मीटरिंग-बिंदुओं की सूची — और उस पर अंकगणितीय तथा अंतराल-जाँच करता है: ऊर्जा संतुलन, हानि दर, मीटरिंग बिंदुओं का जोड़, आपके द्वारा कॉन्फ़िगर की गई हानि-दर पट्टी और तीन-चरण असंतुलन। हर निष्कर्ष के साथ उसमें लगे अंक और सह्यता दिए जाते हैं, ताकि जाँचने वाला जोड़ दोबारा कर सके, और जो जाँच चल नहीं सकी वह चुपचाप पास होने के बजाय `skipped` में दर्ज होती है।

## यह किन सवालों का जवाब देता है

| आपका सवाल | इसका जवाब |
|---|---|
| दर्ज 线损电量, 供电量 − 售电量 से मेल नहीं खाता। तीनों में से कौन-सा अंक गलत है? | `PL-001` यह नहीं बताएगा। यह अंतर दर्ज करता है — `供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh 相差 50 kWh` — और उसकी तुलना सह्यता `toleranceKwh` से करता है, जो 0 पर आती है, यानी तीनों अंक बिल्कुल बराबर होने चाहिए (万 kWh में रिपोर्ट करने पर पूर्णांकन का अंतर रह जाता है, तब शून्य से भिन्न सह्यता कॉन्फ़िगर करें)। नियम केवल घटाव करता है: यह नहीं तय करता कि तीनों में से कौन-सा मान सही है, और यह भी नहीं देखता कि रीडिंग एक ही अवधि की हैं (抄表同期性)। |
| 线损率 में 5.00% भरा है, पर 线损电量 ÷ 供电量 से 6.25% आता है। क्या गड़बड़ी हर में है? | `PL-002` भाग की प्रक्रिया दिखाता है: यह 线损电量 ÷ 供电量 × 100 निकालता है और दर्ज दर से अंतर 个百分点 में दर्ज करता है, जिसमें पूर्णांकन के लिए डिफ़ॉल्ट `tolerancePoints` 0.01 个百分点 की छूट रहती है — पूर्णांकन के नियम अलग से GB/T 8170-2008 से उद्धृत हैं, जिसका शब्दशः पाठ इस पैक के पास भी नहीं है। यह नहीं आँकता कि हर का दायरा सही है या नहीं (口径, जैसे 无损电量 घटाया जाना चाहिए या नहीं): यह सामग्री में बताना या कॉन्फ़िगर करना आपके हाथ है। |
| मेरी लाइन की हानि दर मुझे ऊँची लगती है। क्या टूल इसे दर्ज करेगा? | अपने आप नहीं। `PL-003` 线损率 की तुलना केवल उस पट्टी से करता है जो आप कॉन्फ़िगर करें (`minRate` / `maxRate`); दोनों 0 पर आती हैं यानी कॉन्फ़िगर नहीं हैं, और तब यह नियम कारण के साथ `skipped` में दर्ज होता है, चुपचाप पास होने के बजाय। कॉन्फ़िगर होने पर भी यह `info` तक सीमित है: निष्कर्ष का अर्थ है कि दर आपकी तय पट्टी से बाहर है, यह नहीं कि हानि असामान्य है। मूल्यांकन लक्ष्य आपकी संस्था प्रति लाइन, प्रति वर्ष देती है, इसलिए कोई मान ठहराया नहीं गया। |
| मीटरिंग-बिंदुओं की सूची का जोड़ दर्ज 售电量 से कम है। क्या कोई मीटरिंग बिंदु छूट गया है? | `PL-004` केवल अंतर दर्ज करता है: जिन मीटरिंग बिंदुओं में ऊर्जा का मान है उन्हें जोड़कर दर्ज 售电量 से मिलाता है — 售电量 न हो तो 供电量 से —, सह्यता `toleranceKwh` (डिफ़ॉल्ट 0) के साथ। बिंदु छूटना, दो बार गिना जाना और रीडिंग का समकालिक न होना (抄表不同期) — तीनों एक ही अंतर पैदा करते हैं, इसलिए कारण हाथ से जाँचना पड़ता है; नियम केवल जोड़ करता है। |
| शीट में केवल A और B चरण के मान हैं। असंतुलन की जाँच क्या करती है? | `PL-005` स्वयं को `skipped` में दर्ज करता है: इसे A, B और C नाम के मीटरिंग बिंदु चाहिए, और तीन से कम चरण-मान होने पर यह चल नहीं सकता। तीनों होने पर भी सीमा `maxUnbalancePercent` कॉन्फ़िगर नहीं है (0) और नियम फिर `skipped` में जाता है। सीमा तय करने पर यह (最大值 − 最小值) ÷ 最大值 निकालता है, वह सूत्र निष्कर्ष के साथ दिखाता है, और `info` तक सीमित रहता है: यह नहीं आँकता कि असंतुलन कोई दोष है या नहीं (是否构成缺陷)। |

## यह किन मानकों पर आधारित है

| दस्तावेज़ | संख्यांक | इन्हें उद्धृत करने वाले नियम |
|---|---|---|
| 《电力网电能损耗计算导则》 | DL/T 686-2018 | PL-001, PL-002, PL-003, PL-004, PL-005 |
| 《数值修约规则与极限数值的表示和判定》 | GB/T 8170-2008 | PL-002 |

**Boundary:** this plugin does **arithmetic and interval checks** on one metering period's line-loss
figures — the energy balance, the loss rate, the meter-list sum, the phase unbalance — and shows its
working in every finding. It is not a metering or metering-fault tool (there is no probe, no AMI
integration, no hardware model) and it does not decide whether a loss figure is reasonable or whether
tampering occurred. It reads a spreadsheet export and reports which sums do not close.

> ### ⚠️ Read this before trusting a citation in the report
>
> **Every `excerpt` in this plugin's rule pack says, in so many words, that the clause text was not
> obtained.** The two relations the plugin checks — 线损电量 = 供电量 − 售电量 and
> 线损率 = 线损电量 ÷ 供电量 × 100 — are **definitional**, and their normative home is
> **DL/T 686-2018《电力网电能损耗计算导则》**. That standard is **in force**, and its table of
> contents was verified (chapter 3 is 术语和定义, chapter 8 is 电力网电能损耗分析与降损措施效果计算),
> but **its body is not published for free**, so no verbatim clause could be read.
>
> Rather than paraphrase a quotation, this pack states the gap outright in the `excerpt` field and puts
> the honest reasoning in `note`. Everything is therefore capped at `warn` (principle-derived) or `info`
> (locally configured), and a test asserts that no rule claims a quotation it does not have. **When the
> standard text is in hand, two things must be done: replace each `excerpt` with the real clause, and
> raise `kind` to `direct`.** Until then a finding means "these two numbers do not close", not
> "you violated a standard".
>
> **Assessment thresholds are yours, not the standard's.** Line-loss targets are issued per line and per
> year by the enterprise or its superior, so `PL-003`'s band and `PL-005`'s unbalance limit ship
> **empty**, and a rule that cannot run says so in `skipped` rather than passing silently.

## Compatibility

| सतह | स्थिति |
|---|---|
| Harness | peer रेंज `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — `0.2.0-rc.2` और `0.2.1-alpha.1` दोनों को स्वीकार करने के लिए सत्यापित। **`engines.dsh` जानबूझकर घोषित नहीं**: इसका कोई पाठक नहीं और यह किसी होस्ट को अस्वीकार नहीं कर सकता |
| Node | `^22.19.0 || >=24.0.0` |
| प्लेटफ़ॉर्म | सभी (शुद्ध ESM; कोई नेटिव कोड नहीं, कोई नेटवर्क नहीं, कोई मॉडल कॉल नहीं) |
| टूल मोड | `native`, `ptc` और `both` में काम करता है; पूरे फ़ोल्डर के लिए `ptc` चुनें |

## What it does

नियम-सूची, फ़ील्ड और विस्तृत व्यवहार [README.md](README.md#what-it-does) (अंग्रेज़ी मुख्य संस्करण) में हैं। यह प्लगइन केवल उद्धृत धाराओं के सामने शाब्दिक अंतर सूचीबद्ध करता है और हर न चल पाई जाँच को `skipped` में बताता है।

## Install

```sh
dsh plugin --profile <name> add dsh-power-loss-split
dsh --profile <name> --dump-config | grep 'dsh-power-loss-split'
```

## Configuration

सभी समायोज्य पैरामीटर `src/config.ts` की Schemastery स्कीमा में हैं, इसलिए कोड बदले बिना `cordis.yml` से बदले जा सकते हैं; प्रति-नियम सीमाएँ `rules/` के नियम-पैक में हैं।

| कुंजी | प्रकार | डिफ़ॉल्ट | विवरण |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | नियम-पैक का पथ, पैकेज रूट के सापेक्ष |
| `disabledRules` | string[] | `[]` | बंद करने वाले नियम id; प्रत्येक `skipped` में दिखता है |
| `onlyRules` | string[] | `[]` | केवल ये नियम चलाएँ; खाली होने पर सभी नियम चलते हैं |
| `skipNotes` | string | `""` | हर `skipped` कारण के आगे जोड़ी जाने वाली टिप्पणी |
| `timeoutMs` | number | `120000` | उपकरण का सहकारी समय-सीमा बजट |

## Material format

JSON या YAML स्वीकार्य है। पूरा फ़ील्ड उदाहरण [README.md](README.md#material-format) (अंग्रेज़ी मुख्य संस्करण) में है। पढ़ने की परत में फ़ील्ड वैकल्पिक हैं और जाँच इंजन उन्हें सत्यापित करता है, इसलिए आंशिक निर्यात पर क्रैश के बजाय "अनुपस्थित" श्रेणी के निष्कर्ष मिलते हैं।

## Rule sources

नियम-डेटा कोड से अलग है: प्रत्येक नियम में दस्तावेज़, संख्या, स्रोत की अपनी क्रमांकन-प्रणाली के अनुसार धारा, शब्दशः उद्धरण और स्रोत URL होता है। लोडर लागू करता है कि उद्धरण कम से कम आठ अक्षरों का वास्तविक उद्धरण हो, और जिस जाँच का आधार केवल सामान्य सिद्धांत (`kind: derived-from-principle`, अधिकतम `warn`) या स्थानीय नीति (`kind: institutional-configuration`, अधिकतम `info`) हो, उसे कभी `error` घोषित न किया जाए।

सत्यापित सीमाएँ और जान-बूझकर **न** कहे गए निष्कर्ष [README.md](README.md#rule-sources) (अंग्रेज़ी मुख्य संस्करण) और `rules/evidence/` में हैं।

## Troubleshooting

- **प्लगइन इंस्टॉल हो गया पर टूल दिखता नहीं**: जाँचें कि `main` `lib/index.mjs` पर जाता है और `pnpm run build` ने उसे बनाया है।
- **`dsh plugin add` असंगत बताकर मना करता है**: peer range `0.1.x` और `0.2.x` दोनों को कवर करती है; बाहर होने पर स्पष्ट छूट दें: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`।
- **कोई नियम नहीं चला**: `skipped` सरणी देखें।
- **`check` में `manifest-peers` विफल दिखता है**: यह `dsh-plugin-dev` की ज्ञात अपस्ट्रीम समस्या है; रनटाइम इंस्टॉल के समय अनुकूलता लागू करता है।
- **समय खिसका हुआ लगता है**: सारी गणना दिए गए स्ट्रिंग पर वॉल-क्लॉक है।

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-loss-split
```

अंतिम कमांड `../_shared` का साझा किट `src/shared/` में कॉपी करता है; हर साझा बदलाव के बाद इसे दोबारा चलाएँ।

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-loss-split contributors.
