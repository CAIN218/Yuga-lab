/* 言語切替の選択を記憶する。英語トップの自動振り分けは、この選択を尊重する。 */
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var to = document.documentElement.lang === 'ja' ? 'en' : 'ja';
        var links = document.querySelectorAll('.lang-dropdown-menu a');
        for (var i = 0; i < links.length; i++) {
            links[i].addEventListener('click', function () {
                try { localStorage.setItem('yl-lang', to); } catch (e) {}
            });
        }
    });
})();
