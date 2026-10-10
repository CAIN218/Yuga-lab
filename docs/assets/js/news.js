/*
 * News shown on the home page (English and Japanese).
 * To post an update, add a new entry at the TOP of this list.
 *   date: "YYYY-MM-DD"
 *   tag:  app name or "Site"
 *   en / ja: one sentence for each language
 *   link: page to open (e.g. "lumina.html"), or null
 */
window.YUGALAB_NEWS = [
    {
        date: "2026-10-10",
        tag: "AudioSwitcher",
        en: "Released AudioSwitcher 1.7.0 with a new interface, animated help, and a choice of which devices appear in Multi-Device.",
        ja: "AudioSwitcher 1.7.0 を公開しました。新しいUI、アニメーションつきのヘルプ、Multi-Device に表示するデバイスの選択に対応しています。",
        link: "audioswitcher.html"
    },
    {
        date: "2026-10-10",
        tag: "Site",
        en: "Redesigned the website and added this News section.",
        ja: "サイトのデザインをリニューアルし、お知らせ欄を追加しました。",
        link: null
    },
    {
        date: "2026-07-19",
        tag: "Lumina",
        en: "Released Lumina, a taskbar app for adjusting the brightness of multiple monitors.",
        ja: "複数モニターの明るさをタスクバーから調整できる「Lumina」を公開しました。",
        link: "lumina.html"
    },
    {
        date: "2026-07-18",
        tag: "AudioSwitcher",
        en: "Released AudioSwitcher, which switches your audio output with one hotkey.",
        ja: "ショートカットキーひとつで音声の出力先を切り替える「AudioSwitcher」を公開しました。",
        link: "audioswitcher.html"
    },
    {
        date: "2026-07-18",
        tag: "MeatCam",
        en: "Added MeatCam, an iOS app now in development, to the site.",
        ja: "開発中のiOSアプリ「MeatCam」の紹介ページを追加しました。",
        link: "meatcam.html"
    }
];

(function () {
    var MAX_ITEMS = 5;
    var list = document.getElementById("news-list");
    if (!list || !window.YUGALAB_NEWS) return;
    var lang = list.getAttribute("data-lang") === "ja" ? "ja" : "en";

    window.YUGALAB_NEWS.slice(0, MAX_ITEMS).forEach(function (item) {
        var li = document.createElement("li");
        var row = document.createElement(item.link ? "a" : "div");
        row.className = "news-row";
        if (item.link) row.href = item.link;

        var time = document.createElement("time");
        time.dateTime = item.date;
        time.textContent = item.date.replace(/-/g, ".");

        var tag = document.createElement("span");
        tag.className = "news-tag";
        tag.textContent = item.tag;

        var text = document.createElement("span");
        text.className = "news-text";
        text.textContent = item[lang];

        row.appendChild(time);
        row.appendChild(tag);
        row.appendChild(text);
        li.appendChild(row);
        list.appendChild(li);
    });
})();
