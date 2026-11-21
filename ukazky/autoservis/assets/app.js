/* RAMPA 7 – stránka pre zákazníka: dielňa riadená skrolovaním (auto vyjde na zdvihák), detail každej služby s výberom problému, objednávka termínu. */
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
  var SMER = { pneumatiky: 'l', svetla: 'l' };                   // názov bodu vľavo od bodu, ostatné vpravo
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var siroke = window.matchMedia('(min-width:1000px) and (min-aspect-ratio:5/4)');
  var vybrana = null, spustac = null;

  /* ---------- výška pásu ukážky (podľa nej sa pripína hlavička aj scéna) ---------- */
  function merajPas() { root.style.setProperty('--bar', pas.offsetHeight + 'px'); }
  merajPas();
  window.addEventListener('resize', merajPas);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(merajPas);

  /* ---------- služby: zoznam, body na aute, výber vo formulári ---------- */
  var zoznam = $('zoznam-sluzieb'), body = $('body'), select = $('f-sluzba'), selProblem = $('f-problem');
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

    var o = el('option', null, s.nazov + ' (' + eur(s.cena) + ')'); o.value = s.id; select.appendChild(o);
  });

  /* ---------- detail služby: kamera prejde z auta na diel ---------- */
  var detail = $('detail'), stage = $('scena'), spat = $('spat-auto');
  var ALT = {
    pneumatiky: 'Detail: predné koleso auta a vedľa neho stoh nových pneumatík.',
    brzdy: 'Detail: auto na zdviháku so zloženým zadným kolesom, vidno brzdový kotúč a strmeň.',
    motor: 'Detail: otvorená kapota, motor, olejové veko, autobatéria a nádržka chladiacej kvapaliny.',
    svetla: 'Detail: rozsvietený svetlomet a prístroj na nastavenie svetiel pred autom.',
    klima: 'Detail: otvorená kapota a servisná stanica klimatizácie pripojená hadicami.',
    diagnostika: 'Detail: diagnostický tablet na stojane pri dverách vodiča, na obrazovke zoznam kontrol.',
    vyfuk: 'Detail: auto vysoko na zdviháku, pohľad zospodu na výfuk a tlmič.'
  };
  var nacitane = {};
  function nacitajDetail(id) {
    if (nacitane[id]) return nacitane[id];
    var im = new Image(); im.src = 'assets/det/det-' + id + '.webp';
    return (nacitane[id] = im.decode ? im.decode().catch(function () {}) : Promise.resolve());
  }
  // Dve pružiny (Apple: damping 1): záber auta sa priblíži k dielu, detail dosadne. Obe sa dajú otočiť v polovici.
  var obr = [$('zaber'), $('platno')];
  var dz = new Spring(0, { response: 0.6, damping: 1 });
  dz.onUpdate = function (z) {
    var on = z > 0.0005;
    obr.forEach(function (o) { o.style.transform = on ? 'scale(' + (1 + 0.9 * z).toFixed(4) + ')' : ''; o.style.filter = on ? 'blur(' + (3 * z).toFixed(2) + 'px)' : ''; });
  };
  var din = new Spring(0, { response: 0.55, damping: 1 });
  din.onUpdate = function (e) {
    var k = 1 - e, on = k > 0.0005;
    detail.style.transform = on ? 'scale(' + (1 + 0.22 * k).toFixed(4) + ')' : '';
    detail.style.opacity = on ? Math.min(1, e * 1.6).toFixed(3) : '';
  };
  var detailPre = null;
  function ukazDetail(id) {
    var p = poloha[id], bolo = !detail.hidden, nacitany = false;
    stage.style.setProperty('--ox', (p ? p.x : 50) + '%');
    stage.style.setProperty('--oy', (p ? p.y : 50) + '%');
    intro.classList.add('has-detail');
    spat.hidden = false;
    detailPre = id;
    if (reduced.matches) dz.set(1); else dz.to(1);
    nacitajDetail(id).then(function () { nacitany = true; });
    (function cakaj() {                               // detail nastúpi, keď je auto dosť priblížené a záber načítaný
      if (vybrana !== id || detailPre !== id) return;
      if (!nacitany || (!reduced.matches && dz.x < 0.45)) { requestAnimationFrame(cakaj); return; }
      detail.src = 'assets/det/det-' + id + '.webp';
      detail.alt = ALT[id] || '';
      detail.hidden = false;
      if (reduced.matches) din.set(1); else { din.set(bolo ? Math.min(din.x, 0.4) : 0); din.to(1); }
    })();
  }
  function skryDetail() {
    detailPre = null;
    intro.classList.remove('has-detail');
    spat.hidden = true;
    if (reduced.matches) { din.set(0); detail.hidden = true; dz.set(0); return; }
    din.to(0, { onRest: function () { detail.hidden = true; } });   // späť tou istou cestou
    dz.to(0);
  }

  /* spodný panel karty na mobile: ťahá sa 1:1, pri pustení rozhodne švih (projekcia hybnosti), na hrane mäkko */
  var sheet = new Spring(0, { response: 0.32, damping: 1, eps: 0.5 });
  sheet.onUpdate = function (y) { karta.style.transform = Math.abs(y) > 0.5 ? 'translateY(' + y.toFixed(1) + 'px)' : ''; };
  var tah = null, tahRychlost = new Spring.Tracker();
  function panelRezim() { return rezim === 'scrolly' && !siroke.matches; }
  function zasunPanel(v, potom) {
    if (!panelRezim() || reduced.matches) { potom(); return; }
    sheet.to(karta.offsetHeight + 40, { velocity: v || 0, onRest: function () { potom(); sheet.set(0); } });
  }
  karta.addEventListener('pointerdown', function (e) {
    if (!panelRezim() || !e.target.closest('.card__grab, .card__num, .card__title')) return;
    tah = { id: e.pointerId, y0: e.clientY, base: sheet.x, on: false };
    tahRychlost.reset(); tahRychlost.add(e.clientY);
  });
  karta.addEventListener('pointermove', function (e) {
    if (!tah || e.pointerId !== tah.id) return;
    var dy = e.clientY - tah.y0;
    if (!tah.on) {
      if (Math.abs(dy) < 8) return;
      tah.on = true; tah.y0 = e.clientY - tah.base;
      try { karta.setPointerCapture(e.pointerId); } catch (err) {}
    }
    var y = e.clientY - tah.y0;
    if (y < 0) y = -Spring.rubber(-y, karta.offsetHeight);
    tahRychlost.add(e.clientY);
    sheet.set(y);
  });
  function pustPanel(e) {
    if (!tah || e.pointerId !== tah.id) return;
    var t = tah; tah = null;
    if (!t.on) return;
    var v = tahRychlost.velocity(), y = sheet.x;
    if (y + Spring.project(v) > karta.offsetHeight * 0.45) zasunPanel(v, function () { zavriKartu(true); });
    else sheet.to(0, { velocity: v, damping: Math.abs(v) > 500 ? 0.8 : 1 });
  }
  karta.addEventListener('pointerup', pustPanel);
  karta.addEventListener('pointercancel', pustPanel);

  /* ---------- karta služby s výberom problému ---------- */
  var problemy = $('karta-problemy'), vlastny = $('karta-vlastny'), vlastnyText = $('karta-popis-problemu');
  function kresliProblemy(s) {
    problemy.textContent = '';
    s.problemy.concat([R.NEVIEM]).forEach(function (t) {
      var l = el('label', 'opt' + (t === R.NEVIEM ? ' opt--own' : '')), i = el('input');
      i.type = 'radio'; i.name = 'problem-karta'; i.value = t;
      l.appendChild(i); l.appendChild(el('span', null, t));
      problemy.appendChild(l);
    });
    vlastny.hidden = true; vlastnyText.value = '';
  }
  problemy.addEventListener('change', function (e) {
    var own = e.target.value === R.NEVIEM;
    vlastny.hidden = !own;
    if (own) vlastnyText.focus();
  });
  function vybranyProblem() { var i = problemy.querySelector('input:checked'); return i ? i.value : ''; }

  function tlacidla(id) { return document.querySelectorAll('.svc[data-id="' + id + '"], .spot[data-id="' + id + '"]'); }
  function vyber(id, odkial) {
    var s = R.sluzba(id); if (!s) return;
    if (rezim === 'scrolly' && !intro.classList.contains('is-end')) naKoniec(false);
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
    kresliProblemy(s);
    var bolaOtvorena = !karta.hidden;
    karta.hidden = false; intro.classList.add('has-card');
    karta.scrollTop = 0;
    if (panelRezim() && !bolaOtvorena && !reduced.matches) { sheet.set(karta.offsetHeight); sheet.to(0); } else sheet.set(0);
    ukazDetail(id);
    if (siroke.matches) {                               // bočný panel na desktope: karta s voľbami hneď v zábere
      var bok = karta.parentNode; bok.scrollTo({ top: Math.max(0, karta.offsetTop - 8), behavior: reduced.matches ? 'auto' : 'smooth' });
    }
  }
  function zavriKartu(vratFokus) {
    if (vybrana) Array.prototype.forEach.call(tlacidla(vybrana), function (b) { b.setAttribute('aria-pressed', 'false'); });
    vybrana = null; karta.hidden = true; intro.classList.remove('has-card');
    skryDetail();
    if (vratFokus && spustac && document.contains(spustac)) spustac.focus({ preventScroll: true });
    spustac = null;
  }
  intro.addEventListener('click', function (e) {
    var b = e.target.closest('.svc, .spot');
    if (!b) return;
    if (vybrana === b.dataset.id && !siroke.matches) { zavriKartu(false); return; }
    vyber(b.dataset.id, b);
  });
  intro.addEventListener('pointerover', function (e) { var b = e.target.closest('.svc, .spot'); if (b && e.pointerType === 'mouse') nacitajDetail(b.dataset.id); });
  $('karta-zavriet').addEventListener('click', function () { zasunPanel(0, function () { zavriKartu(true); }); });
  spat.addEventListener('click', function () { zasunPanel(0, function () { zavriKartu(true); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && vybrana) zasunPanel(0, function () { zavriKartu(true); }); });
  $('karta-objednat').addEventListener('click', function () {
    var id = vybrana, pr = vybranyProblem(), text = vlastnyText.value.trim();
    zavriKartu(false);
    objednat(id, pr, text);
  });
  function objednat(id, problem, text) {
    if (potvrdenie && !potvrdenie.hidden) novaObjednavka();
    if (id) { select.value = id; chyba('sluzba', ''); kresliProblemyFormulara(); }
    if (problem) { selProblem.value = problem; podlaProblemu(); }
    if (text) $('f-poznamka').value = text;
    $('objednavka').scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
    var ciel = !select.value ? select : (document.querySelector('#dni input:checked') || document.querySelector('#dni input:not(:disabled)') || select);
    window.setTimeout(function () { ciel.focus({ preventScroll: true }); }, reduced.matches ? 0 : 650);
  }

  /* problém vo formulári: možnosti podľa služby, „neviem príčinu“ zmení poznámku na opis */
  function moznost(text, value) { var o = el('option', null, text); o.value = value; return o; }
  function kresliProblemyFormulara() {
    var s = R.sluzba(select.value), bol = selProblem.value;
    selProblem.textContent = '';
    if (!s) { selProblem.appendChild(moznost('Najprv vyberte službu', '')); selProblem.disabled = true; podlaProblemu(); return; }
    selProblem.disabled = false;
    selProblem.appendChild(moznost('Bez upresnenia', ''));
    s.problemy.concat([R.NEVIEM]).forEach(function (t) { selProblem.appendChild(moznost(t, t)); });
    if (bol && Array.prototype.some.call(selProblem.options, function (o) { return o.value === bol; })) selProblem.value = bol;
    podlaProblemu();
  }
  function podlaProblemu() {
    var own = selProblem.value === R.NEVIEM;
    $('l-poznamka').innerHTML = own ? 'Opíšte, čo sa s autom deje <span class="field__opt">čím viac, tým lepšie</span>' : 'Poznámka <span class="field__opt">nepovinné</span>';
  }
  selProblem.addEventListener('change', podlaProblemu);

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
    intro.classList.toggle('is-moved', postup > .03);
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
      intro.classList.add('is-end', 'is-moved');
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

  /* odkaz na začiatok; fokus na bod alebo službu posunie scénu na koniec prechodu kamery */
  document.addEventListener('click', function (e) {
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
  select.addEventListener('change', function () { chyba('sluzba', ''); kresliProblemyFormulara(); });

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
      email: f.email.value.trim(), auto: f.auto.value.trim(), problem: selProblem.value, poznamka: f.poznamka.value.trim(), moja: true });
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
    [['Služba', s ? s.nazov : r.sluzba], ['Problém', r.problem], ['Termín', R.fmtTermin(r.datum, r.cas)], ['Auto', r.auto], ['Telefón', r.telefon]].filter(function (p) { return p[1]; }).forEach(function (p) {
      dl.appendChild(el('dt', null, p[0])); dl.appendChild(el('dd', null, p[1]));
    });
    form.hidden = true; potvrdenie.hidden = false;
    kresliMoje();
    potvrdenie.focus({ preventScroll: true });
    potvrdenie.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'center' });
  }
  function novaObjednavka() {
    form.reset(); kresliProblemyFormulara(); Object.keys(POLIA).forEach(function (k) { chyba(k, ''); });
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
