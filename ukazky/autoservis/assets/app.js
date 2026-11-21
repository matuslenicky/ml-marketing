/* RAMPA 7 – stránka pre zákazníka: scéna riadená skrolovaním, body služieb, cenník, objednávka termínu. */
(function () {
  'use strict';
  var R = window.Rampa, BODY = window.RAMPA_BODY || { pocet: 24, body: [] };
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  var clamp = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var eur = function (n) { return 'od ' + n + ' €'; };

  var root = document.documentElement, intro = $('uvod'), pin = intro.querySelector('.intro__pin');
  var pas = $('pas'), hlavicka = $('hlavicka'), karta = $('karta');
  var N = BODY.pocet || 24;
  var SMER = { pneumatiky: 'l' };                     // názov bodu vľavo od bodu, ostatné vpravo
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var siroke = window.matchMedia('(min-width:1000px) and (min-aspect-ratio:5/4)');
  var vybrana = null, spustac = null;

  /* ---------- výška pásu ukážky (podľa nej sa pripína hlavička aj scéna) ---------- */
  function merajPas() { root.style.setProperty('--bar', pas.offsetHeight + 'px'); }
  merajPas();
  window.addEventListener('resize', merajPas);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(merajPas);

  /* ---------- služby: zoznam, body na aute, cenník, výber vo formulári ---------- */
  var zoznam = $('zoznam-sluzieb'), body = $('body'), cennik = $('cennik-tabulka'), select = $('f-sluzba');
  var poloha = {};
  BODY.body.forEach(function (b) { poloha[b.id] = b; });

  R.SLUZBY.forEach(function (s, i) {
    var li = el('li'), b = el('button', 'svc');
    b.type = 'button'; b.dataset.id = s.id; b.setAttribute('aria-pressed', 'false'); b.setAttribute('aria-controls', 'karta');
    b.appendChild(el('span', 'svc__n', String(i + 1)));
    b.appendChild(el('span', 'svc__name', s.nazov));
    b.appendChild(el('span', 'svc__price', eur(s.cena)));
    li.appendChild(b); zoznam.appendChild(li);

    var p = poloha[s.id];
    if (p) {
      var sp = el('button', 'spot' + (SMER[s.id] === 'l' ? ' spot--l' : ''));
      sp.type = 'button'; sp.dataset.id = s.id; sp.style.left = p.x + '%'; sp.style.top = p.y + '%'; sp.style.setProperty('--i', i);
      sp.setAttribute('aria-pressed', 'false'); sp.setAttribute('aria-controls', 'karta');
      sp.setAttribute('aria-label', (i + 1) + '. ' + s.nazov + ' – zobraziť službu');
      var dot = el('span', 'spot__dot'); dot.appendChild(el('b', null, String(i + 1)));
      sp.appendChild(dot); sp.appendChild(el('span', 'spot__label', s.nazov));
      body.appendChild(sp);
    }

    var row = el('div', 'prices__row'); row.setAttribute('role', 'row');
    var name = el('span', 'prices__name'); name.setAttribute('role', 'cell');
    var num = el('i', null, String(i + 1)); num.setAttribute('aria-hidden', 'true');
    name.appendChild(num); name.appendChild(document.createTextNode(s.nazov));
    var incl = el('span', 'prices__incl', s.zahrna.join(' · ')); incl.setAttribute('role', 'cell');
    var time = el('span', 'prices__time', s.trvanie); time.setAttribute('role', 'cell');
    var price = el('span', 'prices__price'); price.setAttribute('role', 'cell');
    price.appendChild(el('small', null, 'od')); price.appendChild(document.createTextNode(s.cena + ' €'));
    var cell = el('span'); cell.setAttribute('role', 'cell');
    var ob = el('button', 'btn btn--accent btn--sm', 'Objednať'); ob.type = 'button'; ob.dataset.objednat = s.id;
    ob.setAttribute('aria-label', 'Objednať: ' + s.nazov);
    cell.appendChild(ob);
    [name, incl, time, price, cell].forEach(function (c) { row.appendChild(c); });
    cennik.appendChild(row);

    var o = el('option', null, s.nazov + ' (' + eur(s.cena) + ')'); o.value = s.id; select.appendChild(o);
  });

  function tlacidla(id) { return document.querySelectorAll('.svc[data-id="' + id + '"], .spot[data-id="' + id + '"]'); }
  function vyber(id, odkial) {
    var s = R.sluzba(id); if (!s) return;
    if (vybrana) Array.prototype.forEach.call(tlacidla(vybrana), function (b) { b.setAttribute('aria-pressed', 'false'); });
    vybrana = id; spustac = odkial || null;
    Array.prototype.forEach.call(tlacidla(id), function (b) { b.setAttribute('aria-pressed', 'true'); });
    var i = R.SLUZBY.indexOf(s);
    $('karta-cislo').textContent = 'Služba ' + pad(i + 1) + ' / ' + pad(R.SLUZBY.length);
    $('karta-nazov').textContent = s.nazov;
    $('karta-popis').textContent = s.popis;
    var ul = $('karta-zahrna'); ul.textContent = '';
    s.zahrna.forEach(function (z) { ul.appendChild(el('li', null, z)); });
    $('karta-cena').textContent = s.cena + ' €';
    $('karta-trvanie').textContent = s.trvanie;
    karta.hidden = false; intro.classList.add('has-card');
  }
  function zavriKartu(vratFokus) {
    if (vybrana) Array.prototype.forEach.call(tlacidla(vybrana), function (b) { b.setAttribute('aria-pressed', 'false'); });
    vybrana = null; karta.hidden = true; intro.classList.remove('has-card');
    if (vratFokus && spustac && document.contains(spustac)) spustac.focus({ preventScroll: true });
    spustac = null;
  }
  intro.addEventListener('click', function (e) {
    var b = e.target.closest('.svc, .spot');
    if (!b) return;
    if (vybrana === b.dataset.id && !siroke.matches) { zavriKartu(false); return; }
    vyber(b.dataset.id, b);
  });
  $('karta-zavriet').addEventListener('click', function () { zavriKartu(true); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && vybrana) zavriKartu(true); });
  $('karta-objednat').addEventListener('click', function () { var id = vybrana; if (!siroke.matches) zavriKartu(false); objednat(id); });
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-objednat]');
    if (b) objednat(b.dataset.objednat);
  });
  function objednat(id) {
    if (potvrdenie && !potvrdenie.hidden) novaObjednavka();
    if (id) { select.value = id; chyba('sluzba', ''); }
    $('objednavka').scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
    var ciel = !select.value ? select : (document.querySelector('#dni input:checked') || document.querySelector('#dni input:not(:disabled)') || select);
    window.setTimeout(function () { ciel.focus({ preventScroll: true }); }, reduced.matches ? 0 : 650);
  }

  /* ---------- scéna: zábery podľa skrolovania ---------- */
  var img = $('zaber'), platno = $('platno'), ctx = platno.getContext('2d');
  var zabery = new Array(N), ciel = 0, teraz = 0, nakresleny = -1, bezi = false, postup = 0;
  function cesta(i) { return 'assets/seq/f' + pad(i) + '.webp'; }

  function nacitajZabery() {
    var fronta = [], i;
    for (i = 0; i < N; i++) fronta.push(i);
    function dalsi() {
      if (!fronta.length) return;
      var k = fronta.shift(), im = new Image();
      im.decoding = 'async';
      im.onload = function () { zabery[k] = im; if (k === 0 || Math.abs(k - Math.round(teraz)) < 2) nakresli(true); dalsi(); };
      im.onerror = dalsi;
      im.src = cesta(k);
    }
    dalsi(); dalsi(); dalsi();
  }
  function najblizsi(i) {
    for (var d = 0; d < N; d++) {
      if (zabery[i - d]) return i - d;
      if (zabery[i + d]) return i + d;
    }
    return -1;
  }
  function nakresli(nasilu) {
    var k = najblizsi(Math.round(teraz));
    if (k < 0 || (k === nakresleny && !nasilu)) return;
    ctx.drawImage(zabery[k], 0, 0, platno.width, platno.height);
    nakresleny = k; platno.dataset.zaber = k; platno.classList.add('is-on');
  }
  function krok() {
    var d = ciel - teraz;
    teraz = Math.abs(d) < .02 ? ciel : teraz + d * .22;
    nakresli(false);
    if (teraz !== ciel) window.requestAnimationFrame(krok); else bezi = false;
  }
  function rozsah() { return Math.max(1, intro.offsetHeight - pin.offsetHeight); }
  function prepocitaj() {
    var r = intro.getBoundingClientRect(), bar = pas.offsetHeight;
    postup = clamp((bar - r.top) / rozsah());
    var pf = clamp((postup - .03) / .8);
    ciel = pf * (N - 1);
    intro.style.setProperty('--hero', String(1 - clamp(postup / .15)));
    intro.classList.toggle('is-past', postup > .16);
    var koniec = pf > .985;
    if (koniec !== intro.classList.contains('is-end')) {
      intro.classList.toggle('is-end', koniec);
      if (!koniec && vybrana) zavriKartu(false);
    }
    hlavicka.classList.toggle('is-solid', r.bottom < bar + hlavicka.offsetHeight + 4);
    if (!bezi) { bezi = true; window.requestAnimationFrame(krok); }
  }
  function naKoniec(hladko) {
    var y = window.scrollY + intro.getBoundingClientRect().top - pas.offsetHeight + rozsah() * .93;
    window.scrollTo({ top: y, behavior: hladko && !reduced.matches ? 'smooth' : 'auto' });
  }

  var rezim = null;
  function nastavRezim() {
    var novy = reduced.matches ? 'static' : 'scrolly';
    if (novy === rezim) return;
    rezim = novy;
    intro.classList.toggle('is-scrolly', novy === 'scrolly');
    intro.classList.toggle('is-static', novy === 'static');
    if (novy === 'static') {
      intro.classList.add('is-end'); intro.classList.remove('is-past');
      platno.classList.remove('is-on');
      img.src = cesta(N - 1);                           // bez pohybu: rovno koncový záber s bodmi
      window.removeEventListener('scroll', prepocitaj);
      window.addEventListener('scroll', hlavickaStaticka, { passive: true }); hlavickaStaticka();
    } else {
      window.removeEventListener('scroll', hlavickaStaticka);
      window.addEventListener('scroll', prepocitaj, { passive: true });
      nacitajZabery(); prepocitaj();
    }
  }
  function hlavickaStaticka() { hlavicka.classList.toggle('is-solid', window.scrollY > 8); }
  nastavRezim();
  if (reduced.addEventListener) reduced.addEventListener('change', nastavRezim);
  window.addEventListener('resize', function () { if (rezim === 'scrolly') prepocitaj(); });

  /* odkazy na služby vedú na koniec prechodu kamery; fokus na skryté tlačidlo ich tiež ukáže */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href="#sluzby"]');
    if (a && rezim === 'scrolly') { e.preventDefault(); naKoniec(true); }
    var u = e.target.closest('a[href="#uvod"]');
    if (u) { e.preventDefault(); window.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' }); }
  });
  intro.addEventListener('focusin', function (e) {
    if (rezim === 'scrolly' && !intro.classList.contains('is-end') && e.target.closest('.svc, .spot')) naKoniec(false);
  });

  /* ---------- objednávka ---------- */
  var form = $('formular'), dniBox = $('dni'), casyBox = $('casy'), casInfo = $('cas-info');
  var potvrdenie = $('potvrdenie'), alertBox = $('form-chyby');
  var DNI = R.dni(12);

  function chip(name, value, hlavny, maly, popis) {
    var l = el('label', 'chip'), i = el('input'), s = el('span');
    i.type = 'radio'; i.name = name; i.value = value; if (popis) i.setAttribute('aria-label', popis);
    if (maly) s.appendChild(el('small', null, maly));
    s.appendChild(document.createTextNode(hlavny));
    l.appendChild(i); l.appendChild(s);
    return l;
  }
  function vybranyDen() { var i = dniBox.querySelector('input:checked'); return i ? i.value : ''; }
  function vybranyCas() { var i = casyBox.querySelector('input:checked'); return i ? i.value : ''; }
  function kresliDni() {
    var bol = vybranyDen(), list = R.nacitaj();
    dniBox.textContent = '';
    DNI.forEach(function (d) {
      var volne = R.volneCasy(d, list).length, p = R.fmtDatum(d).split(' ');
      var c = chip('datum', d, p.slice(1).join(' '), volne ? p[0] : 'plno', R.fmtDatum(d, true) + (volne ? '' : ' – obsadené'));
      var inp = c.querySelector('input');
      if (!volne) inp.disabled = true; else if (d === bol) inp.checked = true;
      dniBox.appendChild(c);
    });
  }
  function kresliCasy() {
    var d = vybranyDen(), bol = vybranyCas();
    casyBox.textContent = '';
    if (!d) { casInfo.textContent = 'Najprv vyberte deň.'; return; }
    var list = R.nacitaj(), volne = R.volneCasy(d, list), obs = R.casyDna(d).filter(function (c) { return volne.indexOf(c) < 0; });
    volne.forEach(function (c) {
      var ch = chip('cas', c, c.replace(/^0/, ''), '', c.replace(/^0/, '') + ' hod.');
      if (c === bol) ch.querySelector('input').checked = true;
      casyBox.appendChild(ch);
    });
    casInfo.textContent = 'Voľné časy na ' + R.fmtDatum(d, true) + '.' +
      (obs.length ? ' Obsadené: ' + obs.map(function (c) { return c.replace(/^0/, ''); }).join(', ') + '.' : '');
  }
  dniBox.addEventListener('change', function () { chyba('datum', ''); chyba('cas', ''); kresliCasy(); });
  casyBox.addEventListener('change', function () { chyba('cas', ''); });
  kresliDni(); kresliCasy();

  var POLIA = {
    sluzba: { ciel: function () { return select; } },
    datum: { ciel: function () { return dniBox.querySelector('input:not(:disabled)'); }, box: $('pole-datum') },
    cas: { ciel: function () { return casyBox.querySelector('input') || dniBox.querySelector('input:not(:disabled)'); }, box: $('pole-cas') },
    meno: { ciel: function () { return $('f-meno'); } },
    telefon: { ciel: function () { return $('f-telefon'); } },
    email: { ciel: function () { return $('f-email'); } },
    auto: { ciel: function () { return $('f-auto'); } }
  };
  function chyba(pole, text) {
    var p = $('e-' + pole), def = POLIA[pole], box = def.box || def.ciel();
    p.textContent = text; p.hidden = !text;
    if (box) { if (text) box.setAttribute('aria-invalid', 'true'); else box.removeAttribute('aria-invalid'); }
  }
  function skontroluj() {
    var f = form.elements, ch = {};
    var meno = f.meno.value.trim(), tel = f.telefon.value.trim(), mail = f.email.value.trim(), auto = f.auto.value.trim();
    if (!select.value) ch.sluzba = 'Vyberte službu, na ktorú sa chcete objednať.';
    if (!vybranyDen()) ch.datum = 'Vyberte deň, kedy auto priveziete.';
    if (!vybranyCas()) ch.cas = vybranyDen() ? 'Vyberte jeden z voľných časov.' : 'Vyberte deň a potom čas.';
    if (meno.length < 3) ch.meno = 'Napíšte meno a priezvisko.';
    var cisla = tel.replace(/\D/g, '');
    if (!tel) ch.telefon = 'Napíšte telefónne číslo, na ktoré vám potvrdíme termín.';
    else if (!/^[+\d][\d\s()/-]*$/.test(tel) || cisla.length < 9 || cisla.length > 13) ch.telefon = 'Telefón má mať 9 až 13 číslic, napríklad +421 900 000 000.';
    if (!mail) ch.email = 'Napíšte e-mail, kam pošleme potvrdenie.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(mail)) ch.email = 'E-mail nevyzerá správne. Skúste tvar meno@domena.sk.';
    if (auto.length < 2) ch.auto = 'Napíšte značku a model auta, napríklad Škoda Fabia 2018.';
    return ch;
  }
  ['meno', 'telefon', 'email', 'auto'].forEach(function (k) {
    $('f-' + k).addEventListener('input', function () { if (!$('e-' + k).hidden) chyba(k, ''); });
  });
  select.addEventListener('change', function () { chyba('sluzba', ''); });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var ch = skontroluj(), kluce = Object.keys(POLIA).filter(function (k) { return ch[k]; });
    Object.keys(POLIA).forEach(function (k) { chyba(k, ch[k] || ''); });
    if (kluce.length) {
      alertBox.textContent = '';
      alertBox.appendChild(el('p', null, kluce.length === 1 ? 'Objednávku ešte nemôžeme odoslať. Opravte, prosím, jedno pole:' : 'Objednávku ešte nemôžeme odoslať. Opravte, prosím, tieto polia (' + kluce.length + '):'));
      var ul = el('ul'); kluce.forEach(function (k) { ul.appendChild(el('li', null, ch[k])); });
      alertBox.appendChild(ul); alertBox.hidden = false;
      var prvy = POLIA[kluce[0]].ciel(); if (prvy) prvy.focus();
      return;
    }
    alertBox.hidden = true;
    var f = form.elements;
    var r = R.pridaj({ sluzba: select.value, datum: vybranyDen(), cas: vybranyCas(), meno: f.meno.value.trim(), telefon: f.telefon.value.trim(),
      email: f.email.value.trim(), auto: f.auto.value.trim(), poznamka: f.poznamka.value.trim(), moja: true });
    if (!r) {
      kresliDni(); kresliCasy();
      chyba('cas', 'Tento termín si medzitým rezervoval niekto iný. Vyberte, prosím, iný čas.');
      var c = POLIA.cas.ciel(); if (c) c.focus();
      return;
    }
    ukazPotvrdenie(r);
  });

  function ukazPotvrdenie(r) {
    var s = R.sluzba(r.sluzba);
    $('potvrdenie-nadpis').textContent = 'Rezervácia č. ' + r.id + ' je prijatá';
    $('potvrdenie-text').textContent = 'Ďakujeme, ' + r.meno.split(' ')[0] + '. Termín vám držíme a servis ho potvrdí e-mailom na ' + r.email + '.';
    var dl = $('potvrdenie-udaje'); dl.textContent = '';
    [['Služba', s ? s.nazov : r.sluzba], ['Termín', R.fmtTermin(r.datum, r.cas)], ['Auto', r.auto], ['Telefón', r.telefon]].forEach(function (p) {
      dl.appendChild(el('dt', null, p[0])); dl.appendChild(el('dd', null, p[1]));
    });
    form.hidden = true; potvrdenie.hidden = false;
    kresliMoje();
    potvrdenie.focus({ preventScroll: true });
    potvrdenie.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'center' });
  }
  function novaObjednavka() {
    form.reset(); Object.keys(POLIA).forEach(function (k) { chyba(k, ''); });
    alertBox.hidden = true; form.hidden = false; potvrdenie.hidden = true;
    kresliDni(); kresliCasy();
  }
  $('dalsia').addEventListener('click', function () { novaObjednavka(); select.focus(); });

  /* ---------- vlastné rezervácie zákazníka (v tomto prehliadači) ---------- */
  var moje = $('moje'), mojeZoznam = $('moje-zoznam');
  function kresliMoje() {
    var list = R.nacitaj().filter(function (r) { return r.moja; }).sort(function (a, b) { return b.id - a.id; });
    mojeZoznam.textContent = ''; moje.hidden = !list.length;
    list.forEach(function (r) {
      var s = R.sluzba(r.sluzba), li = el('li', 'mine__item'), info = el('div');
      var tag = el('span', 'tag tag--' + r.stav, R.STAVY[r.stav] || r.stav);
      var nazov = el('strong', null, (s ? s.nazov : r.sluzba) + ' · č. ' + r.id);
      var p = el('p'); p.appendChild(nazov); p.appendChild(document.createTextNode(R.fmtTermin(r.datum, r.cas) + ' · ' + r.auto));
      info.appendChild(tag); info.appendChild(p);
      if (r.stav === 'caka' && r.navrh) info.appendChild(el('p', null, 'Servis navrhuje iný termín: ' + R.fmtTermin(r.navrh.datum, r.navrh.cas) + '.'));
      if (r.poznamkaServisu) info.appendChild(el('p', null, 'Odkaz zo servisu: ' + r.poznamkaServisu));
      li.appendChild(info);
      var acts = el('div', 'mine__acts');
      if (r.stav === 'caka' && r.navrh) {
        var ok = el('button', 'btn btn--dark btn--sm', 'Prijať termín'); ok.type = 'button'; ok.dataset.prijat = r.id; acts.appendChild(ok);
      }
      if (r.stav === 'nova' || r.stav === 'potvrdena' || r.stav === 'caka') {
        var zr = el('button', 'btn btn--line btn--sm', 'Zrušiť rezerváciu'); zr.type = 'button'; zr.dataset.zrusit = r.id; acts.appendChild(zr);
      }
      if (acts.children.length) li.appendChild(acts);
      mojeZoznam.appendChild(li);
    });
  }
  mojeZoznam.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.dataset.prijat) {
      var r = R.nacitaj().filter(function (x) { return x.id === +b.dataset.prijat; })[0];
      if (r && r.navrh) R.zmen(r.id, { datum: r.navrh.datum, cas: r.navrh.cas, navrh: null, stav: 'potvrdena' });
      obnov();
    } else if (b.dataset.zrusit) {
      if (b.dataset.istota) { R.zmen(+b.dataset.zrusit, { stav: 'zrusena', navrh: null }); obnov(); }
      else {                                              // druhé kliknutie potvrdí, odchod z tlačidla zruší
        b.dataset.istota = '1'; b.textContent = 'Naozaj zrušiť?'; b.classList.remove('btn--line'); b.classList.add('btn--dark');
        b.addEventListener('blur', function () { delete b.dataset.istota; b.textContent = 'Zrušiť rezerváciu'; b.classList.add('btn--line'); b.classList.remove('btn--dark'); }, { once: true });
      }
    }
  });
  function obnov() { kresliDni(); kresliCasy(); kresliMoje(); }

  R.vzorove(false);
  obnov();
  window.addEventListener('storage', function (e) { if (e.key === R.KEY) obnov(); });
})();
