/* RAMPA 7 – prehľad rezervácií pre servis. Číta to isté úložisko ako stránka pre zákazníka. */
(function () {
  'use strict';
  var R = window.Rampa;
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  var root = document.documentElement, pas = $('pas');
  function merajPas() { root.style.setProperty('--bar', pas.offsetHeight + 'px'); }
  merajPas(); window.addEventListener('resize', merajPas);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(merajPas);

  var FILTRE = [['nova', 'Nové'], ['potvrdena', 'Potvrdené'], ['caka', 'Čakajú'], ['dokoncena', 'Dokončené'], ['zamietnuta', 'Zamietnuté'], ['zrusena', 'Zrušené'], ['vsetky', 'Všetky']];
  var AKCIE = [['potvrdit', 'Potvrdiť', 'abtn--primary'], ['termin', 'Iný termín', ''], ['dokoncit', 'Dokončené', ''], ['zamietnut', 'Zamietnuť', ''], ['poznamka', 'Poznámka', ''], ['vymazat', 'Vymazať', 'abtn--danger']];
  var IKONA_TEL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 3h3l1.5 4.5-2 1.6a13 13 0 0 0 5.8 5.8l1.6-2 4.5 1.5v3A2.6 2.6 0 0 1 18.4 20 15.4 15.4 0 0 1 4 5.6 2.6 2.6 0 0 1 6.6 3z" fill="currentColor"/></svg>';
  var IKONA_MAIL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v12H3z M3 7l9 7 9-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>';

  R.vzorove(false);
  var filter = 'nova', zoradit = 'termin';
  var filtre = $('filtre'), zoznam = $('zoznam'), prazdne = $('prazdne'), oznam = $('oznam');

  FILTRE.forEach(function (f) {
    var b = el('button', 'tab'); b.type = 'button'; b.dataset.filter = f[0];
    b.appendChild(el('span', null, f[1])); b.appendChild(el('b', null, '0'));
    filtre.appendChild(b);
  });
  filtre.addEventListener('click', function (e) {
    var b = e.target.closest('.tab'); if (!b) return;
    filter = b.dataset.filter; kresli();
  });
  $('zoradit').addEventListener('change', function (e) { zoradit = e.target.value; kresli(); });

  function moze(akcia, r) {
    var zivy = r.stav === 'nova' || r.stav === 'potvrdena' || r.stav === 'caka';
    if (akcia === 'potvrdit') return r.stav === 'nova' || r.stav === 'caka' || ((r.stav === 'zamietnuta' || r.stav === 'zrusena') && R.volneCasy(r.datum).indexOf(r.cas) >= 0);
    if (akcia === 'termin' || akcia === 'dokoncit' || akcia === 'zamietnut') return zivy;
    return true;
  }
  function riadok(dl, nazov, text) { var d = el('div'); d.appendChild(el('dt', null, nazov)); d.appendChild(el('dd', null, text)); dl.appendChild(d); }

  function karta(r) {
    var s = R.sluzba(r.sluzba), li = el('li', 'res res--' + r.stav); li.dataset.id = r.id;
    var top = el('div', 'res__top');
    top.appendChild(el('span', 'tag tag--' + r.stav, R.STAVY[r.stav] || r.stav));
    top.appendChild(el('span', 'res__id', '#' + r.id));
    li.appendChild(top);
    var h = el('h2', 'res__title', s ? s.nazov : r.sluzba); h.id = 'res-' + r.id; h.tabIndex = -1; li.appendChild(h);
    li.setAttribute('aria-labelledby', h.id);
    li.appendChild(el('p', 'res__when', R.fmtTermin(r.datum, r.cas)));
    if (r.stav === 'caka' && r.navrh) li.appendChild(el('p', 'res__alt', 'Navrhnutý nový termín: ' + R.fmtTermin(r.navrh.datum, r.navrh.cas) + '. Čaká sa na odpoveď zákazníka.'));
    li.appendChild(el('p', 'res__who', r.meno));
    var links = el('div', 'res__links');
    var t = el('a'); t.href = 'tel:' + r.telefon.replace(/[^+\d]/g, ''); t.innerHTML = IKONA_TEL; t.appendChild(document.createTextNode(r.telefon));
    var m = el('a'); m.href = 'mailto:' + r.email; m.innerHTML = IKONA_MAIL; m.appendChild(document.createTextNode(r.email));
    links.appendChild(t); links.appendChild(m); li.appendChild(links);
    var dl = el('dl');
    riadok(dl, 'Auto', r.auto);
    if (r.problem) riadok(dl, 'Problém', r.problem);
    if (r.poznamka) riadok(dl, 'Odkaz zákazníka', r.poznamka);
    if (r.poznamkaServisu) riadok(dl, 'Poznámka servisu', r.poznamkaServisu);
    li.appendChild(dl);
    li.appendChild(el('p', 'res__meta', 'Prijaté ' + R.fmtPred(r.vytvorene) + (r.vzor ? ' · vzorová' : r.moja ? ' · z tohto prehliadača' : '')));
    var acts = el('div', 'res__acts');
    AKCIE.forEach(function (a) {
      var b = el('button', 'abtn ' + a[2], a[1]); b.type = 'button'; b.dataset.akcia = a[0]; b.dataset.id = r.id;
      b.setAttribute('aria-label', a[1] + ' – rezervácia #' + r.id + ', ' + r.meno);
      if (!moze(a[0], r)) b.disabled = true;
      acts.appendChild(b);
    });
    li.appendChild(acts);
    return li;
  }

  function kresli(fokus) {
    var vsetky = R.nacitaj(), pocty = { vsetky: vsetky.length };
    vsetky.forEach(function (r) { pocty[r.stav] = (pocty[r.stav] || 0) + 1; });
    Array.prototype.forEach.call(filtre.children, function (b) {
      b.querySelector('b').textContent = pocty[b.dataset.filter] || 0;
      b.setAttribute('aria-pressed', String(b.dataset.filter === filter));
    });
    var list = vsetky.filter(function (r) { return filter === 'vsetky' || r.stav === filter; });
    list.sort(zoradit === 'termin'
      ? function (a, b) { return (a.datum + a.cas).localeCompare(b.datum + b.cas) || a.id - b.id; }
      : function (a, b) { return b.vytvorene.localeCompare(a.vytvorene); });
    zoznam.textContent = '';
    list.forEach(function (r) { zoznam.appendChild(karta(r)); });
    prazdne.hidden = list.length > 0;
    if (!list.length) prazdne.textContent = vsetky.length ? 'V tomto stave teraz nie je žiadna rezervácia.' : 'Zatiaľ žiadne rezervácie. Skúste si jednu objednať na webe servisu alebo obnovte vzorové.';
    var nove = pocty.nova || 0, caka = pocty.caka || 0, d = new Date();
    $('suhrn').innerHTML = '';
    $('suhrn').appendChild(document.createTextNode('Dnes je ' + R.fmtDatum(d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(), true) + ' · '));
    $('suhrn').appendChild(el('strong', null, nove === 0 ? 'žiadna nová' : nove === 1 ? '1 nová' : nove < 5 ? nove + ' nové' : nove + ' nových'));
    $('suhrn').appendChild(document.createTextNode(' čaká na potvrdenie' + (caka ? ', ' + caka + (caka === 1 ? ' čaká' : ' čakajú') + ' na odpoveď zákazníka' : '') + '.'));
    if (fokus) {
      var ciel = zoznam.querySelector('[data-id="' + fokus.id + '"][data-akcia="' + fokus.akcia + '"]:not(:disabled)') || document.getElementById('res-' + fokus.id)
        || filtre.querySelector('[aria-pressed="true"]');
      if (ciel) ciel.focus();
    }
  }

  var casovac = null;
  function povedz(text) {
    oznam.textContent = text; oznam.classList.add('is-on');
    window.clearTimeout(casovac); casovac = window.setTimeout(function () { oznam.classList.remove('is-on'); }, 5200);
  }
  function najdi(id) { return R.nacitaj().filter(function (r) { return r.id === id; })[0]; }

  /* ---------- akcie na karte ---------- */
  var aktivna = null;   // { id, akcia } pre otvorený dialóg
  zoznam.addEventListener('click', function (e) {
    var b = e.target.closest('[data-akcia]'); if (!b || b.disabled) return;
    var id = +b.dataset.id, akcia = b.dataset.akcia, r = najdi(id); if (!r) { kresli(); return; }
    var kto = '#' + r.id + ' (' + r.meno + ')';
    if (akcia === 'potvrdit') {
      var zmeny = { stav: 'potvrdena', navrh: null };
      if (r.stav === 'caka' && r.navrh) { zmeny.datum = r.navrh.datum; zmeny.cas = r.navrh.cas; }
      var nova = R.zmen(id, zmeny);
      povedz('Rezervácia ' + kto + ' je potvrdená na ' + R.fmtTermin(nova.datum, nova.cas) + '. V ostrej prevádzke teraz zákazníkovi odíde e-mail.');
      kresli({ id: id, akcia: 'dokoncit' });
    } else if (akcia === 'dokoncit') {
      R.zmen(id, { stav: 'dokoncena', navrh: null }); povedz('Rezervácia ' + kto + ' je označená ako dokončená.'); kresli({ id: id, akcia: 'poznamka' });
    } else if (akcia === 'zamietnut') {
      R.zmen(id, { stav: 'zamietnuta', navrh: null }); povedz('Rezervácia ' + kto + ' je zamietnutá, termín je znova voľný.'); kresli({ id: id, akcia: 'potvrdit' });
    } else if (akcia === 'vymazat') {
      aktivna = { id: id, akcia: akcia };
      $('dv-nadpis').textContent = 'Vymazať rezerváciu #' + r.id + '?';
      $('dv-text').textContent = r.meno + ', ' + R.fmtTermin(r.datum, r.cas) + '. Rezervácia zmizne natrvalo aj s kontaktnými údajmi zákazníka.';
      $('dlg-vymazat').showModal();
    } else if (akcia === 'termin') {
      aktivna = { id: id, akcia: akcia };
      $('dt-text').textContent = kto + ' má teraz termín ' + R.fmtTermin(r.datum, r.cas) + '.';
      var sd = $('dt-datum'); sd.textContent = '';
      R.dni(12).forEach(function (d) {
        if (!R.volneCasy(d, null, id).length) return;
        var o = el('option', null, R.fmtDatum(d, true)); o.value = d; sd.appendChild(o);
      });
      if (r.navrh) sd.value = r.navrh.datum;
      naplnCasy(r.navrh ? r.navrh.cas : null);
      $('dlg-termin').showModal();
    } else if (akcia === 'poznamka') {
      aktivna = { id: id, akcia: akcia };
      $('dp-koho').textContent = kto; $('dp-text').value = r.poznamkaServisu || '';
      $('dlg-poznamka').showModal();
    }
  });
  function naplnCasy(chcem) {
    var sc = $('dt-cas'), d = $('dt-datum').value, r = aktivna && najdi(aktivna.id); sc.textContent = '';
    if (!d) return;
    R.volneCasy(d, null, aktivna ? aktivna.id : undefined).forEach(function (c) {
      if (r && r.datum === d && r.cas === c) return;                // ten istý termín nie je „iný“
      var o = el('option', null, c.replace(/^0/, '')); o.value = c; sc.appendChild(o);
    });
    if (chcem) sc.value = chcem;
    $('dt-ano').disabled = !sc.options.length;
  }
  $('dt-datum').addEventListener('change', function () { naplnCasy(null); });

  $('dv-ano').addEventListener('click', function () {
    var a = aktivna; $('dlg-vymazat').close(); if (!a) return;
    R.vymaz(a.id); povedz('Rezervácia #' + a.id + ' je vymazaná.'); aktivna = null; kresli({ id: a.id, akcia: 'x' });
  });
  $('dt-form').addEventListener('submit', function () {
    var a = aktivna, d = $('dt-datum').value, c = $('dt-cas').value; if (!a || !d || !c) return;
    R.zmen(a.id, { stav: 'caka', navrh: { datum: d, cas: c } });
    povedz('Zákazníkovi z rezervácie #' + a.id + ' sme navrhli ' + R.fmtTermin(d, c) + '. Čaká sa na jeho odpoveď.');
    aktivna = null; kresli({ id: a.id, akcia: 'potvrdit' });
  });
  $('dp-form').addEventListener('submit', function () {
    var a = aktivna; if (!a) return;
    R.zmen(a.id, { poznamkaServisu: $('dp-text').value.trim() });
    povedz('Poznámka k rezervácii #' + a.id + ' je uložená.'); aktivna = null; kresli({ id: a.id, akcia: 'poznamka' });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-zavriet]'), function (b) {
    b.addEventListener('click', function () { b.closest('dialog').close(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('dialog'), function (d) {
    d.addEventListener('click', function (e) { if (e.target === d) d.close(); });      // klik mimo okna
    d.addEventListener('close', function () {
      if (aktivna) { var a = aktivna; aktivna = null; var b = zoznam.querySelector('[data-id="' + a.id + '"][data-akcia="' + a.akcia + '"]'); if (b) b.focus(); }
    });
  });

  $('vzorove').addEventListener('click', function () {
    R.vzorove(true); filter = 'nova'; kresli(); povedz('Vzorové rezervácie sú obnovené. Vaše vlastné ostali.');
  });
  window.addEventListener('storage', function (e) { if (e.key === R.KEY) kresli(); });

  var maNove = R.nacitaj().some(function (r) { return r.stav === 'nova'; });
  if (!maNove) filter = 'vsetky';
  kresli();
})();
