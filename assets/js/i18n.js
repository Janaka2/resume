/**
 * EN/DE translations for the main page.
 * English is the default and is captured from the markup itself at boot;
 * German lives in the DE dictionary below, keyed by data-i18n attributes.
 * Same mechanism (and same localStorage keys) as partials/janaka_visual_resume_v3_3.html.
 */
window.JP_I18N = (function () {
  'use strict';

  var DE = {
    /* ---- top bar ---- */
    navExp: 'Erfahrung',
    navProjects: 'Projekte',
    navCerts: 'Zertifizierungen',
    navEdu: 'Ausbildung',
    navJourney: 'Werdegang',
    navContact: 'Kontakt',

    /* ---- hero ---- */
    heroStatus: 'prod · stabil seit 2004 · pikett: getragen · audits: bestanden',
    heroRole: 'Senior Java Engineer &amp; Solution Architect',
    heroHook: '<b>Ich baue grundsolide Enterprise-Java-Systeme — und führe sie ins KI-Zeitalter.</b><br>Über 22 Jahre geschäftskritische Software für Banken und den öffentlichen Sektor — UBS, Credit Suisse und die Europäische Kommission.',
    heroBadges: '<span class="badge">Zug, Schweiz 🇨🇭</span><span class="badge">Niederlassung C</span><span class="badge hot">Deutsch B1 ↗</span><span class="badge">Banking-IT · regulierte Systeme</span><span class="badge hot">KI · LLM · Agentic RAG</span>',
    btnViewCv: 'Mein aktueller Lebenslauf',
    btnEmail: 'E-Mail',
    btnPdf: 'PDF-Lebenslauf',
    heroFigcap: 'ZUG · SCHWEIZ',

    /* ---- about ---- */
    aboutEyebrow: 'Profil',
    aboutH2: 'Bewährte Enterprise-Technologie, praktische KI.',
    aboutP1: 'Ich baue grundsolide Enterprise-Java-Systeme und führe sie ins KI-Zeitalter. Seit über 22 Jahren liefere ich geschäftskritische Software für Banken und den öffentlichen Sektor — mit Fokus auf Automatisierung, die wirklich etwas bewegt: LLMs, RAG, LangChain, CrewAI, LangGraph, AutoGen und das OpenAI Agents SDK mit Spring Boot. Man kennt mich für ruhige, verlässliche Umsetzung: Ich gebe Teams Halt, schaffe Klarheit und liefere Ergebnisse. Von der Modernisierung von Legacy-Systemen bis zur Performance-Optimierung von Handelsplattformen: Ich bringe zu Ende, was ich beginne — ohne Abkürzungen. Heute verbinde ich bewährte Enterprise-Technologie mit praktischer KI zu Lösungen, die in der echten Welt funktionieren. Mein Prinzip ist einfach: Finde einen Weg — oder schaffe einen.',
    aboutP2: '<b>Werte:</b> Innovation, Zusammenarbeit, Verlässlichkeit, kontinuierliches Lernen — und Resultate. Ich verwandle Ideen in skalierbare Lösungen, die das Geschäft voranbringen.',
    academyBtn: 'Janaka Academy beitreten ↗',
    academyP: 'Meine Mission ist es, den Riesen in tausend Herzen zu wecken — und jeden so zu begleiten, dass er mich übertrifft: nicht nur im Engineering, sondern auch in geistiger Tiefe und ethischer Integrität. Schritt für Schritt entsteht so eine Gruppe technischer Vordenker, die mit Mitgefühl innovieren, nach Prinzipien leben und die Welt für alle einfacher machen.',

    /* ---- contact / skills / languages cards ---- */
    cContactH: 'Kontakt',
    cPhone: 'Telefon',
    cSkillsH: 'Kernkompetenzen',
    cSkG1: 'Engineering',
    cSkG2: 'KI / LLM-Engineering',
    cSkC2: '<span class="chip">LangChain</span><span class="chip">LlamaIndex</span><span class="chip">RAG / CAG</span><span class="chip">Agentic Workflows</span><span class="chip">lokale LLMs</span>',
    cSkG3: 'DevOps &amp; Cloud',
    cLangsH: 'Sprachen',
    lgEnN: 'Englisch', lgEnL: 'Verhandlungssicher · <b>C1/C2</b>',
    lgDeN: 'Deutsch', lgDeL: 'Gut · <b>B1 ↗ in aktiver Weiterbildung</b>',
    lgSiN: 'Singhalesisch', lgSiL: 'Muttersprache',
    lgFrN: 'Französisch', lgFrL: 'Grundkenntnisse',
    lgNlN: 'Niederländisch', lgNlL: 'Grundkenntnisse',

    /* ---- experience ---- */
    expEyebrow: 'Erfahrung',
    expH2: '22 Jahre, Production-Grade.',
    expMoreBtn: 'Mehr Details ↓',
    x1when: '<b>01.2024 — heute</b> · Zürich, Schweiz',
    x1pts: '<li>Vollständige Verantwortung für sechs Enterprise-Applikationen durch die Credit-Suisse-UBS-Fusion — Systemstabilität ohne Betriebsunterbrüche, unter hohem Druck.</li><li>Führung der Teams durch Multi-Plattform-Migrationen und Technologie-Decommissioning; Lösung hochpriorisierter Produktionsincidents mit ruhiger, entschlossener Hand.</li><li>Leitung der Archivierungsinitiative: 100 % termingerecht unter auditpflichtigen Fristen; Linux- und Oracle-CLI-Pipelines für regulierte Multi-Gigabyte-Datenfeeds.</li><li>Konzeption und Produktivsetzung von LLM- und Agentic-RAG-Automatisierungen für interne Bankprozesse, integriert in bestehende Java-Services — inklusive lokaler Llama-3-Inferenz für Daten, welche die Bank nicht verlassen dürfen.</li><li>Praxiserfahrung mit dem OpenAI Agents SDK und Model Context Protocol (MCP): Multi-Tool-Orchestrierung, Guardrails und RAG-gestützte Enterprise-Applikationen in Python.</li><li>Mentoring von Junior-Engineers, Leitung von Code-Reviews, Pikettdienst.</li>',
    x2when: '<b>05.2019 — 01.2024</b> · Zürich, Schweiz',
    x2pts: '<li>100 % Ownership für das geschäftskritische Master-Data-Management-Tool, von Grund auf neu gebaut — die Golden Source der Bank für Suche und Reporting.</li><li>Architektur und End-to-End-Lieferung von drei Cloud-native-Applikationen (Spring Boot, React, Oracle, Microservices), darunter eine Web-Applikation für dynamische Consumer-Endpoints und Case-Management-Tools mit Streaming-Integration.</li><li>Front-Office-FX-Handelsplattform mit niedriger Latenz (Java 11–17): ≈20 % mehr Responsiveness durch Multithreading und Memory-Tuning.</li><li>Aufbau der CI/CD-, Kubernetes/Docker- und Observability-Pipelines des Teams; TDD mit JUnit und Mockito.</li>',
    x3when: '<b>01.2018 — 05.2019</b> · Zürich, Schweiz',
    x3pts: '<li>Modernisierung von über 20 Legacy-Komponenten zu Spring-Boot-Microservices mit robusten Lösungsarchitekturen.</li><li>Automatisierung der Jenkins-Pipelines; Migration von SVN zu Git.</li><li>Ausbau der Tests mit JUnit, Integrationstests und Cucumber BDD.</li>',
    x4when: '<b>06.2011 — 01.2018</b> · Brüssel, Belgien',
    x4pts: '<li>Entwicklung und Betrieb des zentralen E-Procurement-Systems der EU — geschäftskritisch, mehrsprachig, öffentlicher Sektor — über 6,5 Jahre; das System trug rund 40 % zum Gesamtumsatz der Abteilung bei.</li><li>Verteilte Integrationsflüsse mit Spring Integration; JBPM-Workflows für Freigaben, Eskalationen und Audit-Trails.</li><li>Full-Stack-Lieferung (Angular, Spring/Hibernate, EJB3, Oracle, WebLogic); Release-Verantwortung und L3-Produktionssupport.</li>',
    x5when: '<b>05.2004 — 06.2011</b> · Belgien &amp; Sri Lanka',
    x5pts: '<li>Technischer Berater in Healthcare, Telekom, Banking und E-Commerce — Enterprise-Java/JEE-Lösungen.</li><li>Union Bank of Colombo: Kernbankenmodule — Kreditsystem, Leasing-Zahlungspläne, Scheck- und Sparbuchdruck (EJB2, JSP, DB2 auf AS/400).</li><li>Architektur-Modernisierung in Agile/Scrum; SOAP/REST-Integration; Optimierung von Oracle/MySQL.</li>',
    whH: 'Berufsweg — die ganze Geschichte',
    whIntro: 'Nach dem Karrierestart in Sri Lanka habe ich über ein Jahrzehnt in Belgien gearbeitet — mit <strong>ABSI</strong>, <strong>Roomsnet.com</strong> und <strong>Simbios</strong> an Projekten für Kunden wie <strong>Van Genechten Packaging</strong>, <strong>Nokia Siemens Networks</strong> und <strong>Johnson &amp; Johnson</strong>. Diese Zeit gab mir breite Erfahrung in Healthcare, Hospitality und Enterprise-IT, bevor ich zur <strong>Europäischen Kommission (DIGIT)</strong> wechselte, um grosse E-Procurement-Systeme zu liefern. Seit 2018 geht meine Reise in der Schweiz weiter — mit Full-Stack-Engineering und KI-Integration bei <strong>Credit Suisse</strong> und <strong>UBS</strong>.',
    whL1: 'Meine Reise begann in Sri Lanka: zuerst als Informatik-Dozent, bald darauf in der Bankenwelt bei der Union Bank. 2006 zog ich nach Belgien — ein prägendes Jahrzehnt des Wachstums in meiner Karriere.',
    whL2: 'Ich arbeitete mit <strong>ABSI</strong> im Gesundheitswesen, später bei <strong>Roomsnet.com</strong> als Java/JEE-Entwickler und Technical Lead in der Hotellerie, und mit <strong>Simbios</strong> an Projekten für Kunden wie <strong>Van Genechten Packaging</strong>, <strong>Nokia Siemens Networks</strong>, <strong>Johnson &amp; Johnson</strong> und <strong>Centric IT Solutions</strong>.',
    whL3: '2011 wechselte ich zur <strong>Europäischen Kommission (DIGIT)</strong> und leitete die Entwicklung robuster E-Procurement-Systeme und komplexer Workflows für die EU.',
    whL4: 'Seit 2018 ist die Schweiz meine Basis — mit <strong>UBS</strong> und <strong>Credit Suisse</strong> im Zentrum: hochperformantes Full-Stack-Engineering, Systemmigrationen und die Integration KI-gestützter Automatisierung.',

    /* ---- independent projects ---- */
    pjEyebrow: 'Eigene Projekte',
    pjH2: 'Zwei Produkte, von der Idee bis in Produktion.',
    pjLede: 'In meiner Freizeit und auf eigener Infrastruktur entstanden — unabhängig von meiner Anstellung und ohne Bezug zum Geschäft meines Arbeitgebers. Beide sind live, und beide sind von Grund auf privat gebaut: Alle Daten bleiben auf dem Gerät der Nutzerin oder des Nutzers.',
    pjLive: 'Live',
    p1Sub: 'nuechtern.app · Fasten-Tracker · PWA',
    p1Desc: 'Ein Fasten-Begleiter, der die Biologie sichtbar macht: ein Timer, der die aktuelle Stoffwechselphase zeigt und sagt, was der Körper in Stunde 14 tatsächlich tut — dazu die Hinweise zu Flüssigkeit und Elektrolyten, die den meisten Trackern fehlen.',
    p1Pts: '<li>Stoffwechsel-Timer, Wasser- und Elektrolyt-Protokoll, Gewichtsverlauf, Serien und Meilensteine.</li><li>Lässt sich auf dem Homescreen installieren und läuft vollständig offline — ohne Konto, ohne Werbung, ohne Tracking.</li><li>Für den deutschsprachigen Markt geschrieben, auf Deutsch und Englisch.</li>',
    p1Chips: '<span class="chip">PWA</span><span class="chip">Offline-first</span><span class="chip">nur auf dem Gerät</span><span class="chip">DE / EN</span>',
    p1Btn: 'nüchtern öffnen ↗',
    p2Sub: 'daily-momentum.com · Zeiterfassung · PWA',
    p2Desc: 'Eine stille Aufzeichnung, wohin der Tag gegangen ist. Ein Tippen sagt, was man gerade tut — es gibt keinen Start- und keinen Stopp-Knopf, denn etwas zu beginnen beendet das Vorherige. Alles andere wird daraus abgeleitet.',
    p2Pts: '<li>Der Tag als ein einziger Streifen, die Woche im Vergleich zur Vorwoche, Muster ausschliesslich aus dem Erfassten.</li><li>Ein vergessener Nachmittag kommt später als Frage zurück statt als Lücke; Einträge lassen sich verschieben, teilen, zusammenführen und umbenennen.</li><li>Kein Konto, kein Server, kein Upload — mit Export als Sicherungsdatei oder Tabelle, jederzeit.</li>',
    p2Chips: '<span class="chip">PWA</span><span class="chip">Offline-first</span><span class="chip">nur auf dem Gerät</span><span class="chip">Datenexport</span>',
    p2Btn: 'Daily Momentum öffnen ↗',
    pjHowLabel: 'Wie sie entstanden sind',
    pjHowH: 'Ein Engineer, KI im Prozess, ausgeliefert.',
    pjHowP: 'Beide Produkte wurden von einer Person spezifiziert, gestaltet, gebaut, getextet und deployed — an Abenden und Wochenenden — mit LLMs als bewusstem Werkzeug in jedem Schritt, nicht als Spielerei. Dieselbe Arbeitsweise bringe ich in regulierte Umgebungen: mit dem Modell schnell vorankommen und das Ergebnis anschliessend an dem Massstab messen, den die Domäne verlangt.',
    pjHowPts: '<li>Produktumfang und Interaktionsflüsse zuerst gegen ein Modell entworfen, danach von Hand gekürzt, bis nur noch bleibt, was seinen Platz verdient.</li><li>Umsetzung in engen Generieren-und-Prüfen-Schleifen — Architektur und Review bleiben bei mir, und nichts geht live, was ich nicht Zeile für Zeile erklären kann.</li><li>Oberflächentexte in zwei Sprachen sowie das visuelle Erscheinungsbild beider Apps KI-gestützt erstellt und auf eine einheitliche Stimme redigiert.</li><li>Von der leeren Seite zur öffentlichen URL in Wochen statt Quartalen — ohne Team, ohne Budget, ohne fremde Hilfe.</li>',
    pjAcqH: 'Beide Produkte könnten ein besseres Zuhause finden.',
    pjAcqP: 'Beide sind unabhängig von meiner Anstellung entstanden und stehen mir daher frei zur Weitergabe. Wenn eines davon in ein Portfolio passt, das Sie aufbauen, spreche ich gerne über Übernahme oder Lizenzierung — Quellcode, Marke, Domain und eine dokumentierte Übergabe.',
    pjAcqBtn: '✉&nbsp; Per E-Mail anfragen',

    /* ---- certifications ---- */
    certEyebrow: 'Zertifizierungen &amp; Kurse',
    certH2: 'Immer am Lernen.',
    certG1: 'Cloud, KI &amp; Automation',
    certG2: 'Java, Spring &amp; Produktivität',
    certG3: 'Daten &amp; SQL',
    certG4: 'Sprachen &amp; Soft Skills',
    certG5: 'Sun-Zertifizierungen (seit 2006)',
    lblInstructor: 'Kursleitung:',
    lblInstructors: 'Kursleitung:',
    lblIssuer: 'Aussteller:',
    lblDone: '✓ 100 % abgeschlossen',
    lblDone98: '98 % abgeschlossen',
    lblDoneDate: 'Abgeschlossen am 21.09.2025',
    lblIssued2006: 'Ausgestellt Jan. 2006',

    /* ---- education ---- */
    eduEyebrow: 'Ausbildung',
    eduH2: 'Qualifikationen.',
    edu1d: 'BSc — Informatik, Statistik &amp; Mathematik',
    edu2d: 'BIT — Bachelor of Information Technology',
    edu2s: '1999 — 2004 · 6 Semester abgeschlossen',
    edu3d: 'Master in Computer Engineering',
    edu3s: '2007 — heute · laufend',

    /* ---- life journey ---- */
    jEyebrow: 'Mein Lebensweg',
    jH2: 'Von Galle nach Zug.',
    jTab1: '👶 Frühe Jahre', jTab2: '🎓 Ausbildung', jTab3: '💼 Karrierestart',
    jTab4: '🇧🇪 Belgien', jTab5: '🇨🇭 Schweiz', jTab6: '🌟 Zukunftspläne',
    j1a: '<h3>Geboren</h3><p class="jw">Februar 1980</p><p>Galle, Sri Lanka</p>',
    j1b: '<h3>Schulzeit</h3><p class="jw">1985 — 1998</p><p>Süden Sri Lankas</p>',
    j2a: '<h3>Bachelor-Abschluss</h3><p class="jw">1999 — 2004</p><p>University of Sri Jayewardenepura</p><p>BSc in Informatik, Statistik, Mathematik</p>',
    j2b: '<h3>Zweiter Bachelor</h3><p class="jw">1999 — 2004</p><p>University of Colombo</p><p>BIT (6 Semester abgeschlossen)</p>',
    j2c: '<h3>Masterstudium</h3><p class="jw">2007 — heute</p><p>University of Moratuwa</p><p>Computer Engineering (laufend)</p>',
    j2d: '<h3>Zertifizierungen</h3><p class="jw">2005 — 2006</p><p>Sun-Java-Zertifizierungen (SCJP, SCBCD, SCEA, SCWCD)</p>',
    j3a: '<h3>Erste Stelle</h3><p class="jw">2004</p><p>Union Bank of Colombo Ltd</p><p>Banking Software Engineer</p>',
    j3b: '<h3>Frühe Karriere</h3><p class="jw">2006 — 2008</p><p>Mehrere Unternehmen in Sri Lanka</p><p>Java/JEE-Entwickler</p>',
    j4a: '<h3>Umzug nach Belgien</h3><p class="jw">August 2008</p><p>Raum Brüssel</p>',
    j4b: '<h3>Hochzeit</h3><p class="jw">2010</p><p>Belgien</p>',
    j4c: '<h3>Erstes Kind</h3><p class="jw">Januar 2012</p><p>Sohn</p>',
    j4d: '<h3>Zweites Kind</h3><p class="jw">Dezember 2013</p><p>Tochter</p>',
    j4e: '<h3>Erstes Eigenheim</h3><p class="jw">Dezember 2015</p><p>Belgien</p>',
    j4f: '<h3>Drittes Kind</h3><p class="jw">Dezember 2016</p><p>Tochter</p>',
    j4g: '<h3>Europäische Kommission</h3><p class="jw">2011 — 2018</p><p>Sr. Full-Stack Java Developer</p><p>E-Procurement-Systeme</p>',
    j5a: '<h3>Umzug in die Schweiz</h3><p class="jw">Januar 2018</p><p>Raum Zürich</p>',
    j5b: '<h3>UBS</h3><p class="jw">2018 — 2019</p><p>IT Solution Development Specialist</p><p>Bankensysteme</p>',
    j5c: '<h3>Remote aus UK</h3><p class="jw">2019 — 2020</p><p>Liverpool, UK</p><p>Remote-Arbeit für Schweizer Kunden</p>',
    j5d: '<h3>Credit Suisse</h3><p class="jw">2019 — 2024</p><p>IT Solution Developer</p><p>Bankensysteme &amp; FX-Handel</p>',
    j5e: '<h3>UBS</h3><p class="jw">2024 — heute</p><p>Senior Full-Stack Solution Engineer (Lead)</p><p>KI-Integration &amp; LLMs</p>',
    j6a: '<h3>Master abschliessen</h3><p class="jw">laufend</p><p>University of Moratuwa</p><p>Computer Engineering</p>',
    j6b: '<h3>KI-Forschung &amp; Entwicklung</h3><p class="jw">Zukunftsziel</p><p>Fortgeschrittene KI-Systeme</p><p>LLM-Optimierung &amp; Deployment</p>',
    j6c: '<h3>Projekte mit globaler Wirkung</h3><p class="jw">Langfristige Vision</p><p>Enterprise-KI-Lösungen</p><p>Skalierbare intelligente Systeme</p>',
    j6d: '<h3>Technologie-Leadership</h3><p class="jw">Karriereziel</p><p>Architektur-Exzellenz</p><p>Mentoring der nächsten Engineer-Generation</p>',
    j6e: '<h3>Start der Janaka Academy</h3><p class="jw">02.11.2025</p><p>1’000+ Engineers weltweit stärken</p><p>Schritt-für-Schritt-Training, damit andere mich übertreffen — technisch und ethisch</p>',
    j6btn: 'Beitreten ↗',

    /* ---- key metrics ---- */
    kmEyebrow: 'Kennzahlen',
    kmH2: 'Zahlen, die halten.',
    km1: 'Jahre Produktions-Java',
    km2: 'Apps durch die CS–UBS-Fusion geführt',
    km3: 'FX-Plattform-Latenz reduziert',
    km4: 'Banken + die EU',

    /* ---- AI assistant CTA + chat ---- */
    ctaH: 'Möchten Sie mehr erfahren?',
    ctaP: 'Chatten Sie mit meinem KI-Assistenten über meine Erfahrung, meine Skills oder meine Verfügbarkeit.',
    ctaBtn: '💬&nbsp; Jetzt chatten',
    chatTitle: 'Chat mit Janakas KI-Assistent',

    /* ---- contact / footer ---- */
    ctEyebrow: 'Kontakt',
    ctH2: 'Mein Postfach ist offen.',
    ctLede: 'Wenn Banking-Grade-Engineering plus praktische KI das Problem auf Ihrem Tisch ist — in der Schweiz oder remote/hybrid in Europa — sprechen wir.',
    ctPS: 'PS — You are very welcome to write in English, too.',
    ctRefs: 'Ausgezeichnete Referenzen von UBS, Credit Suisse und der Europäischen Kommission auf Anfrage.',
    ctExplore: 'Entdecken',
    ctMailBadge: 'Kontakt',
    ctRights: 'Alle Rechte vorbehalten.',
    footRight: 'von Hand gebaut — keine Frameworks, kein Build-Step. Quelltext ansehen.'
  };

  /* Strings used by JS-driven UI (not tied to a data-i18n node) */
  var STR = {
    en: {
      title: 'Janaka Premathilaka — Senior Java Engineer & Solution Architect',
      langBtnAria: 'Auf Deutsch wechseln',
      themeBtnAria: 'Switch between light and dark theme',
      readMore: 'Read more',
      showLess: 'Show less',
      chatClose: 'Close chat',
      pdf: 'partials/Janaka_Premathilaka_CV_2026.pdf'
    },
    de: {
      title: 'Janaka Premathilaka — Senior Java Engineer & Solution Architect (Lebenslauf)',
      langBtnAria: 'Switch to English',
      themeBtnAria: 'Zwischen hellem und dunklem Design wechseln',
      readMore: 'Mehr lesen',
      showLess: 'Weniger anzeigen',
      chatClose: 'Chat schliessen',
      pdf: 'partials/Janaka_Premathilaka_Lebenslauf_2026_DE.pdf'
    }
  };

  /* English is captured from the markup the first time we see each key. */
  var EN = {};
  function capture() {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var k = el.dataset.i18n;
      if (!(k in EN)) EN[k] = el.innerHTML;
    });
  }
  function apply(lang) {
    capture(); // pick up any nodes added since the last run (partials load async)
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var k = el.dataset.i18n;
      if (lang === 'de' && DE[k] !== undefined) el.innerHTML = DE[k];
      else if (EN[k] !== undefined) el.innerHTML = EN[k];
    });
  }

  return { apply: apply, STR: STR };
})();
