// Zoznam odborov v sekcii „Pre koho“. Uprav pole a spusti: node tools/odbory.mjs
// Prepíše v index.html len časť medzi značkami odbory:start a odbory:end.
// Zámerne tu nie sú realitky, developeri ani školské systémy.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const OBLASTI = [
  ['Remeslá a opravy v domácnosti', 'Problém, adresa, fotky a naliehavosť ešte pred výjazdom.', ['Inštalatéri', 'Elektrikári', 'Kúrenári', 'Plynári', 'Klimatizácie', 'Tepelné čerpadlá', 'Fotovoltika', 'Nabíjačky pre elektromobily', 'Maliari', 'Murári', 'Obkladači', 'Podlahári', 'Sadrokartonári', 'Stolári', 'Tesári', 'Pokrývači', 'Klampiari', 'Kominári', 'Zámočníci', 'Havarijné otváranie dverí', 'Hodinoví manželia', 'Opravy spotrebičov', 'Úprava vody', 'Studne a čerpadlá', 'Výťahy', 'Alarmy a kamery', 'Inteligentné domácnosti', 'Garážové brány', 'Odkvapy a žľaby', 'Izolácie', 'Sklenári']],
  ['Výroba a montáž na mieru', 'Rozmery, materiál a fotky pripravené na cenovú ponuku.', ['Kuchyne na mieru', 'Nábytok na mieru', 'Vstavané skrine', 'Okná', 'Dvere', 'Žalúzie a rolety', 'Markízy', 'Pergoly', 'Ploty a brány', 'Zimné záhrady', 'Zasklenie balkónov', 'Schodiská', 'Krby a pece', 'Bazény', 'Sauny na mieru', 'Vírivky', 'Kamenárstvo', 'Kováči', 'CNC obrábanie', 'Laserové rezanie', '3D tlač', 'Reklamné polepy', 'Svetelné reklamy', 'Tlačiarne', 'Potlač textilu', 'Výšivky', 'Krajčírstvo na mieru', 'Čalúnnici', 'Rámovanie obrazov', 'Gravírovanie']],
  ['Stavba, projekt a exteriér', 'Rozsah, pozemok a termín bez kola telefonátov.', ['Stavebné firmy', 'Rekonštrukcie', 'Drevostavby', 'Zateplenie', 'Zemné práce', 'Demolácie', 'Betón a dlažby', 'Asfaltovanie', 'Geodeti', 'Architekti', 'Interiéroví dizajnéri', 'Projektanti', 'Statici', 'Energetické certifikáty', 'Záhradní architekti', 'Záhradníci', 'Kosenie', 'Orez stromov', 'Zavlažovanie', 'Zimná údržba a odhŕňanie snehu', 'Servis bazénov', 'Septiky a žumpy', 'Vianočné osvetlenie domov', 'Poľnohospodárske služby', 'Vinohradnícke služby', 'Lesnícke práce']],
  ['Upratovanie a údržba', 'Plocha, typ práce a pravidelnosť v jednom dopyte.', ['Upratovanie domácností', 'Upratovanie firiem', 'Upratovanie po stavbe', 'Upratovanie apartmánov', 'Tepovanie', 'Čistenie okien', 'Čistenie fasád', 'Čistenie striech', 'Tlakové umývanie', 'Čistenie solárnych panelov', 'Čistenie potrubí', 'Čistenie vzduchotechniky', 'Deratizácia a dezinsekcia', 'Vypratávanie bytov', 'Odvoz odpadu', 'Správa a údržba budov', 'Práčovne', 'Chemické čistiarne', 'Mangľovne', 'Sanácia po požiari a vode', 'Odstraňovanie plesní', 'Odstraňovanie graffiti']],
  ['Auto, moto a doprava', 'Vozidlo, problém a želaný termín ešte pred príchodom.', ['Autoservisy', 'Pneuservisy', 'Karosárne', 'Lakovne', 'Autoklimatizácie', 'Autosklá', 'Autoumyvárne', 'Mobilné umývanie áut', 'Detailing', 'Fólie na autá', 'Autoelektrikári', 'Diagnostika vozidiel', 'STK a emisné kontroly', 'Odťahové služby', 'Autoškoly', 'Motoservisy', 'Servis karavanov', 'Servis nákladných áut', 'Servis poľnohospodárskych strojov', 'Sťahovanie', 'Kuriéri', 'Taxi', 'Letiskové transfery', 'Autobusová doprava', 'Limuzíny', 'Parkoviská na rezerváciu', 'Servis lodí']],
  ['Ubytovanie a pobyty', 'Pobyt, počet hostí a konkrétne miesto v jednej žiadosti.', ['Kempy', 'Karavanové parky', 'Glamping', 'Chaty', 'Penzióny', 'Hotely', 'Butikové hotely', 'Wellness hotely', 'Apartmány', 'Hostely', 'Horské chaty', 'Agroturistika', 'Vinárske pobyty', 'Kúpele', 'Hausbóty', 'Domy na stromoch', 'Rybárske pobyty', 'Poľovnícke pobyty', 'Maríny a kotviská']],
  ['Gastro', 'Čas, počet hostí a stôl bez telefonovania.', ['Reštaurácie', 'Fine dining', 'Bistrá', 'Kaviarne', 'Čajovne', 'Vinárne', 'Pivovary', 'Puby', 'Bary', 'Kokteilové bary', 'Cukrárne a torty na objednávku', 'Pekárne', 'Catering', 'Rozvoz obedov', 'Firemné obedy', 'Súkromní kuchári', 'Degustácie', 'Food trucky']],
  ['Krása a osobná starostlivosť', 'Služba, pracovník a voľný termín v jednom kalendári.', ['Kaderníctva', 'Barbershopy', 'Kozmetické salóny', 'Manikúra', 'Pedikúra', 'Mihalnice a obočie', 'Permanentný make-up', 'Depilácia', 'Soláriá', 'Vizáž', 'Masáže', 'Wellness a spa', 'Verejné sauny', 'Kryoterapia', 'Floating', 'Tetovanie', 'Piercing', 'Odstraňovanie tetovania', 'Osobní stylisti', 'Svadobné účesy']],
  ['Zdravie a terapia', 'Typ návštevy a termín, podrobnosti až na mieste.', ['Súkromné ambulancie', 'Zubári', 'Dentálna hygiena', 'Ortodontisti', 'Očné ambulancie', 'Optiky', 'Fyzioterapia', 'Rehabilitácie', 'Chiropraktici', 'Psychológovia', 'Psychoterapeuti', 'Logopédi', 'Výživoví poradcovia', 'Estetické kliniky', 'Podológovia', 'Načúvacie pomôcky', 'Odberové laboratóriá', 'Domáca ošetrovateľská starostlivosť', 'Opatrovateľské služby', 'Pôrodné asistentky', 'Akupunktúra']],
  ['Zvieratá', 'Zviera, služba a termín bez dopisovania.', ['Veterinári', 'Mobilní veterinári', 'Psie salóny', 'Výcvik psov', 'Psie škôlky', 'Venčenie psov', 'Hotely pre zvieratá', 'Stráženie zvierat', 'Ohradené výbehy pre psov', 'Ustajnenie koní', 'Podkúvači', 'Fyzioterapia zvierat']],
  ['Šport a fitness', 'Kurt, lekcia alebo tréner bez ručného zapisovania.', ['Fitness centrá', 'Osobní tréneri', 'Joga', 'Pilates', 'Crossfit', 'Tanečné štúdiá', 'Bojové umenia', 'Box', 'Tenisové kurty', 'Padel', 'Squash', 'Bedminton', 'Futbalové ihriská', 'Športové haly', 'Športové kluby', 'Plavárne', 'Klziská', 'Lezecké steny', 'Golf', 'Jazdiarne', 'Lyžiarske školy', 'Surfové školy', 'Potápačské centrá', 'Kitesurfing', 'Plachtenie', 'Bowling', 'Biliard', 'Strelnice']],
  ['Zážitky, atrakcie a výlety', 'Dátum, počet ľudí a vstupenka na jednom mieste.', ['Únikové hry', 'Paintball', 'Laser game', 'Motokáry', 'VR herne', 'Detské herne', 'Trampolínové parky', 'Lanové parky', 'Zipline', 'Bobové dráhy', 'Aquaparky', 'Zoo a farmy', 'Múzeá a galérie', 'Hrady a prehliadky', 'Jaskyne', 'Sprievodcovia', 'Mestské prehliadky', 'Vínne túry', 'Gastro túry', 'Horskí vodcovia', 'Splavy a rafting', 'Vyhliadkové plavby', 'Rybárske výlety', 'Jachty', 'Balónové lety', 'Vyhliadkové lety', 'Paragliding', 'Parašutizmus', 'Safari', 'Karaoke', 'Divadlá', 'Komorné kiná']],
  ['Kurzy a vzdelávanie', 'Kurz, úroveň a voľné miesto bez e-mailovania.', ['Jazykové školy', 'Doučovanie', 'Hudobné lekcie', 'Výtvarné kurzy', 'Keramika', 'Kurzy varenia', 'Kurzy šitia', 'Prvá pomoc', 'Rekvalifikácie', 'Firemné školenia', 'Workshopy', 'Plavecké kurzy', 'Letné tábory', 'Detské krúžky', 'Príprava na skúšky', 'Kurzy fotografovania', 'Programovanie pre deti', 'Barmanské kurzy', 'Letecké školy', 'Lodné preukazy']],
  ['Podujatia, foto a kreatíva', 'Dátum, miesto a rozsah podujatia v jednej žiadosti.', ['Fotografi', 'Kameramani', 'Fotoateliéry', 'Nahrávacie štúdiá', 'Svadobné salóny', 'Svadobní koordinátori', 'Organizátori podujatí', 'DJ', 'Kapely', 'Moderátori', 'Kvetinárstva', 'Výzdoba', 'Sály a svadobné priestory', 'Stany a mobiliár', 'Skákacie hrady', 'Ozvučenie a svetlá', 'Fotobúdky', 'Detské oslavy', 'Konferenčné priestory', 'Animátori']],
  ['Požičovne a prenájom', 'Vec, termín a dostupnosť bez dvojitého prenájmu.', ['Náradie', 'Stavebné stroje', 'Plošiny', 'Lešenie', 'Prívesy', 'Požičovne áut', 'Karavany', 'Dodávky', 'Motorky', 'Bicykle', 'Elektrobicykle', 'Kolobežky', 'Lyže a snowboardy', 'Lode a kajaky', 'Paddleboardy', 'Spoločenské šaty', 'Kostýmy', 'Detské pomôcky', 'Foto a video technika', 'Zdravotné pomôcky', 'Coworking', 'Zasadačky', 'Skladové boxy', 'Garáže', 'Ateliéry na prenájom', 'Kuchyne na prenájom']],
  ['Kancelárie a poradenstvo', 'Téma, podklady a termín stretnutia vopred.', ['Účtovníci', 'Daňoví poradcovia', 'Mzdové služby', 'Advokáti', 'Notári', 'Finanční poradcovia', 'Poisťovací agenti', 'Prekladatelia', 'Tlmočníci', 'Personálne agentúry', 'Kouči', 'Mediátori', 'BOZP a požiarna ochrana', 'Revízni technici', 'Súdni znalci', 'Patentoví zástupcovia', 'Konzultanti', 'Imigračné poradenstvo', 'Pohrebné služby']],
  ['Servis a opravy vecí', 'Vec, porucha a stav opravy prehľadne pre zákazníka.', ['Opravy mobilov', 'Opravy počítačov', 'Servis elektroniky', 'Hodinári', 'Zlatníci', 'Opravy obuvi', 'Opravy odevov', 'Servis bicyklov', 'Servis kočíkov', 'Opravy hudobných nástrojov', 'Brúsenie nožov', 'Servis lyží', 'Servis kávovarov', 'Servis šijacích strojov', 'Opravy nábytku', 'Reštaurátori', 'Servis záhradnej techniky', 'Výroba kľúčov', 'IT podpora pre firmy', 'Digitalizácia fotiek']],
];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const nb = (s) => esc(s).replace(/(^|\s)([aiouvzsk])\s/gi, '$1$2&nbsp;');
const key = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

const seen = new Map();
for (const [oblast, , odbory] of OBLASTI) for (const o of odbory) {
  if (seen.has(key(o))) throw new Error(`Duplicita: ${o} (${seen.get(key(o))} / ${oblast})`);
  seen.set(key(o), oblast);
}
const total = seen.size;
const rounded = Math.floor(total / 10) * 10;

const fields = OBLASTI.map(([oblast, note, odbory]) => `        <details class="obl">
          <summary>
            <h3>${nb(oblast)}</h3>
            <span class="obl-note">${nb(note)}</span>
            <span class="obl-n"><span class="obl-c">${odbory.length}</span><i aria-hidden="true"></i><span class="sr"> odborov</span></span>
          </summary>
          <ul class="trades">${odbory.map((o) => `<li>${nb(o)}</li>`).join('')}</ul>
        </details>`).join('\n');

const block = `<!-- odbory:start -->
      <div class="finder">
        <label for="odbor">Nájdite svoj odbor</label>
        <input id="odbor" type="search" placeholder="napríklad kominár, padel, jachty" autocomplete="off" enterkeyhint="search">
        <p id="odbor-stav" role="status">Vyše ${rounded} odborov v&nbsp;${OBLASTI.length} oblastiach</p>
      </div>
      <div class="fields">
${fields}
      </div>
      <p class="fields-more">Váš odbor tu nie je? <a href="#kontakt">Napíšte nám</a>, čo robíte. Ak riešite dopyty alebo termíny, základ bude rovnaký.</p>
      <!-- odbory:end -->`;

const file = fileURLToPath(new URL('../index.html', import.meta.url));
const html = readFileSync(file, 'utf8');
const re = /<!-- odbory:start -->[\s\S]*?<!-- odbory:end -->/;
if (!re.test(html)) throw new Error('V index.html chýbajú značky odbory:start/end');
writeFileSync(file, html.replace(re, () => block));
console.log(`${total} odborov v ${OBLASTI.length} oblastiach`);
