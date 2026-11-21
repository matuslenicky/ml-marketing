/* RAMPA 7 – spoločné údaje a úložisko rezervácií pre index.html aj admin.html.
   Ukážka: všetko sa ukladá len do localStorage tohto prehliadača. */
(function () {
  'use strict';
  var KEY = 'rampa7.rezervacie.v1';
  var SEED_KEY = 'rampa7.vzorove.v1';

  var SLUZBY = [
    { id: 'pneumatiky', nazov: 'Prezúvanie pneumatík', kratko: 'Pneumatiky', cena: 29, trvanie: '45 min',
      popis: 'Prezujeme, vyvážime a skontrolujeme. Druhú sadu vám uskladníme do ďalšej sezóny.',
      problemy: ['Prezutie na zimné alebo letné', 'Auto ťahá do strany', 'Volant sa pri rýchlosti trasie', 'Defekt, pneumatika stráca vzduch', 'Ojazdené pneumatiky, chcem nové'],
      zahrna: ['Prezutie a vyváženie štyroch kolies', 'Kontrola dezénu, tlaku a ventilov', 'Dotiahnutie momentovým kľúčom', 'Uskladnenie sady za príplatok'] },
    { id: 'brzdy', nazov: 'Brzdy', kratko: 'Brzdy', cena: 49, trvanie: '1,5 h',
      popis: 'Platničky, kotúče aj kvapalina. Pred výmenou vám ukážeme, koľko materiálu ešte ostáva.',
      problemy: ['Brzdy pískajú alebo škrípu', 'Pedál je mäkký, ide hlboko', 'Pri brzdení sa trasie volant', 'Svieti kontrolka bŕzd', 'Pri brzdení ťahá do strany'],
      zahrna: ['Výmena platničiek a kotúčov', 'Výmena brzdovej kvapaliny', 'Kontrola hadíc a strmeňov', 'Skúšobná jazda po oprave'] },
    { id: 'motor', nazov: 'Motor a olej', kratko: 'Motor a olej', cena: 59, trvanie: '1 h',
      popis: 'Olej a filtre podľa predpisu výrobcu, k tomu prehliadka motora a zápis do servisnej knižky.',
      problemy: ['Pravidelná výmena oleja a filtrov', 'Svieti kontrolka motora alebo oleja', 'Motor stráca výkon', 'Z motora ide zvláštny zvuk', 'Pod autom kvapká olej alebo kvapalina'],
      zahrna: ['Výmena oleja a olejového filtra', 'Vzduchový a palivový filter', 'Kontrola rozvodov a únikov', 'Zápis do servisnej knižky'] },
    { id: 'svetla', nazov: 'Svetlá a elektrika', kratko: 'Svetlá a elektrika', cena: 15, trvanie: '30 min',
      popis: 'Od žiarovky po autobatériu. Svetlomety nastavíme na prístroji, nie od oka.',
      problemy: ['Nesvieti svetlo alebo smerovka', 'Svetlá oslepujú, sú zle nastavené', 'Auto ťažko štartuje (batéria)', 'Nefunguje elektrika (okná, zásuvka)'],
      zahrna: ['Nastavenie svetlometov', 'Výmena žiaroviek a poistiek', 'Test a výmena autobatérie', 'Kontrola nabíjania'] },
    { id: 'klima', nazov: 'Klimatizácia', kratko: 'Klimatizácia', cena: 45, trvanie: '1 h',
      popis: 'Doplníme chladivo, vyčistíme rozvody a vymeníme kabínový filter, aby klíma chladila a nezapáchala.',
      problemy: ['Klimatizácia nechladí', 'Z klímy zapácha', 'Klíma hučí alebo píska', 'Pravidelný servis klimatizácie'],
      zahrna: ['Plnenie chladiva podľa hmotnosti', 'Dezinfekcia výparníka a rozvodov', 'Výmena kabínového filtra', 'Skúška tesnosti okruhu'] },
    { id: 'diagnostika', nazov: 'Diagnostika', kratko: 'Diagnostika', cena: 25, trvanie: '30 min',
      popis: 'Svieti kontrolka? Načítame riadiace jednotky a povieme vám po slovensky, čo auto hlási.',
      problemy: ['Svieti kontrolka na palubnej doske', 'Auto prešlo do núdzového režimu', 'Chyba sa objavuje len občas', 'Kontrola pred kúpou auta'],
      zahrna: ['Načítanie chýb všetkých jednotiek', 'Meranie živých hodnôt', 'Vymazanie uložených závad', 'Protokol s odporúčaním'] },
    { id: 'vyfuk', nazov: 'Výfuk', kratko: 'Výfuk', cena: 35, trvanie: '1 h',
      popis: 'Hrkoce alebo je hlučný? Vymeníme tlmič, spoje aj závesy a skontrolujeme emisie.',
      problemy: ['Výfuk je hlučný alebo hrkoce', 'V aute cítiť výfukové plyny', 'Neprešli emisie pred STK', 'Výfuk je prehrdzavený alebo visí'],
      zahrna: ['Výmena tlmičov a spojov', 'Zváranie a oprava závesov', 'Kontrola lambda sondy', 'Meranie emisií pred STK'] }
  ];

  var NEVIEM = 'Neviem príčinu – opíšem';

  var STAVY = {
    nova: 'Nová', potvrdena: 'Potvrdená', caka: 'Čaká na zákazníka',
    dokoncena: 'Dokončená', zamietnuta: 'Zamietnutá', zrusena: 'Zrušená'
  };

  var CASY_TYZDEN = ['07:30', '09:00', '10:30', '13:00', '14:30', '16:00'];
  var CASY_SOBOTA = ['08:00', '09:30', '11:00'];
  var DNI = ['nedeľa', 'pondelok', 'utorok', 'streda', 'štvrtok', 'piatok', 'sobota'];
  var DNI_KR = ['ne', 'po', 'ut', 'st', 'št', 'pi', 'so'];

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function iso(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function zIso(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function plusDni(d, n) { var x = new Date(d.getFullYear(), d.getMonth(), d.getDate()); x.setDate(x.getDate() + n); return x; }

  function sluzba(id) {
    for (var i = 0; i < SLUZBY.length; i++) if (SLUZBY[i].id === id) return SLUZBY[i];
    return null;
  }
  function casyDna(datum) {
    var d = zIso(datum).getDay();
    return d === 0 ? [] : d === 6 ? CASY_SOBOTA.slice() : CASY_TYZDEN.slice();
  }
  /* Najbližšie dni, keď má servis otvorené (od zajtra, bez nedieľ). */
  function dni(pocet) {
    var out = [], d = plusDni(new Date(), 1);
    while (out.length < pocet) { if (d.getDay() !== 0) out.push(iso(d)); d = plusDni(d, 1); }
    return out;
  }

  var pamat = null;   // náhrada, keď localStorage nie je dostupný (súkromné okno a pod.)
  function nacitaj() {
    try {
      var raw = localStorage.getItem(KEY);
      var list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch (e) { return pamat || []; }
  }
  function uloz(list) {
    pamat = list;
    try { localStorage.setItem(KEY, JSON.stringify(list)); return true; } catch (e) { return false; }
  }
  function noveId(list) {
    var m = 0; for (var i = 0; i < list.length; i++) m = Math.max(m, list[i].id || 0);
    return m + 1;
  }
  function drziTermin(r) { return r.stav === 'nova' || r.stav === 'potvrdena' || r.stav === 'caka' || r.stav === 'dokoncena'; }
  /* Obsadené časy v daný deň. Pri „čaká na zákazníka“ sa drží pôvodný aj navrhnutý termín. */
  function obsadene(datum, list, okremId) {
    var o = {};
    (list || nacitaj()).forEach(function (r) {
      if (r.id === okremId || !drziTermin(r)) return;
      if (r.datum === datum) o[r.cas] = true;
      if (r.stav === 'caka' && r.navrh && r.navrh.datum === datum) o[r.navrh.cas] = true;
    });
    return o;
  }
  function volneCasy(datum, list, okremId) {
    var o = obsadene(datum, list, okremId);
    return casyDna(datum).filter(function (c) { return !o[c]; });
  }
  function pridaj(udaje) {
    var list = nacitaj();
    if (volneCasy(udaje.datum, list).indexOf(udaje.cas) < 0) return null;       // termín medzitým niekto obsadil
    var r = {
      id: noveId(list), stav: 'nova', vytvorene: new Date().toISOString(),
      sluzba: udaje.sluzba, datum: udaje.datum, cas: udaje.cas,
      meno: udaje.meno, telefon: udaje.telefon, email: udaje.email, auto: udaje.auto,
      problem: udaje.problem || '', poznamka: udaje.poznamka || '', poznamkaServisu: '', navrh: null, moja: !!udaje.moja
    };
    list.push(r); uloz(list);
    return r;
  }
  function zmen(id, zmeny) {
    var list = nacitaj(), najdene = null;
    list.forEach(function (r) {
      if (r.id !== id) return;
      for (var k in zmeny) if (Object.prototype.hasOwnProperty.call(zmeny, k)) r[k] = zmeny[k];
      r.zmenene = new Date().toISOString(); najdene = r;
    });
    if (najdene) uloz(list);
    return najdene;
  }
  function vymaz(id) {
    var list = nacitaj(), n = list.length;
    list = list.filter(function (r) { return r.id !== id; });
    uloz(list);
    return list.length < n;
  }

  function fmtDatum(datum, dlhy) {
    var d = zIso(datum);
    return (dlhy ? DNI[d.getDay()] : DNI_KR[d.getDay()]) + ' ' + d.getDate() + '. ' + (d.getMonth() + 1) + '.' + (dlhy ? ' ' + d.getFullYear() : '');
  }
  function fmtTermin(datum, cas) { return fmtDatum(datum, true) + ' o ' + cas.replace(/^0/, ''); }
  function fmtPred(isoCas) {
    var t = new Date(isoCas), min = Math.max(0, Math.round((Date.now() - t.getTime()) / 60000));
    var kedy = t.getDate() + '. ' + (t.getMonth() + 1) + '. ' + t.getHours() + ':' + pad(t.getMinutes());
    var pred = min < 1 ? 'práve teraz' : min < 60 ? 'pred ' + min + ' min' : min < 60 * 24 ? 'pred ' + Math.round(min / 60) + ' h'
      : 'pred ' + Math.round(min / 1440) + (Math.round(min / 1440) === 1 ? ' dňom' : ' dňami');
    return pred + ' (' + kedy + ')';
  }

  /* Vzorové rezervácie, aby administrácia ani kalendár neboli pri prvom otvorení prázdne. */
  function vzorove(znova) {
    try { if (!znova && localStorage.getItem(SEED_KEY)) return false; } catch (e) { if (pamat) return false; }
    var list = nacitaj().filter(function (r) { return !r.vzor; });
    var d = dni(9), teraz = Date.now();
    function volny(datum, chcem) {
      var v = volneCasy(datum, list);
      return v.indexOf(chcem) >= 0 ? chcem : v[0];
    }
    var vzor = [
      { sluzba: 'brzdy', den: d[1], cas: '09:00', stav: 'nova', pred: 12, meno: 'Jana Ukážková', telefon: '+421 000 000 001', email: 'jana.ukazkova@example.com', auto: 'Škoda Octavia 2.0 TDI, 2017', poznamka: 'Pri brzdení píska predná náprava.' },
      { sluzba: 'pneumatiky', den: d[0], cas: '13:00', stav: 'nova', pred: 95, meno: 'Peter Vzorový', telefon: '+421 000 000 002', email: 'peter.vzorovy@example.com', auto: 'Kia Ceed SW, 2020', poznamka: 'Zimné kolesá na diskoch priveziem so sebou.' },
      { sluzba: 'motor', den: d[2], cas: '07:30', stav: 'potvrdena', pred: 60 * 26, meno: 'Marek Príklad', telefon: '+421 000 000 003', email: 'marek.priklad@example.com', auto: 'Volkswagen Golf 1.4 TSI, 2015', poznamka: '', poznamkaServisu: 'Objednaný olej 5W-30 a filtre, prídu v utorok.' },
      { sluzba: 'klima', den: d[3], cas: '10:30', stav: 'caka', pred: 60 * 5, meno: 'Lucia Skúšobná', telefon: '+421 000 000 004', email: 'lucia.skusobna@example.com', auto: 'Hyundai i30, 2019', poznamka: 'Klíma nechladí, len fúka.', navrhDen: d[4], navrhCas: '14:30' },
      { sluzba: 'diagnostika', den: iso(plusDni(new Date(), -2)), cas: '14:30', stav: 'dokoncena', pred: 60 * 24 * 6, meno: 'Tomáš Ukážka', telefon: '+421 000 000 005', email: 'tomas.ukazka@example.com', auto: 'Opel Astra 1.6, 2012', poznamka: 'Svieti kontrolka motora.', poznamkaServisu: 'Chybná zapaľovacia cievka 2. valca, vymenená.' },
      { sluzba: 'vyfuk', den: d[5], cas: '16:00', stav: 'zamietnuta', pred: 60 * 30, meno: 'Eva Testová', telefon: '+421 000 000 006', email: 'eva.testova@example.com', auto: 'Dodávka nad 3,5 t', poznamka: '', poznamkaServisu: 'Vozidlo nad 3,5 t na rampu nezmestíme.' },
      { sluzba: 'svetla', den: d[2], cas: '13:00', stav: 'zrusena', pred: 60 * 50, meno: 'Ján Demo', telefon: '+421 000 000 007', email: 'jan.demo@example.com', auto: 'Dacia Duster, 2021', poznamka: '' }
    ];
    vzor.forEach(function (v) {
      var cas = v.stav === 'zamietnuta' || v.stav === 'zrusena' || v.stav === 'dokoncena' ? v.cas : volny(v.den, v.cas);
      if (!cas) return;
      var r = {
        id: noveId(list), stav: v.stav, vytvorene: new Date(teraz - v.pred * 60000).toISOString(),
        sluzba: v.sluzba, datum: v.den, cas: cas, meno: v.meno, telefon: v.telefon, email: v.email, auto: v.auto,
        poznamka: v.poznamka, poznamkaServisu: v.poznamkaServisu || '', navrh: null, moja: false, vzor: true
      };
      if (v.navrhDen) { var nc = volny(v.navrhDen, v.navrhCas); if (nc) r.navrh = { datum: v.navrhDen, cas: nc }; else r.stav = 'nova'; }
      list.push(r);
    });
    uloz(list);
    try { localStorage.setItem(SEED_KEY, '1'); } catch (e) { /* bez úložiska ostanú len v pamäti */ }
    return true;
  }

  window.Rampa = {
    KEY: KEY, SLUZBY: SLUZBY, STAVY: STAVY,
    sluzba: sluzba, dni: dni, casyDna: casyDna, volneCasy: volneCasy, obsadene: obsadene,
    NEVIEM: NEVIEM, nacitaj: nacitaj, pridaj: pridaj, zmen: zmen, vymaz: vymaz, vzorove: vzorove,
    fmtDatum: fmtDatum, fmtTermin: fmtTermin, fmtPred: fmtPred
  };
})();
