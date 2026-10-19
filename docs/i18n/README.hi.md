# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · **हिन्दी**

**आपके AI एजेंट के अंदर एक प्रिंटिंग प्रेस।** बस कहिए "इन 40 मेहमानों के लिए बैज, विज़िटिंग कार्ड और एक फ़्लायर":
एजेंट उन्हें डिज़ाइन करता है, शीट पर सजाता है, आपको सटीक प्रूफ़ दिखाता है और **आपके असली प्रिंटर** पर मिलीमीटर
की सटीकता से छापता है। और वह **आपकी सभी प्रिंट प्रोफ़ाइल याद रखता है**: प्रिंटर, काग़ज़, ट्रे, मीडिया का प्रकार,
गुणवत्ता, कलर प्रोफ़ाइल, कैलिब्रेशन, यहाँ तक कि निर्माता के ख़ास ड्राइवर विकल्प भी। एक बार समझाइए, बस।

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="मिश्रित A4 शीट का प्रूफ़"></p>

> स्थिति: v0.2, Windows। नया: कोई भी PDF छापें (जैसे दूसरी डिज़ाइन स्किल से) और कई चीज़ों का स्वचालित लेआउट (`layout`)। आगे: प्रिंट की ग़लतियों से सीखना, macOS/Linux।

## प्रिंटर संगतता

**काग़ज़ पर छापने वाले प्रिंटरों के लिए: इंकजेट, लेज़र, फ़ोटो, डाई-सब्लिमेशन और लेबल प्रिंटर। 3D प्रिंटरों के लिए नहीं।**

जिस भी प्रिंटर का Windows ड्राइवर है, ब्रांड चाहे जो हो, उसके साथ काम करता है: छपाई Windows के मानक प्रिंट सिस्टम से होती है, और निर्माता के ख़ास विकल्प (काग़ज़ का प्रकार, बिना किनारे, गुणवत्ता) ड्राइवर की अपनी सेटिंग विंडो से प्रोफ़ाइल में सहेजे जाते हैं।

| प्रिंटर का प्रकार | ब्रांड |
|---|---|
| इंकजेट | Epson · Canon · HP · Brother |
| लेज़र और MFP | HP · Brother · Canon · Kyocera · Xerox · Ricoh · Konica Minolta · Sharp · Lexmark · OKI · Pantum · Samsung |
| फ़ोटो (इंकजेट) | Epson · Canon · HP |
| डाई-सब्लिमेशन (फ़ोटो) | DNP · Mitsubishi · Citizen · HiTi · Kodak · Canon Selphy |
| लेबल / थर्मल | Zebra · TSC · Brother QL · Dymo · Xprinter |

अब तक जाँचा गया:

| प्रिंटर | प्रकार | स्थिति |
|---|---|---|
| Microsoft Print to PDF | वर्चुअल | ✅ सभी टेस्ट |
| Epson L8050 | इंकजेट, फ़ोटो | ✅ ट्रे, मीडिया प्रकार और किनारे पहचाने गए · टेस्ट प्रिंट बाक़ी |

किसी दूसरे मॉडल से छापा? [बताइए](https://github.com/ildargiv/printshop-mcp/issues/new?template=printer-report.yml), हम इसे सूची में जोड़ देंगे। macOS और Linux (CUPS) योजना में हैं।

## इंस्टॉल करें

**Claude Code** (स्किल + MCP सर्वर एक प्लगइन में):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**कोई भी MCP क्लाइंट** (Claude Desktop, Cursor, Codex…):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

[uv](https://docs.astral.sh/uv/) और रेंडरिंग के लिए Edge या Chrome ज़रूरी है।

## Ctrl+P क्यों नहीं?

| Ctrl+P | printshop-mcp |
|---|---|
| "पेज में फ़िट करें" चुपचाप छोटा कर देता है: 90 mm बन जाता है 88.7 mm | सीधे डिवाइस पिक्सल में रेंडर: CSS में 1 mm = काग़ज़ पर 1 mm |
| सामग्री न छपने वाले किनारे में चली जाती है | प्रूफ़ असली न छपने वाला क्षेत्र दिखाता है, जाँच चेतावनी देती है |
| एजेंट नतीजा नहीं देख पाता | प्रूफ़ इमेज + JSON रिपोर्ट: कटा टेक्स्ट, कम रिज़ॉल्यूशन वाली इमेज, ग़लत काग़ज़ |
| हर बार सेटिंग भूल जाते हैं | पूरी ड्राइवर स्थिति, कैलिब्रेशन और ICC वाली नामित प्रोफ़ाइल |
| एक बार में एक ही तरह की चीज़ | बैज, कार्ड और फ़्लायर कटिंग मार्क के साथ एक ही शीट पर |

## एजेंट को क्या मिलता है

- **स्किल** `skills/printshop`: काम का क्रम (प्रोफ़ाइल → डिज़ाइन → प्रूफ़ → प्रिंट → प्रोफ़ाइल सुधार), HTML नियम,
  लेआउट संदर्भ और टेम्पलेट: बैज 90×55, विज़िटिंग कार्ड 90×50, A6 फ़्लायर, टेबल टेंट, मिश्रित शीट।
- **MCP टूल**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (निर्माता के विकल्प ड्राइवर विंडो में
  एक बार सेट करने के लिए `open_driver_dialog=true`), `layout`, `proof`, `print_job`, `printer_status`।
- **HTML**: हर शीट `<section class="ps-sheet" style="width:210mm;height:297mm">` है, लेआउट mm में;
  `data-fit="9pt"` टेक्स्ट को फ़िट होने तक छोटा करता है; `data-cut` कटिंग मार्क जोड़ता है। हिंदी के लिए `"Nirmala UI"` जैसे फ़ॉन्ट लें।

## सुरक्षा

प्रिंट सिर्फ़ `proof` के बाद; जॉब 1 घंटे में समाप्त होती है और एक ही बार छपती है। `PRINTSHOP_MAX_SHEETS`
(डिफ़ॉल्ट 50) काग़ज़ की खपत सीमित करता है; `PRINTSHOP_DRYRUN=1` प्रिंटर को कुछ नहीं भेजता।

MIT लाइसेंस।
