<div dir="rtl">

# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · **العربية** · [हिन्दी](README.hi.md)

**المطبعة داخل وكيل الذكاء الاصطناعي الخاص بك.** اطلب «بطاقات تعريف لهؤلاء الضيوف الأربعين، وبطاقات عمل، ونشرة إعلانية»:
يصمّمها الوكيل ويرتّبها على الأوراق ويعرض عليك بروفة دقيقة ثم يطبعها على **طابعتك الحقيقية** بدقة المليمتر.
كما أنه **يتذكّر جميع ملفات الطباعة الخاصة بك**: الطابعة والورق والدرج ونوع الوسائط والجودة وملف الألوان والمعايرة،
وحتى خيارات برنامج التشغيل الخاصة بالشركة المصنّعة. اشرح مرة واحدة فقط.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="بروفة لورقة A4 مختلطة"></p>

> الحالة: الإصدار 0.2، ويندوز. جديد: طباعة أي ملف PDF (مثلًا من مهارات تصميم أخرى) وترتيب تلقائي لعناصر كثيرة (`layout`). قريبًا: التعلّم من أخطاء الطباعة، macOS/Linux.

## التثبيت

**Claude Code** (مهارة + خادم MCP في إضافة واحدة):

</div>

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

<div dir="rtl">

**أي عميل MCP** (Claude Desktop وCursor وCodex…):

</div>

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

<div dir="rtl">

يتطلّب [uv](https://docs.astral.sh/uv/) ومتصفح Edge أو Chrome (للعرض).

## لماذا لا نستخدم Ctrl+P؟

| Ctrl+P | printshop-mcp |
|---|---|
| «ملاءمة للصفحة» تصغّر بصمت: 90 مم تصبح 88.7 مم | عرض مباشر بوحدات بكسل الجهاز: 1 مم في CSS = 1 مم على الورق |
| يقع المحتوى في الهامش غير القابل للطباعة | تُظهر البروفة المنطقة غير القابلة للطباعة فعليًا، ويحذّر الفحص المسبق |
| لا يرى الوكيل النتيجة | صور البروفة + تقرير JSON: نص مقطوع، صور منخفضة الدقة، ورق خاطئ |
| تُنسى الإعدادات في كل مرة | ملفات مسمّاة تحفظ حالة برنامج التشغيل كاملة والمعايرة وICC |
| نوع واحد من المطبوعات في كل مرة | بطاقات تعريف وبطاقات عمل ونشرات على أوراق مشتركة مع علامات القص |

## ما يحصل عليه الوكيل

- **المهارة** `skills/printshop`: سير العمل (الملفات ← التصميم ← البروفة ← الطباعة ← تصحيح الملف)، قواعد HTML،
  مرجع الترتيب وقوالب: بطاقات تعريف 90×55، بطاقات عمل 90×50، نشرات A6، بطاقة طاولة، ورقة مختلطة.
- **أدوات MCP**: `list_printers` و`describe_printer` و`list_profiles` و`save_profile` (`open_driver_dialog=true` لضبط
  خيارات الشركة المصنّعة مرة واحدة) و`layout`, `proof` و`print_job` و`printer_status`.
- **HTML**: كل ورقة هي `<section class="ps-sheet" style="width:210mm;height:297mm">` والتخطيط بالمليمتر؛
  `data-fit="9pt"` يصغّر النص حتى يتّسع، و`data-cut` يضيف علامات القص. للعربية استخدم `dir="rtl"` وخط `"Segoe UI", Tahoma`.

## الأمان

لا طباعة إلا بعد `proof`؛ تنتهي صلاحية المهمة بعد ساعة وتُطبع مرة واحدة. يحدّ `PRINTSHOP_MAX_SHEETS` (الافتراضي 50)
من استهلاك الورق، و`PRINTSHOP_DRYRUN=1` لا يرسل أي شيء إلى الطابعة.

ترخيص MIT.

</div>
