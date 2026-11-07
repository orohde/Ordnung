/* Ordnung! – web UI (vanilla JS, Fundamental Styles) */
'use strict';

// ------------------------------------------------------------------ i18n

const I18N = {
  de: {
    'login.user': 'Benutzer', 'login.pass': 'Passwort', 'login.submit': 'Anmelden',
    'login.error': 'Anmeldung fehlgeschlagen.', 'app.logout': 'Abmelden',
    'search.placeholder': 'Suchen …', 'list.recursive': 'mit Unterordnern',
    'list.empty': 'Keine Dokumente.', 'list.more': 'Mehr laden',
    'col.date': 'Datum', 'col.title': 'Titel', 'col.area': 'Bereich',
    'pv.open': 'Öffnen', 'pv.download': 'Herunterladen',
    'pv.none': 'Für diesen Dateityp gibt es keine Vorschau.',
    'pv.bottom': 'Lesebereich unten anzeigen', 'pv.right': 'Lesebereich rechts anzeigen',
    'pv.lay.bottom': 'Unten', 'pv.lay.right': 'Rechts', 'pv.trash': 'Löschen', 'pv.meta': 'Titel und Datum ändern', 'pv.gofolder': 'Im Ordnerbaum zeigen',
    'mp.title': 'Mappen', 'mp.new': 'Neue Mappe', 'mp.new.q': 'Name der neuen Mappe (z. B. Steuererklärung 2026):',
    'mp.zip': 'ZIP herunterladen', 'mp.pdf': 'Als eine PDF', 'mp.linked': 'verknüpft', 'mp.in': 'liegt in',
    'mp.out': 'Aus der Mappe nehmen', 'mp.added': '{n} Dokument(e) in „{name}“ aufgenommen.', 'mp.removed': 'Aus „{name}“ genommen.',
    'mp.rename': 'Bearbeiten …', 'mp.edit': 'Mappe bearbeiten', 'mp.delete': 'Mappe auflösen',
    'mp.name': 'Name', 'mp.name.ph': 'z. B. Steuererklärung 2026', 'mp.area': 'Gehört zu',
    'mp.area.hint': 'Sehen kann die Mappe nur, wer diesen Bereich lesen darf. Hineinlegen darf, wer dort schreiben darf.',
    'mp.delete.q': 'Mappe „{name}“ auflösen? Die Dokumente bleiben, wo sie sind, sie verlieren nur das Etikett.',
    'mp.empty': 'Noch keine Mappe. Mit + anlegen, dann Dokumente darauf ziehen.',
    'st.trash': 'Papierkorb', 'st.trash.days': 'Endgültig löschen nach', 'st.trash.unit': 'Tagen',
    'st.trash.hint': 'Gelöschte Dokumente liegen im Papierkorb (.papierkorb im Archiv). Nach dieser Frist löscht Ordnung! sie einmal am Tag endgültig. 0 heißt: nie.',
    'tr.rule': 'Dokumente werden {n} Tage nach dem Löschen endgültig entfernt (einstellbar unter Einstellungen → Ablage).',
    'tr.rule0': 'Der Papierkorb wird nie automatisch geleert (einstellbar unter Einstellungen → Ablage).',
    'tr.left': 'noch {n} Tag(e)', 'tr.today': 'wird heute entfernt',
    'tr.link': '🗑 Papierkorb', 'tr.title': 'Papierkorb', 'tr.deleted': 'Gelöscht', 'tr.from': 'Lag in',
    'tr.intro': 'Gelöschte Dokumente. „Wiederherstellen“ legt ein Dokument an seinen alten Platz zurück.',
    'acc.lang': 'Sprache', 'acc.lang.hint': 'Gilt für dieses Konto auf allen Geräten.',
    'tr.empty': 'Der Papierkorb ist leer.', 'tr.view': 'Ansehen', 'tr.restore': 'Wiederherstellen',
    'tr.restored': '„{title}“ liegt wieder in {folder}.',
    'fo.menu': 'Ordner bearbeiten', 'fo.new': 'Neuer Unterordner …', 'fo.newtop': 'Neuer Ordner …', 'fo.rename': 'Umbenennen oder verschieben …',
    'fo.delete': 'Ordner löschen', 'fo.new.q': 'Name des neuen Ordners in „{folder}“:', 'fo.newtop.q': 'Name des neuen Ordners:',
    'fo.rename.q': 'Neuer Name. Mit „/“ lässt sich der Ordner auch verschieben (z. B. Versicherungen/Cosmos/KFZ):',
    'fo.delete.q': 'Ordner „{folder}“ und seine leeren Unterordner löschen?', 'fo.notempty': 'Nur leere Ordner lassen sich löschen.',
    'fo.renamed': 'Umbenannt. {rules} Regel(n) angepasst.',
    'op.trashed': '„{title}“ liegt im Papierkorb.', 'op.undo': 'Rückgängig', 'op.restored': 'Wiederhergestellt.',
    'op.moved': '{n} Dokument(e) nach „{folder}“ verschoben.', 'op.moved.fail': '{n} nicht verschoben: {err}',
    'op.drag': '{n} Dokument(e)',
    'tree.all': 'Alle Ordner', 'tree.root': 'Hauptordner', 'tree.expand': 'Alle aufklappen', 'tree.collapse': 'Alle zuklappen', 'list.search': 'Suche',
    'snd.tab': 'Absender', 'snd.tab.expert': 'Ordner (Experten)', 'snd.title': 'Absender',
    'snd.side': 'Wer dir schreibt und wohin die Post kommt. Ordnung! lernt beim Ablegen mit und fragt dich, ob es sich etwas merken soll.',
    'snd.intro': 'Wer dir schreibt und in welchem Ordner seine Post liegt.',
    'snd.search': 'Absender suchen …', 'snd.docs': '{n} Dok.', 'snd.rename': 'Umbenennen', 'snd.own': 'Das ist meine eigene Adresse',
    'snd.own.q': '„{name}“ ({domain}) ist eine eigene Adresse und soll nie als Absender gelten?',
    'snd.propose': 'Regel vorschlagen', 'snd.propose.none': 'Dafür findet Ordnung! kein eindeutiges Merkmal – Post von {name} sieht hier aus wie anderswo.',
    'snd.more': '+ {n} weitere Ordner', 'snd.none': 'Keine Absender gefunden.',
    'grade.green': 'sicher', 'grade.yellow': 'meistens', 'grade.red': 'rät oder weiß es nicht',
    'learn.q': 'Soll Ordnung! sich das merken? Künftig automatisch:<br><b>{label}</b> → <b>{folder}</b>',
    'learn.meta': 'Passt auf {n} abgelegte Dokumente in diesem Ordner und auf keine anderen.',
    'learn.meta0': 'Neuer Absender – bisher keine anderen Dokumente von ihm.',
    'learn.name': 'Absender heißt', 'learn.yes': 'Ja, künftig so', 'learn.no': 'Nein',
    'learn.done': 'Gemerkt: {label} → {folder}.', 'learn.examples': 'Zum Beispiel:',
    'src.learned': 'gelernt',
    'tags.title': 'Tags', 'tags.ph': 'Tag …', 'tags.new': '+ Tag', 'tags.add': 'Tag hinzufügen', 'tags.remove': 'Tag entfernen',
    'tags.clearsel': 'Auswahl aufheben', 'tags.selall': 'Alle auswählen', 'tags.sel': '{n} ausgewählt',
    'tags.filter': 'Tag', 'tags.done': '{n} Dokument(e) geändert.', 'tags.del': 'Tag entfernen',
    'status.docs': '{n} Dokumente', 'status.scan': 'eingelesen {t}', 'status.scanning': 'liest ein …',
    'count.of': '{n} von {total}', 'area.none': '(ohne)',
    'status.texts': 'Texte {done}/{total}',
    'set.title': 'Einstellungen', 'set.account': 'Mein Konto', 'set.users': 'Benutzer', 'set.system': 'System',
    'set.ai': 'KI', 'set.back': '← Zurück zum Archiv', 'set.storage': 'Ablage',
    'st.intro': 'Wo das Archiv liegt und aus welchen Ordnern neue Dokumente kommen. Zur Auswahl stehen die Ordner, die dem Container zur Verfügung stehen.',
    'st.inbox.note': 'Aktive Eingangsordner werden jede Minute gelesen (auch Unterordner). Neue Dokumente erscheinen im Posteingang und werden erst nach deiner Bestätigung abgelegt.',
    'ib.up': "⬆ Hochladen",
    'ib.up.title': "PDFs, Fotos (auch direkt mit der iPhone-Kamera) oder Word-Dateien in den Posteingang laden",
    'ib.up.combine.q': "{n} Dateien zu einem Dokument zusammenfassen, z. B. die Seiten eines Briefs?\n\nOK = ein Dokument, Abbrechen = jede Datei einzeln.",
    'ib.up.busy': "Lade {n} Datei(en) hoch …",
    'ib.up.done': "{n} Dokument(e) im Posteingang.",
    'st.area.new': "Neuer Bereich",
    'st.area.name.ph': "Kurzname, z. B. haus",
    'st.area.label.ph': "Anzeigename, z. B. Haus Musterweg",
    'st.area.add': "Bereich anlegen",
    'st.area.hint2': "Ein Bereich ist ein Hauptordner im Archiv und muss keinem Konto gehören. Wer ihn sehen oder befüllen darf, legst du danach unter Benutzer fest.",
    'st.area.added': "Bereich „{name}“ angelegt. Rechte vergibst du unter Einstellungen → Benutzer.",
    'st.area.del': "Leeren Bereich entfernen",
    'st.area.del.q': "Leeren Bereich „{name}“ entfernen?",
    'err.invalid area name': "Kurzname: Kleinbuchstaben, Ziffern, Punkt, Binde- oder Unterstrich.",
    'err.area exists': "Diesen Bereich gibt es schon.",
    'err.area contains documents': "In diesem Bereich liegen Dokumente, er lässt sich nicht entfernen.",
    'ib.title': 'Posteingang', 'ib.short': 'Eingang', 'ib.s.new': 'Zu erledigen', 'ib.s.filed': 'Abgelegt (Original im Eingang)',
    'ib.s.dismissed': 'Verworfen', 'ib.rescan': 'Eingang neu lesen', 'ib.agree': 'Übereinstimmende ablegen',
    'ib.agree.hint': 'Legt alles ab, bei dem Regel und Eingangsordner dasselbe sagen.',
    'ib.agree.q': '{n} Dokumente ablegen, bei denen Regel und Eingangsordner übereinstimmen?',
    'ib.agree.done': '{n} abgelegt.', 'ib.agree.none': 'Nichts, bei dem Regel und Eingangsordner übereinstimmen.',
    'ib.summary': '{new} zu erledigen · {reading} in Texterkennung · {filed} abgelegt', 'ib.folder': 'Ordner', 'ib.name': 'Dateiname',
    'ib.ai': 'KI fragen', 'ib.ai.dlg.cancel': 'Abbrechen', 'ib.ai.pick': 'Welche Anweisung?', 'ib.ai.pick.hint': 'Pfeiltasten wählen, Enter fragt die KI.', 'ib.ai.pick.edit': 'Anweisungen bearbeiten',
    'ai.prompts': 'Anweisungen für „KI fragen“', 'ai.prompts.hint': 'Im Posteingang wählst du eine davon aus, die Standard-Anweisung ist vorausgewählt. Dateiname, Ordnerliste, Dokumenttext und Antwortformat hängt Ordnung! selbst an.',
    'ai.prompts.add': 'Neue Anweisung', 'ai.prompts.name': 'Name, z. B. „Erikas Arztpost“', 'ai.prompts.std': 'Standard', 'ai.prompts.tpl': 'Vorlage einsetzen',
    'ai.prompts.tpl.ask': 'Den Text durch die mitgelieferte Vorlage ersetzen?', 'ai.prompts.del': 'Löschen', 'ai.prompts.last': 'Eine Anweisung muss bleiben.', 'ib.ai.run': 'KI denkt nach …', 'ib.ai.done': 'KI-Vorschlag übernommen ({cost} $).',
    'ib.delete': 'Löschen', 'ib.delete.q': '„{name}“ endgültig löschen? Die Datei verschwindet aus dem Eingangsordner und lässt sich nicht zurückholen.',
    'err.cannot delete': 'Die Datei ließ sich nicht löschen (Eingangsordner schreibgeschützt?).',
    'ib.dismiss': 'Verwerfen', 'ib.undismiss': 'Zurückholen', 'ib.file': 'Ablegen', 'ib.filed': 'Abgelegt unter {path}.',
    'ib.learn': 'Kein passende Regel gefunden – für diesen Ordner Regeln vorschlagen lassen?',
    'ib.learn.link': 'Zu den Regeln',
    'ib.reading': 'Text wird gelesen …', 'ib.nosugg': 'kein Vorschlag', 'ib.dup': 'schon im Archiv',
    'ib.dup.long': 'Diese Datei liegt schon im Archiv: {path}', 'ib.dup.force': 'Trotzdem ablegen',
    'ib.src.rule': 'Regel', 'ib.src.folder': 'Eingangsordner', 'ib.src.ai': 'KI',
    'ib.why.rule': 'Regel: {conds}', 'ib.why.folder': 'Liegt im Eingang unter „{folder}“.', 'ib.why.ai': 'KI: {reason}',
    'ib.why.none': 'Weder eine Regel noch der Eingangsordner geben einen Hinweis. Ordner selbst wählen oder die KI fragen.',
    'ib.conflict': 'Die Hinweise sind sich nicht einig – bitte prüfen.',
    'ib.ro': 'Das Archiv ist nur lesend eingehängt (die Paperless-Originale). Ablegen geht erst, wenn unter Einstellungen → Ablage auf ein frisches Archiv umgestellt ist.',
    'ib.noinbox': 'Es ist noch kein Eingangsordner aktiv. Unter Einstellungen → Ablage einen anlegen und auf „aktiv“ setzen.',
    'ib.empty': 'Nichts im Eingang. Neue Dateien erscheinen hier spätestens nach einer Minute.',
    'ib.pick': 'Wähle links ein Dokument.', 'ib.text': '{pages} Seiten · {method}', 'ib.text.none': 'kein Text erkannt',
    'ib.area.pick': '– Bereich wählen –',
    'err.archive is read-only for filing': 'Das Archiv ist nur lesend eingehängt – Ablegen geht erst nach der Umstellung auf ein frisches Archiv.',
    'err.unknown area': 'Bitte einen Bereich wählen.', 'err.title missing': 'Bitte einen Titel eingeben.',
    'err.invalid date': 'Bitte ein gültiges Datum eingeben.', 'err.no text yet': 'Der Text ist noch nicht gelesen.',
    'err.area excluded from AI': 'Dieser Bereich darf nicht an die KI gehen.', 'err.file changed – please reload': 'Die Datei hat sich geändert – bitte neu laden.',
    'err.already in the archive': 'Diese Datei liegt schon im Archiv: {path}',
    'st.ref': 'Lernbestand', 'st.ref.none': 'kein Lernbestand',
    'st.ref.hint': 'Bereits sortierte Dokumente, an denen die Regeln gemessen und gelernt werden – zum Beispiel die alten Paperless-Originale. Wird nur gelesen und erscheint nicht im Archiv.',
    'st.switch': 'Mit frischem Archiv neu anfangen', 'st.switch.path': 'Neues Archiv', 'st.switch.go': 'Archiv umstellen …',
    'st.switch.hint': 'Das jetzige Archiv wird zum Lernbestand, der gewählte Ordner zum neuen, beschreibbaren Archiv. Regeln und Ordnerbeschreibungen ziehen auf die Ordnernamen aus dem Import-Plan um, die Zielordner des Plans werden als Ordnervorlage angelegt. Auf der Platte wird nichts kopiert, verschoben oder gelöscht.',
    'st.switch.q': 'Archiv auf {new} umstellen?\n\n{old} wird zum Lernbestand (nur lesend). Das Archiv ist danach leer, bis Dokumente über den Posteingang hineinkommen.',
    'st.switch.ok': 'Umgestellt: {rules} Regeln auf neue Ordnernamen umgezogen, {folders} Vorlagenordner angelegt.',
    'err.new archive folder must be writable': 'Der neue Archivordner muss beschreibbar sein.',
    'err.choose a different absolute folder': 'Bitte einen anderen, vollständigen Pfad wählen.',
    'err.old and new archive must not overlap': 'Altes und neues Archiv dürfen nicht ineinander liegen.',
    'err.learning set folder not readable': 'Der Lernbestand ist nicht vorhanden oder nicht lesbar.',
    'err.learning set and archive must not overlap': 'Lernbestand und Archiv dürfen nicht ineinander liegen.',
    'ai.inboxauto': 'Posteingang: KI automatisch fragen, wenn weder Regel noch Eingangsordner weiterhelfen',
    'rules.ref': 'Lernbestand',
    'imp.title': 'Import', 'imp.intro': 'Hier wird nur geplant, wohin jeder Ordner beim Import kommt. Es wird nichts kopiert oder verschoben.',
    'imp.f.todo': 'Hinweise und Änderungen', 'imp.f.open': 'Noch offen', 'imp.f.all': 'Alle Ordner', 'imp.search': 'Ordner suchen …',
    'imp.confirmall': 'Alle bestätigen', 'imp.preview': 'Zielstruktur', 'imp.confirm': 'Bestätigen', 'imp.reset': 'Vorschlag',
    'imp.toparent': 'In übergeordneten Ordner', 'imp.docs': '{n} Dok.', 'imp.ok': 'bestätigt', 'imp.empty': 'Nichts zu tun in dieser Ansicht.',
    'imp.k.docs': 'Dokumente', 'imp.k.before': 'Ordner bisher', 'imp.k.after': 'Ordner danach', 'imp.k.moves': 'Ordner ändern sich',
    'imp.k.noarea': 'Dok. ohne Bereich', 'imp.k.open': 'noch offen',
    'imp.r.double': 'doppelte Ebene zusammengefasst', 'imp.r.spelling': 'Schreibweise vereinheitlicht',
    'imp.h.no_area': 'ohne Bereich – bitte zuordnen', 'imp.h.single': 'nur 1 Dokument', 'imp.h.scattered': 'gleicher Name auch unter: {list}',
    'imp.confirmall.q': 'Alle Zuordnungen so bestätigen, wie sie gerade stehen – auch die nicht angezeigten? (Ordner ohne Bereich bleiben offen.)',
    'rules.title': 'Regeln', 'rules.intro': 'Wähle links einen Ordner. Regeln ordnen neue Dokumente später automatisch ein; jede Regel wird gegen den vorhandenen Bestand geprüft.',
    'rules.summary': '{n} Regeln in {f} Ordnern', 'rules.card': 'Beschreibung des Ordners', 'rules.card.hint': 'Freiwillig: ein, zwei Sätze, was in diesen Ordner gehört. Hilft der KI beim Einsortieren und dir später beim Wiederfinden.',
    'rules.desc.ph': 'z. B. Wohngebäudeversicherung: Versicherungsschein, Beitragsrechnungen, Schadensmeldungen',
    'rules.rules': 'Regeln', 'rules.new': 'Neue Regel', 'rules.addcond': '+ Bedingung (und)', 'rules.test': 'Gegen Bestand prüfen',
    'rules.none': 'Noch keine Regeln für diesen Ordner.', 'rules.suggest': 'Vorschläge', 'rules.suggest.run': 'Vorschläge ermitteln',
    'rules.suggest.hint': 'Gesucht wird ohne KI: Kennungen und Wörter, die in diesem Ordner häufig und anderswo (fast) nie vorkommen.',
    'rules.suggest.none': 'Keine eindeutigen Merkmale gefunden.', 'rules.suggest.busy': 'Suche …',
    'rules.nodocs': 'Dieser Ordner enthält selbst keine Dokumente, nur Unterordner. Regeln und Vorschläge gehören in die Unterordner.',
    'err.folder has no documents of its own': 'Dieser Ordner enthält selbst keine Dokumente, nur Unterordner.',
    'rules.gen': 'Regeln aus dem Bestand erzeugen',
    'rules.gen.q': 'Für jeden Ordner mit mindestens 2 Dokumenten bis zu 3 Regeln erzeugen, die keinen einzigen Ausreißer haben (ohne KI, kostenlos). Ordner mit vorhandenen Regeln werden übersprungen. Das dauert einige Minuten. Starten?',
    'rules.gen.run': 'Läuft: {done} von {total} Ordnern, {rules} Regeln …',
    'rules.gen.done': 'Fertig: {rules} Regeln für {fwr} Ordner, sie erfassen {covered} Dokumente.',
    'src.starter': 'Standard', 'rules.starter': 'Standardregeln übernehmen',
    'rules.starter.q': 'Die mitgelieferten Standardregeln an deinem Bestand messen und jede in den Ordner legen, in dem sie ihre Dokumente findet? Regeln, die nirgends gut passen, werden weggelassen. Bitte prüfen – gemessen heißt nicht immer sinnvoll:',
    'rules.starter.done': '{added} Standardregeln übernommen, {skipped} passten nirgends gut genug.',
    'src.auto': 'automatisch', 'src.ai': 'KI', 'src.suggestion': 'Vorschlag', 'src.manual': 'eigene',
    'rules.ai.run': 'KI-Vorschläge', 'rules.ai.busy': 'Die KI liest Beispieldokumente und schlägt Regeln vor …',
    'rules.ai.meta': '{model} · {samples} Beispieldokumente · {seconds} s · {cost} $',
    'rules.ai.none': 'Die KI hat keine brauchbaren Regeln gefunden.',
    'err.no documents that may be sent to the AI': 'In diesem Ordner liegen nur Dokumente aus Bereichen, die nicht an die KI gehen dürfen.',
    'err.AI is disabled': 'KI ist in den Einstellungen nicht eingeschaltet.',
    'rules.take': 'Übernehmen', 'rules.adapt': 'Anpassen', 'rules.docs': '{n} Dokumente', 'rules.and': 'und',
    'rules.stats': '{inside} von {total} im Ordner', 'rules.out': '{n} außerhalb', 'rules.out0': '0 außerhalb ✓',
    'rules.outliers': 'Würde auch erfassen:', 'rules.missed': 'Nicht erfasst:', 'rules.active': 'aktiv',
    'rules.delete.q': 'Regel wirklich löschen?', 'rules.saved': 'Gespeichert.',
    'cond.contains': 'Text enthält', 'cond.id': 'Kennung (Leerzeichen egal)', 'cond.regex': 'Regulärer Ausdruck',
    'err.condition too short (min. 3 characters)': 'Eine Bedingung braucht mindestens 3 Zeichen.',
    'err.a rule needs at least one condition': 'Eine Regel braucht mindestens eine Bedingung.',
    'fo.intro': 'Die Ordnerstruktur gilt für alle Bereiche. Ein Ordner entsteht in einem Bereich erst, wenn dort das erste Dokument hineinkommt – leere Ordner siehst du nur hier, bei den Regeln und beim Import.',
    'fo.readonly': 'Das Archiv ist nur lesend eingehängt: Ordner mit Dokumenten lassen sich erst nach dem Import umbenennen oder verschieben. Leere Ordner gehen immer.',
    'set.folders': 'Ordner', 'fo.new.ph': 'Neuer Ordner, z. B. Auto/T-Roc/Versicherung', 'fo.add': 'Anlegen',
    'fo.starter': 'Startvorlage „Haushalt“', 'fo.starter.q': 'Rund 40 übliche Haushaltsordner (Banken, Versicherungen, Gesundheit …) anlegen? Vorhandene bleiben unverändert.',
    'fo.starter.ok': '{n} Ordner angelegt.', 'fo.added': 'Ordner angelegt.', 'fo.sub': '+ Unterordner', 'fo.rename': 'Umbenennen / verschieben',
    'fo.delete': 'Löschen', 'fo.delete.q': 'Leeren Ordner „{name}“ samt leerer Unterordner löschen?', 'fo.docs': '{n} Dok.', 'fo.empty': 'leer',
    'fo.renamed': 'Umbenannt. {rules} Regeln mitgenommen.', 'fo.sub.ph': 'Name des Unterordners',
    'err.folder exists': 'Diesen Ordner gibt es schon.', 'err.folder contains documents': 'In diesem Ordner liegen Dokumente, er kann nicht gelöscht werden.',
    'err.archive is read-only': 'Das Archiv ist nur lesend eingehängt – Ordner mit Dokumenten lassen sich erst nach dem Import umbenennen.',
    'err.cannot move a folder into itself': 'Ein Ordner kann nicht in sich selbst verschoben werden.', 'err.empty folder name': 'Bitte einen Namen eingeben.',
    'st.areas': 'Bereiche', 'st.areas.hint': 'Anzeigename je Bereich. Leer lassen = Anzeigename des gleichnamigen Kontos bzw. der Ordnername.',
    'st.archive': 'Archivordner', 'st.path': 'Pfad', 'st.browse': 'Durchsuchen', 'st.inboxes': 'Eingangsordner',
    'st.add': 'Eingangsordner hinzufügen', 'st.name': 'Name', 'st.area': 'Bereich', 'st.area.none': 'beim Einsortieren wählen',
    'st.enabled': 'aktiv', 'st.after': 'Nach dem Einsortieren', 'st.after.move': 'Original nach „_importiert“ verschieben',
    'st.after.keep': 'Original im Eingang lassen', 'st.remove': 'Entfernen',
    'st.ok.rw': 'vorhanden · lesbar · beschreibbar', 'st.ok.ro': 'vorhanden · nur lesbar', 'st.missing': 'nicht vorhanden oder nicht lesbar',
    'st.files': '{n} Dateien darin', 'st.saved': 'Gespeichert.', 'st.choose': 'Diesen Ordner wählen', 'st.up': 'eine Ebene höher',
    'st.roots': 'Verfügbare Ordner', 'st.nodirs': 'keine Unterordner',
    'err.archive folder not readable': 'Der Archivordner ist nicht vorhanden oder nicht lesbar.',
    'err.inbox and archive must not overlap': 'Eingang und Archiv dürfen nicht ineinander liegen.',
    'err.absolute path required': 'Bitte einen vollständigen Pfad angeben (beginnt mit /).',
    'ai.intro': 'Die KI macht nur Vorschläge. Einsortiert wird nach geprüften Regeln oder nach deiner Bestätigung.',
    'ai.enabled': 'KI-Vorschläge verwenden', 'ai.provider': 'Anbieter', 'ai.openai': 'Anderer OpenAI-kompatibler Server', 'ai.ollama': 'Ollama (eigener Server)',
    'ai.baseurl': 'Server-Adresse', 'ai.model': 'Modell', 'ai.key': 'API-Schlüssel', 'ai.clearkey': 'Entfernen',
    'ai.limit': 'Monatslimit (USD)', 'ai.exclude': 'Nie an die KI senden', 'ai.test': 'Verbindung testen',
    'ai.key.set': 'gespeichert ({hint}) – leer lassen = unverändert', 'ai.key.none': 'noch kein Schlüssel hinterlegt',
    'ai.key.local': 'bei lokalen Servern meist nicht nötig',
    'ai.price': '{input} $ / {output} $ je 1 Mio. Token (Eingabe / Ausgabe)', 'ai.price.none': 'Preis unbekannt – Verbrauch wird nur in Token gezählt',
    'ai.usage': '{month}: {cost} $ verbraucht, {calls} Anfragen', 'ai.saved': 'Gespeichert.',
    'ai.testing': 'Teste …', 'ai.test.ok': 'Antwort von {model} in {seconds} s: „{text}“ ({cost} $)',
    'err.no API key': 'Es ist kein API-Schlüssel hinterlegt.', 'err.API key rejected': 'Der API-Schlüssel wurde abgelehnt.',
    'err.monthly limit reached': 'Das Monatslimit ist erreicht.', 'err.no server address': 'Es fehlt die Server-Adresse.',
    'err.cannot reach the Anthropic API': 'Die Anthropic-API ist nicht erreichbar.',
    'err.unknown model': 'Das Modell „{model}“ kennt der Anbieter nicht.',
    'err.not an Anthropic key': 'Das ist kein Anthropic-Schlüssel (er beginnt mit sk-ant-). Hat ein Passwortmanager das Feld gefüllt?',
    'ai.other': 'Anderes Modell eingeben …', 'ai.reload': 'Liste neu laden',
    'ai.models.loading': 'Frage verfügbare Modelle ab …', 'ai.models.live': '{n} Modelle vom Anbieter abgefragt',
    'ai.models.builtin': 'Eingebaute Liste – Abfrage beim Anbieter nicht möglich: {reason}',
    'acc.who': 'Angemeldet als {name}', 'acc.old': 'Aktuelles Passwort', 'acc.new': 'Neues Passwort',
    'acc.change': 'Passwort ändern', 'acc.ok': 'Passwort geändert.',
    'usr.new': 'Neuer Benutzer', 'usr.edit': 'Benutzer {name} bearbeiten', 'usr.name': 'Benutzer',
    'usr.display': 'Anzeigename', 'usr.pass': 'Passwort', 'usr.pass.keep': 'leer lassen = unverändert',
    'usr.role': 'Rolle', 'usr.areas': 'Bereiche', 'usr.admin': 'Administrator (sieht alle Bereiche, darf Einstellungen ändern)',
    'usr.adminrole': 'Admin', 'usr.userrole': 'Benutzer', 'usr.all': 'alle', 'usr.none': 'keine',
    'usr.delete.q': 'Benutzer {name} wirklich löschen?', 'usr.saved': 'Gespeichert.',
    'perm.none': 'kein Zugriff', 'perm.read': 'lesen', 'perm.write': 'lesen + schreiben',
    'btn.cancel': 'Abbrechen', 'btn.save': 'Speichern', 'btn.edit': 'Bearbeiten', 'btn.delete': 'Löschen',
    'sys.version': 'Version', 'sys.docs': 'Dokumente', 'sys.scan': 'Zuletzt eingelesen', 'sys.texts': 'Texte erkannt',
    'sys.ocr': 'Seiten per Texterkennung', 'sys.ocrstate': 'Texterkennung (OCR)', 'sys.on': 'aktiv', 'sys.off': 'nicht verfügbar',
    'sys.err.title': "Dokumente ohne lesbaren Text",
    'sys.err.hint': "Diese Dokumente lassen sich öffnen, nur ihr Text fehlt in der Volltextsuche. Über Titel und Ordner findest du sie trotzdem.",
    'sys.err.password': "mit Passwort geschützt – den Text kann Ordnung! nicht lesen",
    'sys.err.missing': "Datei fehlte beim Lesen – wird neu versucht",
    'sys.err.damaged': "Datei beschädigt oder kein gültiges PDF",
    'sys.err.other': "Unbekannter Fehler",
    'sys.err.retry': "Erneut lesen",
    'sys.err.retried': "{n} Dokument(e) werden neu gelesen.",
    'sys.errors': 'Fehler beim Lesen', 'sys.mode': 'Archiv', 'sys.readonly': 'nur lesend', 'sys.writable': 'beschreibbar',
    'sys.rescan': 'Ordner jetzt neu einlesen', 'sys.rescan.ok': 'Einlesen gestartet.',
    'err.user exists': 'Diesen Benutzer gibt es schon.', 'err.invalid user name': 'Nur Kleinbuchstaben, Ziffern, . _ - erlaubt.',
    'err.last administrator': 'Der letzte Administrator kann nicht entfernt werden.',
    'err.wrong password': 'Aktuelles Passwort stimmt nicht.', 'err.cannot delete yourself': 'Du kannst dich nicht selbst löschen.',
    'err.cannot remove your own admin role': 'Die eigene Admin-Rolle kann man nicht abgeben.',
  },
  en: {
    'login.user': 'User', 'login.pass': 'Password', 'login.submit': 'Sign in',
    'login.error': 'Sign-in failed.', 'app.logout': 'Sign out',
    'search.placeholder': 'Search …', 'list.recursive': 'include subfolders',
    'list.empty': 'No documents.', 'list.more': 'Load more',
    'col.date': 'Date', 'col.title': 'Title', 'col.area': 'Area',
    'pv.open': 'Open', 'pv.download': 'Download',
    'pv.none': 'No preview for this file type.',
    'pv.bottom': 'Show reading pane below', 'pv.right': 'Show reading pane on the right',
    'pv.lay.bottom': 'Below', 'pv.lay.right': 'Right', 'pv.trash': 'Delete', 'pv.meta': 'Change title and date', 'pv.gofolder': 'Show in the folder tree',
    'mp.title': 'Collections', 'mp.new': 'New collection', 'mp.new.q': 'Name of the new collection (e.g. Tax return 2026):',
    'mp.zip': 'Download ZIP', 'mp.pdf': 'As one PDF', 'mp.linked': 'linked', 'mp.in': 'stored in',
    'mp.out': 'Remove from collection', 'mp.added': 'Added {n} document(s) to “{name}”.', 'mp.removed': 'Removed from “{name}”.',
    'mp.rename': 'Edit …', 'mp.edit': 'Edit collection', 'mp.delete': 'Dissolve collection',
    'mp.name': 'Name', 'mp.name.ph': 'e.g. Tax return 2026', 'mp.area': 'Belongs to',
    'mp.area.hint': 'Only people who may read this area see the collection. Adding needs write access there.',
    'mp.delete.q': 'Dissolve collection “{name}”? The documents stay where they are, they only lose the label.',
    'mp.empty': 'No collection yet. Create one with +, then drag documents onto it.',
    'st.trash': 'Trash', 'st.trash.days': 'Delete for good after', 'st.trash.unit': 'days',
    'st.trash.hint': 'Deleted documents go to the trash (.papierkorb in the archive). After this period Ordnung! deletes them for good, once a day. 0 means never.',
    'tr.rule': 'Documents are removed for good {n} days after deletion (Settings → Storage).',
    'tr.rule0': 'The trash is never emptied automatically (Settings → Storage).',
    'tr.left': '{n} day(s) left', 'tr.today': 'removed today',
    'tr.link': '🗑 Trash', 'tr.title': 'Trash', 'tr.deleted': 'Deleted', 'tr.from': 'Was in',
    'tr.intro': 'Deleted documents. “Restore” puts a document back where it was.',
    'acc.lang': 'Language', 'acc.lang.hint': 'For this account, on all devices.',
    'tr.empty': 'The trash is empty.', 'tr.view': 'View', 'tr.restore': 'Restore',
    'tr.restored': '“{title}” is back in {folder}.',
    'fo.menu': 'Edit folder', 'fo.new': 'New subfolder …', 'fo.newtop': 'New folder …', 'fo.rename': 'Rename or move …',
    'fo.delete': 'Delete folder', 'fo.new.q': 'Name of the new folder in “{folder}”:', 'fo.newtop.q': 'Name of the new folder:',
    'fo.rename.q': 'New name. Use “/” to move the folder as well (e.g. Insurance/Cosmos/Car):',
    'fo.delete.q': 'Delete folder “{folder}” and its empty subfolders?', 'fo.notempty': 'Only empty folders can be deleted.',
    'fo.renamed': 'Renamed. {rules} rule(s) updated.',
    'op.trashed': '“{title}” moved to the trash.', 'op.undo': 'Undo', 'op.restored': 'Restored.',
    'op.moved': 'Moved {n} document(s) to “{folder}”.', 'op.moved.fail': '{n} not moved: {err}',
    'op.drag': '{n} document(s)',
    'tree.all': 'All folders', 'tree.root': 'Main folder', 'tree.expand': 'Expand all', 'tree.collapse': 'Collapse all', 'list.search': 'Search',
    'snd.tab': 'Senders', 'snd.tab.expert': 'Folders (experts)', 'snd.title': 'Senders',
    'snd.side': 'Who writes to you and where their post goes. Ordnung! learns while you file and asks whether to remember it.',
    'snd.intro': 'Who writes to you and which folder their post is in.',
    'snd.search': 'Search senders …', 'snd.docs': '{n} docs', 'snd.rename': 'Rename', 'snd.own': 'This is my own address',
    'snd.own.q': 'Is “{name}” ({domain}) your own address that should never count as a sender?',
    'snd.propose': 'Suggest a rule', 'snd.propose.none': 'No distinctive feature found – post from {name} looks here like elsewhere.',
    'snd.more': '+ {n} more folders', 'snd.none': 'No senders found.',
    'grade.green': 'sure', 'grade.yellow': 'mostly', 'grade.red': 'guessing or unknown',
    'learn.q': 'Shall Ordnung! remember this? From now on automatically:<br><b>{label}</b> → <b>{folder}</b>',
    'learn.meta': 'Fits {n} filed documents in this folder and none elsewhere.',
    'learn.meta0': 'New sender – no other documents from them yet.',
    'learn.name': 'Sender is called', 'learn.yes': 'Yes, from now on', 'learn.no': 'No',
    'learn.done': 'Remembered: {label} → {folder}.', 'learn.examples': 'For example:',
    'src.learned': 'learned',
    'tags.title': 'Tags', 'tags.ph': 'Tag …', 'tags.new': '+ tag', 'tags.add': 'Add tag', 'tags.remove': 'Remove tag',
    'tags.clearsel': 'Clear selection', 'tags.selall': 'Select all', 'tags.sel': '{n} selected',
    'tags.filter': 'Tag', 'tags.done': '{n} document(s) changed.', 'tags.del': 'Remove tag',
    'status.docs': '{n} documents', 'status.scan': 'scanned {t}', 'status.scanning': 'scanning …',
    'count.of': '{n} of {total}', 'area.none': '(none)',
    'status.texts': 'Texts {done}/{total}',
    'set.title': 'Settings', 'set.account': 'My account', 'set.users': 'Users', 'set.system': 'System',
    'set.ai': 'AI', 'set.back': '← Back to the archive', 'set.storage': 'Storage',
    'st.intro': 'Where the archive lives and which folders new documents come from. You can pick from the folders available to the container.',
    'st.inbox.note': 'Active inbox folders are read every minute (including subfolders). New documents show up in the inbox and are only filed after you confirm.',
    'ib.up': "⬆ Upload",
    'ib.up.title': "Upload PDFs, photos (straight from the iPhone camera, too) or Word files into the inbox",
    'ib.up.combine.q': "Combine {n} files into one document, e.g. the pages of a letter?\n\nOK = one document, Cancel = each file on its own.",
    'ib.up.busy': "Uploading {n} file(s) …",
    'ib.up.done': "{n} document(s) in the inbox.",
    'st.area.new': "New area",
    'st.area.name.ph': "Short name, e.g. house",
    'st.area.label.ph': "Display name, e.g. House Sample Road",
    'st.area.add': "Create area",
    'st.area.hint2': "An area is a top folder in the archive and does not have to belong to an account. Who may see or fill it is set afterwards under Users.",
    'st.area.added': "Area “{name}” created. Grant rights under Settings → Users.",
    'st.area.del': "Remove empty area",
    'st.area.del.q': "Remove the empty area “{name}”?",
    'err.invalid area name': "Short name: lowercase letters, digits, dot, hyphen or underscore.",
    'err.area exists': "This area already exists.",
    'err.area contains documents': "This area holds documents and cannot be removed.",
    'ib.title': 'Inbox', 'ib.short': 'Inbox', 'ib.s.new': 'To do', 'ib.s.filed': 'Filed (original left in the inbox)',
    'ib.s.dismissed': 'Dismissed', 'ib.rescan': 'Read inbox again', 'ib.agree': 'File matching ones',
    'ib.agree.hint': 'Files everything where rule and inbox folder agree.',
    'ib.agree.q': 'File {n} documents where rule and inbox folder agree?',
    'ib.agree.done': '{n} filed.', 'ib.agree.none': 'Nothing where rule and inbox folder agree.',
    'ib.summary': '{new} to do · {reading} being read · {filed} filed', 'ib.folder': 'Folder', 'ib.name': 'File name',
    'ib.ai': 'Ask AI', 'ib.ai.dlg.cancel': 'Cancel', 'ib.ai.pick': 'Which instruction?', 'ib.ai.pick.hint': 'Arrow keys choose, Enter asks the AI.', 'ib.ai.pick.edit': 'Edit instructions',
    'ai.prompts': 'Instructions for "Ask AI"', 'ai.prompts.hint': 'In the inbox you pick one of them, the default is preselected. Ordnung! adds the file name, the folder list, the document text and the answer format itself.',
    'ai.prompts.add': 'New instruction', 'ai.prompts.name': 'Name, e.g. "Erika\'s doctor letters"', 'ai.prompts.std': 'Default', 'ai.prompts.tpl': 'Insert template',
    'ai.prompts.tpl.ask': 'Replace the text with the built-in template?', 'ai.prompts.del': 'Delete', 'ai.prompts.last': 'One instruction has to stay.', 'ib.ai.run': 'AI is thinking …', 'ib.ai.done': 'AI suggestion applied ({cost} $).',
    'ib.delete': 'Delete', 'ib.delete.q': 'Delete “{name}” for good? The file is removed from the inbox folder and cannot be brought back.',
    'err.cannot delete': 'The file could not be deleted (inbox folder read-only?).',
    'ib.dismiss': 'Dismiss', 'ib.undismiss': 'Bring back', 'ib.file': 'File', 'ib.filed': 'Filed as {path}.',
    'ib.learn': 'No matching rule – let Ordnung! suggest rules for this folder?', 'ib.learn.link': 'To the rules',
    'ib.reading': 'Reading text …', 'ib.nosugg': 'no suggestion', 'ib.dup': 'already filed',
    'ib.dup.long': 'This file is already in the archive: {path}', 'ib.dup.force': 'File anyway',
    'ib.src.rule': 'Rule', 'ib.src.folder': 'Inbox folder', 'ib.src.ai': 'AI',
    'ib.why.rule': 'Rule: {conds}', 'ib.why.folder': 'Sits in the inbox under “{folder}”.', 'ib.why.ai': 'AI: {reason}',
    'ib.why.none': 'Neither a rule nor the inbox folder give a hint. Choose a folder or ask the AI.',
    'ib.conflict': 'The hints disagree – please check.',
    'ib.ro': 'The archive is mounted read-only (the Paperless originals). Filing works once you switch to a fresh archive under Settings → Storage.',
    'ib.noinbox': 'No inbox folder is active yet. Add one under Settings → Storage and set it to “active”.',
    'ib.empty': 'The inbox is empty. New files show up here within a minute.',
    'ib.pick': 'Pick a document on the left.', 'ib.text': '{pages} pages · {method}', 'ib.text.none': 'no text recognised',
    'ib.area.pick': '– choose area –',
    'err.archive is read-only for filing': 'The archive is mounted read-only – filing works after switching to a fresh archive.',
    'err.unknown area': 'Please choose an area.', 'err.title missing': 'Please enter a title.',
    'err.invalid date': 'Please enter a valid date.', 'err.no text yet': 'The text has not been read yet.',
    'err.area excluded from AI': 'This area must not be sent to the AI.', 'err.file changed – please reload': 'The file changed – please reload.',
    'err.already in the archive': 'This file is already in the archive: {path}',
    'st.ref': 'Learning set', 'st.ref.none': 'no learning set',
    'st.ref.hint': 'Documents sorted already, used to measure and learn rules – e.g. the old Paperless originals. Only read, never shown in the archive.',
    'st.switch': 'Start over with a fresh archive', 'st.switch.path': 'New archive', 'st.switch.go': 'Switch archive …',
    'st.switch.hint': 'The current archive becomes the learning set, the chosen folder the new, writable archive. Rules and folder descriptions move to the folder names of the import plan, the plan\'s target folders become template folders. Nothing is copied, moved or deleted on disk.',
    'st.switch.q': 'Switch the archive to {new}?\n\n{old} becomes the learning set (read-only). The archive is empty afterwards until documents come in through the inbox.',
    'st.switch.ok': 'Switched: {rules} rules moved to new folder names, {folders} template folders added.',
    'err.new archive folder must be writable': 'The new archive folder must be writable.',
    'err.choose a different absolute folder': 'Please choose a different, full path.',
    'err.old and new archive must not overlap': 'Old and new archive must not be inside each other.',
    'err.learning set folder not readable': 'The learning set folder is missing or not readable.',
    'err.learning set and archive must not overlap': 'Learning set and archive must not be inside each other.',
    'ai.inboxauto': 'Inbox: ask the AI automatically when neither a rule nor the inbox folder helps',
    'rules.ref': 'learning set',
    'imp.title': 'Import', 'imp.intro': 'This only plans where each folder goes on import. Nothing is copied or moved.',
    'imp.f.todo': 'Hints and changes', 'imp.f.open': 'Still open', 'imp.f.all': 'All folders', 'imp.search': 'Search folders …',
    'imp.confirmall': 'Confirm all', 'imp.preview': 'Target structure', 'imp.confirm': 'Confirm', 'imp.reset': 'Suggestion',
    'imp.toparent': 'Into parent folder', 'imp.docs': '{n} docs', 'imp.ok': 'confirmed', 'imp.empty': 'Nothing to do in this view.',
    'imp.k.docs': 'Documents', 'imp.k.before': 'Folders now', 'imp.k.after': 'Folders after', 'imp.k.moves': 'Folders change',
    'imp.k.noarea': 'Docs without area', 'imp.k.open': 'still open',
    'imp.r.double': 'doubled level merged', 'imp.r.spelling': 'spelling unified',
    'imp.h.no_area': 'no area – please assign', 'imp.h.single': 'only 1 document', 'imp.h.scattered': 'same name also under: {list}',
    'imp.confirmall.q': 'Confirm all mappings as they stand – including those not shown? (Folders without an area stay open.)',
    'rules.title': 'Rules', 'rules.intro': 'Pick a folder on the left. Rules will file new documents automatically later; every rule is checked against the existing archive.',
    'rules.summary': '{n} rules in {f} folders', 'rules.card': 'Folder description', 'rules.card.hint': 'Optional: one or two sentences on what belongs here. Helps the AI when filing and you when searching later.',
    'rules.desc.ph': 'e.g. Home insurance: policy, premium invoices, claims',
    'rules.rules': 'Rules', 'rules.new': 'New rule', 'rules.addcond': '+ condition (and)', 'rules.test': 'Check against archive',
    'rules.none': 'No rules for this folder yet.', 'rules.suggest': 'Suggestions', 'rules.suggest.run': 'Find suggestions',
    'rules.suggest.hint': 'No AI involved: identifiers and words that are frequent in this folder and (almost) never elsewhere.',
    'rules.suggest.none': 'No distinctive features found.', 'rules.suggest.busy': 'Searching …',
    'rules.nodocs': 'This folder holds no documents of its own, only subfolders. Rules and suggestions belong to the subfolders.',
    'err.folder has no documents of its own': 'This folder holds no documents of its own, only subfolders.',
    'rules.gen': 'Create rules from the archive',
    'rules.gen.q': 'Create up to 3 rules for every folder with at least 2 documents, without a single outsider (no AI, free). Folders that already have rules are skipped. This takes a few minutes. Start?',
    'rules.gen.run': 'Running: {done} of {total} folders, {rules} rules …',
    'rules.gen.done': 'Done: {rules} rules for {fwr} folders, covering {covered} documents.',
    'src.starter': 'standard', 'rules.starter': 'Adopt standard rules',
    'rules.starter.q': 'Measure the shipped standard rules against your archive and put each one into the folder where it finds its documents? Rules that fit nowhere well are left out. Please check – measured does not always mean sensible:',
    'rules.starter.done': '{added} standard rules adopted, {skipped} did not fit anywhere well enough.',
    'src.auto': 'automatic', 'src.ai': 'AI', 'src.suggestion': 'suggestion', 'src.manual': 'own',
    'rules.ai.run': 'AI suggestions', 'rules.ai.busy': 'The AI reads sample documents and proposes rules …',
    'rules.ai.meta': '{model} · {samples} sample documents · {seconds} s · {cost} $',
    'rules.ai.none': 'The AI found no usable rules.',
    'err.no documents that may be sent to the AI': 'This folder only holds documents from areas that must not be sent to the AI.',
    'err.AI is disabled': 'AI is not switched on in the settings.',
    'rules.take': 'Accept', 'rules.adapt': 'Adjust', 'rules.docs': '{n} documents', 'rules.and': 'and',
    'rules.stats': '{inside} of {total} in the folder', 'rules.out': '{n} outside', 'rules.out0': '0 outside ✓',
    'rules.outliers': 'Would also catch:', 'rules.missed': 'Not caught:', 'rules.active': 'active',
    'rules.delete.q': 'Really delete this rule?', 'rules.saved': 'Saved.',
    'cond.contains': 'Text contains', 'cond.id': 'Identifier (spaces ignored)', 'cond.regex': 'Regular expression',
    'err.condition too short (min. 3 characters)': 'A condition needs at least 3 characters.',
    'err.a rule needs at least one condition': 'A rule needs at least one condition.',
    'fo.intro': 'The folder structure is shared by all areas. A folder appears in an area only with its first document – empty folders show up here, in the rules and in the import only.',
    'fo.readonly': 'The archive is mounted read-only: folders with documents can be renamed or moved after the import. Empty folders always work.',
    'set.folders': 'Folders', 'fo.new.ph': 'New folder, e.g. Car/Insurance', 'fo.add': 'Create',
    'fo.starter': 'Starter template “Household”', 'fo.starter.q': 'Create about 40 common household folders (banks, insurance, health …)? Existing ones stay unchanged.',
    'fo.starter.ok': '{n} folders created.', 'fo.added': 'Folder created.', 'fo.sub': '+ Subfolder', 'fo.rename': 'Rename / move',
    'fo.delete': 'Delete', 'fo.delete.q': 'Delete the empty folder “{name}” and its empty subfolders?', 'fo.docs': '{n} docs', 'fo.empty': 'empty',
    'fo.renamed': 'Renamed. {rules} rules moved along.', 'fo.sub.ph': 'Name of the subfolder',
    'err.folder exists': 'This folder already exists.', 'err.folder contains documents': 'This folder holds documents and cannot be deleted.',
    'err.archive is read-only': 'The archive is mounted read-only – folders with documents can be renamed after the import.',
    'err.cannot move a folder into itself': 'A folder cannot be moved into itself.', 'err.empty folder name': 'Please enter a name.',
    'st.areas': 'Areas', 'st.areas.hint': 'Display name per area. Leave empty to use the matching account’s display name or the folder name.',
    'st.archive': 'Archive folder', 'st.path': 'Path', 'st.browse': 'Browse', 'st.inboxes': 'Inbox folders',
    'st.add': 'Add inbox folder', 'st.name': 'Name', 'st.area': 'Area', 'st.area.none': 'choose when filing',
    'st.enabled': 'active', 'st.after': 'After filing', 'st.after.move': 'move original to “_importiert”',
    'st.after.keep': 'leave original in the inbox', 'st.remove': 'Remove',
    'st.ok.rw': 'exists · readable · writable', 'st.ok.ro': 'exists · read-only', 'st.missing': 'missing or not readable',
    'st.files': '{n} files inside', 'st.saved': 'Saved.', 'st.choose': 'Choose this folder', 'st.up': 'one level up',
    'st.roots': 'Available folders', 'st.nodirs': 'no subfolders',
    'err.archive folder not readable': 'The archive folder is missing or not readable.',
    'err.inbox and archive must not overlap': 'Inbox and archive must not be inside each other.',
    'err.absolute path required': 'Please enter a full path (starting with /).',
    'ai.intro': 'The AI only makes suggestions. Documents are filed by verified rules or after your confirmation.',
    'ai.enabled': 'Use AI suggestions', 'ai.provider': 'Provider', 'ai.openai': 'Other OpenAI-compatible server', 'ai.ollama': 'Ollama (own server)',
    'ai.baseurl': 'Server address', 'ai.model': 'Model', 'ai.key': 'API key', 'ai.clearkey': 'Remove',
    'ai.limit': 'Monthly limit (USD)', 'ai.exclude': 'Never send to the AI', 'ai.test': 'Test connection',
    'ai.key.set': 'stored ({hint}) – leave empty to keep', 'ai.key.none': 'no key stored yet',
    'ai.key.local': 'usually not needed for local servers',
    'ai.price': '{input} $ / {output} $ per million tokens (input / output)', 'ai.price.none': 'unknown price – usage is counted in tokens only',
    'ai.usage': '{month}: {cost} $ spent, {calls} requests', 'ai.saved': 'Saved.',
    'ai.testing': 'Testing …', 'ai.test.ok': 'Answer from {model} in {seconds} s: “{text}” ({cost} $)',
    'err.no API key': 'No API key stored.', 'err.API key rejected': 'The API key was rejected.',
    'err.monthly limit reached': 'The monthly limit has been reached.', 'err.no server address': 'The server address is missing.',
    'err.cannot reach the Anthropic API': 'The Anthropic API cannot be reached.',
    'err.unknown model': 'The provider does not know the model “{model}”.',
    'err.not an Anthropic key': 'This is not an Anthropic key (those start with sk-ant-). Did a password manager fill the field?',
    'ai.other': 'Enter another model …', 'ai.reload': 'Reload list',
    'ai.models.loading': 'Asking for available models …', 'ai.models.live': '{n} models from the provider',
    'ai.models.builtin': 'Built-in list – could not ask the provider: {reason}',
    'acc.who': 'Signed in as {name}', 'acc.old': 'Current password', 'acc.new': 'New password',
    'acc.change': 'Change password', 'acc.ok': 'Password changed.',
    'usr.new': 'New user', 'usr.edit': 'Edit user {name}', 'usr.name': 'User',
    'usr.display': 'Display name', 'usr.pass': 'Password', 'usr.pass.keep': 'leave empty = unchanged',
    'usr.role': 'Role', 'usr.areas': 'Areas', 'usr.admin': 'Administrator (sees all areas, may change settings)',
    'usr.adminrole': 'Admin', 'usr.userrole': 'User', 'usr.all': 'all', 'usr.none': 'none',
    'usr.delete.q': 'Really delete user {name}?', 'usr.saved': 'Saved.',
    'perm.none': 'no access', 'perm.read': 'read', 'perm.write': 'read + write',
    'btn.cancel': 'Cancel', 'btn.save': 'Save', 'btn.edit': 'Edit', 'btn.delete': 'Delete',
    'sys.version': 'Version', 'sys.docs': 'Documents', 'sys.scan': 'Last scan', 'sys.texts': 'Texts extracted',
    'sys.ocr': 'Pages via OCR', 'sys.ocrstate': 'Text recognition (OCR)', 'sys.on': 'active', 'sys.off': 'not available',
    'sys.err.title': "Documents without readable text",
    'sys.err.hint': "These documents open fine, only their text is missing from the full-text search. Title and folder still find them.",
    'sys.err.password': "password-protected – Ordnung! cannot read the text",
    'sys.err.missing': "file was missing while reading – will be retried",
    'sys.err.damaged': "file damaged or not a valid PDF",
    'sys.err.other': "Unknown error",
    'sys.err.retry': "Read again",
    'sys.err.retried': "{n} document(s) are being read again.",
    'sys.errors': 'Read errors', 'sys.mode': 'Archive', 'sys.readonly': 'read-only', 'sys.writable': 'writable',
    'sys.rescan': 'Rescan folders now', 'sys.rescan.ok': 'Scan started.',
    'err.user exists': 'This user already exists.', 'err.invalid user name': 'Only lowercase letters, digits, . _ - allowed.',
    'err.last administrator': 'The last administrator cannot be removed.',
    'err.wrong password': 'Current password is wrong.', 'err.cannot delete yourself': 'You cannot delete yourself.',
    'err.cannot remove your own admin role': 'You cannot give up your own admin role.',
  },
};
const LANGS = ['de', 'en', 'fr', 'it'];
// the account's choice (remembered in this browser), else the browser language
let LANG = (() => {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem('ordnung.lang')); } catch { /* none */ }
  if (LANGS.includes(saved)) return saved;
  const nav = (navigator.language || 'de').slice(0, 2).toLowerCase();
  return LANGS.includes(nav) ? nav : 'en';
})();
const t = (key, vars = {}) =>
  ((I18N[LANG] || {})[key] || (LANG !== 'de' && I18N.en[key]) || I18N.de[key] || key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');

function applyI18n() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
}

// --------------------------------------------------------------- storage

const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem('ordnung.' + key); return v === null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem('ordnung.' + key, JSON.stringify(value)); } catch { /* ignore */ }
  },
};

// ------------------------------------------------------------------- api

async function api(path, options = {}) {
  const res = await fetch('api/' + path, {
    credentials: 'same-origin',
    headers: options.body ? { 'Content-Type': 'application/json' } : {},
    ...options,
  });
  if (res.status === 401) { showLogin(); throw new Error('unauthorized'); }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try { detail = (await res.json()).detail || detail; } catch { /* keep */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// ----------------------------------------------------------------- state

const PAGE = 200;
const AREA_COLORS = ['#0070f2', '#c35500', '#188918', '#a100c2', '#d20a0a', '#007c87', '#5d36ff', '#8f6a00'];

const State = {
  areas: [],          // [{name, count}]
  active: new Set(),  // selected areas
  folder: store.get('folder', ''),
  recursive: store.get('recursive', true),
  query: '',
  open: new Set(store.get('open', [])),
  items: [],
  total: 0,
  selected: null,
  me: null,
  tags: new Set(),    // tag filter (all must match)
  sel: new Set(),     // ids ticked in the list
  tagList: [],        // [{name, count}]
  mappen: [],         // [{name, count}] – tags shown like folders
  mappe: null,        // the Mappe currently shown
};

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const areaColor = name => AREA_COLORS[Math.max(0, State.areas.findIndex(a => a.name === name)) % AREA_COLORS.length];
const areaLabel = name => {
  if (!name) return t('area.none');
  const area = State.areas.find(a => a.name === name);
  return (area && area.label) || name;
};
const highlight = s => esc(s).replace(/\x02/g, '<mark>').replace(/\x03/g, '</mark>');
const errText = e => {
  const k = 'err.' + e.message;
  if (I18N[LANG][k]) return t(k);
  const m = /^unknown model: (.+)$/.exec(e.message);
  if (m) return t('err.unknown model', { model: m[1] });
  const d = /^already in the archive: (.+)$/.exec(e.message);
  if (d) return t('err.already in the archive', { path: d[1] });
  return e.message;
};

function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  if (LANG === 'de') return `${d}.${m}.${y}`;
  return LANG === 'en' ? iso : `${d}/${m}/${y}`;
}

// ----------------------------------------------------------------- theme

const THEMES = ['system', 'light', 'dark'];
function applyTheme(theme) {
  const dark = theme === 'dark' || (theme === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
  $('theme-dark').disabled = !dark;
  $('theme-light').disabled = dark;
  $('btn-theme').textContent = { system: '◐', light: '☀', dark: '☾' }[theme];
}
let theme = store.get('theme', 'system');
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => applyTheme(theme));

// ----------------------------------------------------------------- views

function showLogin() {
  $('view-app').hidden = true;
  $('view-login').hidden = false;
  $('login-user').focus();
}

async function showApp() {
  $('view-login').hidden = true;
  $('view-app').hidden = false;
  State.me = await api('me');
  if (LANGS.includes(State.me.language) && State.me.language !== LANG) {
    store.set('lang', State.me.language);       // the account's language wins
    if (store.get('lang', null) === State.me.language) { location.reload(); return; }
  }
  document.querySelectorAll('.admin-only').forEach(el => { el.hidden = !State.me.is_admin; });
  const areas = await api('areas');
  State.areas = areas;
  const saved = store.get('areas', null);
  State.active = new Set(areas.map(a => a.name).filter(n => !saved || saved.includes(n)));
  if (!State.active.size) State.active = new Set(areas.map(a => a.name));
  $('chk-recursive').checked = State.recursive;
  renderChips();
  route();
  await loadOpen();
  await Promise.all([loadTree(), loadDocs(), loadStatus(), loadTags()]);
  updateImportButton();
}

// ----------------------------------------------------------------- chips

function renderChips() {
  const box = $('area-chips');
  box.innerHTML = '';
  if (State.areas.length < 2) return;
  for (const area of State.areas) {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip';
    chip.setAttribute('aria-pressed', State.active.has(area.name));
    chip.innerHTML = `<span class="chip__dot" style="--dot:${areaColor(area.name)}"></span>${esc(areaLabel(area.name))}`;
    chip.addEventListener('click', () => {
      if (State.active.has(area.name)) State.active.delete(area.name); else State.active.add(area.name);
      if (!State.active.size) State.active.add(area.name);
      store.set('areas', [...State.active]);
      renderChips();
      loadTree();
      loadDocs();
      loadTags();
    });
    box.appendChild(chip);
  }
}

const areaParam = () => 'areas=' + encodeURIComponent([...State.active].join(','));

// ------------------------------------------------------------------ tree

let treeData = null;

async function loadTree() {
  treeData = await api('tree?' + areaParam());
  renderTree();
}

function renderTree() {
  const box = $('tree');
  box.innerHTML = '';
  const all = { ...treeData, name: t('tree.all'), path: '' };
  addNode(box, all, 0);
}

function addNode(box, node, depth) {
  const hasKids = node.children.length > 0;
  const isOpen = depth === 0 || State.open.has(node.path);
  const row = document.createElement('div');
  row.className = 'tree-row' + (node.path === State.folder && !State.mappe ? ' is-selected' : '');
  row.style.setProperty('--depth', depth);
  row.setAttribute('role', 'treeitem');
  const dots = State.active.size > 1 && node.areas.length < State.active.size
    ? `<span class="tree-dots">${node.areas.map(a => `<span class="area-dot" style="--dot:${areaColor(a)}" title="${esc(areaLabel(a))}"></span>`).join('')}</span>`
    : '';
  if (!node.count && depth > 0) row.classList.add('is-empty');
  row.innerHTML =
    `<span class="tree-caret${isOpen ? ' is-open' : ''}">${hasKids && depth > 0 ? '›' : ''}</span>` +
    `<span class="tree-name">${esc(node.name)}</span>${dots}` +
    `<span class="tree-count">${node.count}</span>` +
    (State.me && State.me.is_admin ? `<button type="button" class="tree-menu" title="${esc(t('fo.menu'))}" aria-label="${esc(t('fo.menu'))}">⋯</button>` : '');
  const menuBtn = row.querySelector('.tree-menu');
  if (menuBtn) menuBtn.addEventListener('click', ev => { ev.stopPropagation(); folderMenu(menuBtn, node); });
  box.appendChild(row);

  row.querySelector('.tree-caret').addEventListener('click', ev => {
    if (!hasKids || depth === 0) return;
    ev.stopPropagation();
    toggleOpen(node.path);
  });
  row.addEventListener('click', () => {
    if (hasKids && depth > 0 && State.folder === node.path) { toggleOpen(node.path); return; }
    if (hasKids && depth > 0) State.open.add(node.path);
    selectFolder(node.path);
  });

  treeDropTarget(row, node, hasKids && depth > 0 && !isOpen);
  if (hasKids && isOpen) node.children.forEach(child => addNode(box, child, depth + 1));
}

function toggleOpen(path) {
  if (State.open.has(path)) State.open.delete(path); else State.open.add(path);
  saveOpen();
  renderTree();
}

// Which folders are expanded is kept per person on the server (and in the
// browser as a fallback), so it follows the account to other devices.
let saveOpenTimer = null;
function saveOpen() {
  store.set('open', [...State.open]);
  clearTimeout(saveOpenTimer);
  saveOpenTimer = setTimeout(flushOpen, 600);
}
function flushOpen() {
  if (!saveOpenTimer) return;
  saveOpenTimer = null;
  fetch('api/me/prefs', {
    method: 'PUT', keepalive: true, headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tree_open: [...State.open] }),
  }).catch(() => {});
}
addEventListener('pagehide', flushOpen);

async function loadOpen() {
  try {
    const prefs = await api('me/prefs');
    if (prefs.tree_open.length || !State.open.size) State.open = new Set(prefs.tree_open);
    else saveOpen();                       // first time: take over what this browser had
  } catch { /* keep the browser's copy */ }
  openAncestors(State.folder);
}

function openAncestors(path) {
  const parts = path ? path.split('/') : [];
  for (let i = 1; i < parts.length; i++) State.open.add(parts.slice(0, i).join('/'));
}

function setAllOpen(open) {
  if (!treeData) return;
  if (open) {
    const walk = node => node.children.forEach(c => { if (c.children.length) { State.open.add(c.path); walk(c); } });
    walk(treeData);
  } else {
    State.open.clear();
  }
  saveOpen();
  renderTree();
}

function selectFolder(path) {
  State.folder = path;
  store.set('folder', path);
  openAncestors(path);
  saveOpen();
  $('search').value = '';
  State.query = '';
  State.tags.clear();
  State.mappe = null;
  $('tree-panel').classList.remove('is-open');
  renderTree();
  renderMappen();
  loadDocs();
}

// ----------------------------------------------------------------- list

let listToken = 0;

async function loadDocs(append = false) {
  const token = ++listToken;
  const offset = append ? State.items.length : 0;
  const searching = State.query.trim().length > 0;
  const params = [
    areaParam(),
    // a search or a tag filter always covers the whole archive (of the chosen areas)
    'folder=' + encodeURIComponent(searching || State.tags.size ? '' : State.folder),
    'recursive=' + (searching || State.recursive),
    'tags=' + encodeURIComponent([...State.tags].join(',')),
    'q=' + encodeURIComponent(State.query),
    'limit=' + PAGE,
    'offset=' + offset,
  ].join('&');
  const data = await api('documents?' + params);
  if (token !== listToken) return;
  State.items = append ? State.items.concat(data.items) : data.items;
  State.total = data.total;
  renderList();
}

function renderList() {
  const searching = State.query.trim().length > 0 || State.tags.size > 0;
  const folderName = State.folder ? State.folder.split('/').pop() : t('tree.all');
  $('list-title').textContent = State.query.trim() ? `${t('list.search')}: ${State.query}`
    : State.mappe ? '📎 ' + State.mappe : (State.tags.size ? t('tags.filter') + ':' : folderName);
  const inMappe = !!State.mappe && !State.query.trim();
  $('list-mappe-actions').hidden = !inMappe;
  if (inMappe) {
    const q = 'api/mappen/download?name=' + encodeURIComponent(State.mappe);
    $('mappe-zip').href = q + '&format=zip';
    $('mappe-pdf').href = q + '&format=pdf';
  }
  $('list-tagfilter').innerHTML = [...State.tags].filter(tag => tag !== State.mappe).map(tag =>
    `<button type="button" class="tag tag--filter" data-tag="${esc(tag)}" title="${esc(t('tags.del'))}">${esc(tag)} ×</button>`).join('');
  $('list-tagfilter').querySelectorAll('[data-tag]').forEach(b => b.addEventListener('click', () => toggleTagFilter(b.dataset.tag)));
  $('list-count').textContent = State.items.length < State.total
    ? t('count.of', { n: State.items.length, total: State.total })
    : t('status.docs', { n: State.total });

  const rows = $('doc-rows');
  rows.innerHTML = '';
  const showFolder = searching || State.recursive;
  for (const doc of State.items) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row' + (State.selected && State.selected.id === doc.id ? ' is-selected' : '');
    const linked = State.mappe && !State.query.trim();
    const sub = (linked
      ? `<div class="doc-folder"><span class="link-badge">📎 ${esc(t('mp.linked'))}</span> ${esc(t('mp.in'))} ` +
        `<a href="#" class="goto-folder" data-folder="${esc(doc.folder)}">${esc((doc.folder || t('tree.root')).replaceAll('/', ' › '))}</a></div>`
      : showFolder && (searching || doc.folder !== State.folder)
      ? `<div class="doc-folder">${esc(doc.folder || t('tree.root'))}</div>` : '') +
      (doc.snippet ? `<div class="doc-snippet">${highlight(doc.snippet)}</div>` : '');
    const shownTags = (doc.tags || []).filter(x => !(linked && x === State.mappe));
    const tags = shownTags.length
      ? `<div class="tag-row">${shownTags.map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div>` : '';
    tr.innerHTML =
      `<td class="fd-table__cell col-check"><input type="checkbox"${State.sel.has(doc.id) ? ' checked' : ''} aria-label="${esc(doc.title)}"></td>` +
      `<td class="fd-table__cell col-date">${esc(formatDate(doc.date))}</td>` +
      `<td class="fd-table__cell"><div class="doc-title">${esc(doc.title)}</div>${tags}${sub}</td>` +
      `<td class="fd-table__cell col-area"><span class="doc-area"><span class="area-dot" style="--dot:${areaColor(doc.area)}"></span>${esc(areaLabel(doc.area))}</span></td>`;
    const box = tr.querySelector('.col-check input');
    box.addEventListener('click', ev => ev.stopPropagation());
    box.addEventListener('change', () => {
      if (box.checked) State.sel.add(doc.id); else State.sel.delete(doc.id);
      renderBulk();
    });
    tr.querySelector('.col-check').addEventListener('click', ev => ev.stopPropagation());
    tr.addEventListener('click', () => openPreview(doc));
    const go = tr.querySelector('.goto-folder');
    if (go) go.addEventListener('click', ev => { ev.preventDefault(); ev.stopPropagation(); selectFolder(go.dataset.folder); });
    if (linked && canWrite(doc)) {
      const out = document.createElement('button');
      out.type = 'button';
      out.className = 'mappe-out';
      out.title = t('mp.out');
      out.setAttribute('aria-label', t('mp.out'));
      out.textContent = '✕';
      out.addEventListener('click', async ev => {
        ev.stopPropagation();
        try {
          await api('tags/change', { method: 'POST', body: JSON.stringify({ ids: [doc.id], remove: [State.mappe] }) });
          toast(esc(t('mp.removed', { name: State.mappe })), null, 3000);
          loadDocs(); loadTags();
        } catch (e) { toast(esc(e.message)); }
      });
      tr.querySelector('.col-area').appendChild(out);
    }
    if (canWrite(doc)) {
      tr.draggable = true;
      tr.addEventListener('dragstart', ev => docDragStart(ev, doc));
      tr.addEventListener('dragend', docDragEnd);
    }
    rows.appendChild(tr);
  }
  renderBulk();
  $('list-empty').hidden = State.items.length > 0;
  $('btn-more').hidden = State.items.length >= State.total;
}

// --------------------------------------------------------------- layout

const Layout = {
  treeWidth: store.get('treeWidth', null),       // px
  pvPos: store.get('previewPos', 'right'),        // 'right' | 'bottom'
  pvSize: store.get('previewSize', {}),           // { right: px, bottom: px }
};

function applyLayout() {
  const root = document.documentElement.style;
  if (Layout.treeWidth) root.setProperty('--tree-w', Layout.treeWidth + 'px');
  const bottom = Layout.pvPos === 'bottom';
  $('work').classList.toggle('work--bottom', bottom);
  const size = Layout.pvSize[Layout.pvPos];
  if (size) $('preview').style.setProperty('--pv-size', size + 'px');
  else $('preview').style.removeProperty('--pv-size');
  const btn = $('pv-layout');
  btn.textContent = (bottom ? '\u25E8 ' : '\u2B13 ') + t(bottom ? 'pv.lay.right' : 'pv.lay.bottom');
  btn.title = t(bottom ? 'pv.right' : 'pv.bottom');
  btn.setAttribute('aria-label', btn.title);
}

function makeSplitter(handle, onMove, onEnd) {
  handle.addEventListener('pointerdown', ev => {
    ev.preventDefault();
    handle.setPointerCapture(ev.pointerId);
    handle.classList.add('is-dragging');
    document.body.classList.add('is-resizing');
    const move = e => onMove(e);
    const up = () => {
      handle.releasePointerCapture(ev.pointerId);
      handle.classList.remove('is-dragging');
      document.body.classList.remove('is-resizing');
      handle.removeEventListener('pointermove', move);
      handle.removeEventListener('pointerup', up);
      handle.removeEventListener('pointercancel', up);
      onEnd();
    };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
    handle.addEventListener('pointercancel', up);
  });
}

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function initLayout() {
  applyLayout();
  makeSplitter($('split-tree'), e => {
    const left = $('archive-layout').getBoundingClientRect().left;
    Layout.treeWidth = Math.round(clamp(e.clientX - left, 160, window.innerWidth * 0.5));
    document.documentElement.style.setProperty('--tree-w', Layout.treeWidth + 'px');
  }, () => store.set('treeWidth', Layout.treeWidth));

  makeSplitter($('split-preview'), e => {
    const box = $('work').getBoundingClientRect();
    const size = Layout.pvPos === 'bottom'
      ? clamp(box.bottom - e.clientY, 160, box.height - 120)
      : clamp(box.right - e.clientX, 260, box.width - 260);
    Layout.pvSize[Layout.pvPos] = Math.round(size);
    $('preview').style.setProperty('--pv-size', Layout.pvSize[Layout.pvPos] + 'px');
  }, () => store.set('previewSize', Layout.pvSize));

  // double click resets to the default size
  $('split-tree').addEventListener('dblclick', () => {
    Layout.treeWidth = null;
    store.set('treeWidth', null);
    document.documentElement.style.removeProperty('--tree-w');
  });
  $('split-preview').addEventListener('dblclick', () => {
    delete Layout.pvSize[Layout.pvPos];
    store.set('previewSize', Layout.pvSize);
    applyLayout();
  });

  const sideSplitter = (handleId, varName, storeKey, fromRight) => {
    const saved = store.get(storeKey, null);
    if (saved) document.documentElement.style.setProperty(varName, saved + 'px');
    let width = saved;
    makeSplitter($(handleId), e => {
      const box = $(handleId).parentElement.getBoundingClientRect();
      width = Math.round(clamp(fromRight ? box.right - e.clientX : e.clientX - box.left, 180, box.width * 0.6));
      document.documentElement.style.setProperty(varName, width + 'px');
    }, () => store.set(storeKey, width));
    $(handleId).addEventListener('dblclick', () => {
      store.set(storeKey, null);
      document.documentElement.style.removeProperty(varName);
    });
  };
  sideSplitter('split-rules', '--rules-w', 'rulesWidth', false);
  sideSplitter('split-import', '--import-w', 'importWidth', true);
  sideSplitter('split-inbox', '--inbox-w', 'inboxWidth', false);

  $('pv-layout').addEventListener('click', () => {
    Layout.pvPos = Layout.pvPos === 'bottom' ? 'right' : 'bottom';
    store.set('previewPos', Layout.pvPos);
    applyLayout();
  });
}

// -------------------------------------------------------------- preview

function openPreview(doc) {
  State.selected = doc;
  const url = `api/documents/${doc.id}/file`;
  $('pv-title').textContent = doc.title;
  // the folder is a link: jump to it in the tree, the preview stays open
  $('pv-sub').innerHTML = [formatDate(doc.date), areaLabel(doc.area)].filter(Boolean).map(esc)
    .concat(`<a href="#" class="pv-folder" title="${esc(t('pv.gofolder'))}">${esc((doc.folder || t('tree.root')).replaceAll('/', ' › '))}</a>`)
    .join(' · ');
  $('pv-sub').querySelector('.pv-folder').addEventListener('click', ev => {
    ev.preventDefault();
    const keep = State.selected;
    selectFolder(doc.folder || '');
    if (matchMedia('(max-width: 900px)').matches) closePreview();   // phone: the preview covers the list
    else State.selected = keep;
    setTimeout(() => document.querySelector('.tree-row.is-selected')?.scrollIntoView({ block: 'nearest' }), 300);
  });
  tagEditor($('pv-tags'), doc.tags || [], async tags => {
    const r = await api(`documents/${doc.id}/tags`, { method: 'PUT', body: JSON.stringify({ tags }) });
    doc.tags = r.tags;
    State.items.filter(x => x.sha256 === doc.sha256).forEach(x => { x.tags = r.tags; });
    renderList();
    loadTags();
    return r.tags;
  });
  $('pv-open').href = url;
  $('pv-download').href = url + '?download=true';
  editorButton(doc);
  $('pv-trash').hidden = !canWrite(doc);
  $('pv-meta').hidden = !canWrite(doc);
  $('pv-meta-form').hidden = true;
  const body = $('pv-body');
  if (doc.ext === 'pdf') body.innerHTML = `<iframe src="${url}#view=FitH" title="${esc(doc.title)}"></iframe>`;
  else if (['png', 'jpg', 'jpeg'].includes(doc.ext)) body.innerHTML = `<img src="${url}" alt="${esc(doc.title)}">`;
  else body.innerHTML = `<p class="preview__none">${esc(t('pv.none'))}</p>`;
  $('preview').hidden = false;
  $('split-preview').hidden = false;
  renderList();
}

function closePreview() {
  State.selected = null;
  $('preview').hidden = true;
  $('split-preview').hidden = true;
  $('pv-body').innerHTML = '';
  renderList();
}

// --------------------------------------------------------------- status

let statusTimer = null;
async function loadStatus() {
  clearTimeout(statusTimer);
  try {
    const s = await api('status');
    State.status = s;
    const time = s.last_scan ? new Date(s.last_scan).toLocaleString(LANG, { dateStyle: 'short', timeStyle: 'short' }) : '–';
    const texts = s.texts && s.texts.done < s.texts.total ? ' · ' + t('status.texts', s.texts) : '';
    $('status').textContent = s.scanning && !s.last_scan
      ? t('status.scanning')
      : `${t('status.docs', { n: s.total })} · ${t('status.scan', { t: time })}${texts} · v${s.version}`;
    const badge = $('ib-badge');
    if (s.inbox) { badge.hidden = !s.inbox.new; badge.textContent = s.inbox.new; }
    if (s.scanning && !s.last_scan) statusTimer = setTimeout(async () => { await loadStatus(); await showApp(); }, 3000);
    else statusTimer = setTimeout(loadStatus, texts ? 15000 : 60000);
  } catch { /* shown elsewhere */ }
}

// -------------------------------------------------------------- settings

const PANES = { konto: 'account', benutzer: 'users', ordner: 'folders', ablage: 'storage', ki: 'ai', system: 'system' };
const ADMIN_PANES = new Set(['users', 'folders', 'storage', 'ai', 'system']);

function route() {
  if (!State.me) return;
  const m = location.hash.match(/^#\/einstellungen(?:\/([a-z]+))?/);
  const r = State.me.is_admin ? location.hash.match(/^#\/regeln(?:\/(.*))?$/) : null;
  const imp = State.me.is_admin && /^#\/import/.test(location.hash);
  const ib = State.me.is_admin && /^#\/eingang/.test(location.hash);
  const trash = /^#\/papierkorb/.test(location.hash);
  $('trashpage').hidden = !trash;
  const inSettings = !!m;
  $('settings').hidden = !inSettings;
  $('rules').hidden = !r;
  $('importpage').hidden = !imp;
  $('inboxpage').hidden = !ib;
  const other = inSettings || !!r || imp || ib || trash;
  $('archive-toolbar').hidden = other;
  $('archive-layout').hidden = other;
  if (!ib) clearTimeout(Inb.timer);
  if (ib) { openInbox(); return; }
  if (trash) { loadTrash(); return; }
  if (r) { openRules(r[1] ? decodeURIComponent(r[1]) : ''); return; }
  if (imp) { loadImport(); return; }
  if (!inSettings) return;
  let pane = PANES[m && m[1]] || 'account';
  if (ADMIN_PANES.has(pane) && !State.me.is_admin) pane = 'account';
  $('acc-who').textContent = t('acc.who', { name: State.me.display_name || State.me.name });
  showPane(pane);
}

function showPane(pane) {
  document.querySelectorAll('.set-link').forEach(a => a.classList.toggle('is-active', a.dataset.pane === pane));
  document.querySelectorAll('.set-pane').forEach(p => { p.hidden = p.dataset.pane !== pane; });
  if (pane !== 'users') $('usr-form').hidden = true;
  if (pane === 'users') loadUsers();
  if (pane === 'ai') loadAI();
  if (pane === 'storage') loadStorage();
  if (pane === 'folders') loadFolders();
  if (pane === 'system') loadSystem();
}

function setMsg(el, text, ok) {
  el.textContent = text;
  el.className = 'form-msg ' + (ok ? 'is-ok' : 'is-error');
}

let users = [];
let editing = null;   // null = new user, else name

async function loadUsers() {
  users = await api('users');
  const rows = $('usr-rows');
  rows.innerHTML = '';
  for (const u of users) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    const areas = u.is_admin ? t('usr.all')
      : (Object.entries(u.areas).map(([a, p]) => `${areaLabel(a)} (${t('perm.' + p)})`).join(', ') || t('usr.none'));
    tr.innerHTML =
      `<td class="fd-table__cell"><div class="doc-title">${esc(u.display_name || u.name)}</div><div class="doc-folder">${esc(u.name)}</div></td>` +
      `<td class="fd-table__cell"><span class="role-badge">${t(u.is_admin ? 'usr.adminrole' : 'usr.userrole')}</span></td>` +
      `<td class="fd-table__cell">${esc(areas)}</td>` +
      `<td class="fd-table__cell usr-actions">` +
      `<button class="fd-button fd-button--transparent" data-act="edit">${t('btn.edit')}</button>` +
      (u.name === State.me.name ? '' : `<button class="fd-button fd-button--transparent fd-button--negative" data-act="del">${t('btn.delete')}</button>`) +
      `</td>`;
    tr.querySelector('[data-act="edit"]').addEventListener('click', () => editUser(u));
    tr.querySelector('[data-act="del"]')?.addEventListener('click', () => deleteUser(u));
    rows.appendChild(tr);
  }
}

function editUser(u) {
  editing = u ? u.name : null;
  const form = $('usr-form');
  form.hidden = false;
  $('usr-msg').textContent = '';
  $('usr-form-title').textContent = u ? t('usr.edit', { name: u.name }) : t('usr.new');
  $('usr-name').value = u ? u.name : '';
  $('usr-name').disabled = !!u;
  $('usr-display').value = u ? u.display_name : '';
  $('usr-pass').value = '';
  $('usr-pass').required = !u;
  $('usr-pass').placeholder = u ? t('usr.pass.keep') : '';
  $('usr-admin').checked = u ? u.is_admin : false;
  const box = $('usr-areas');
  box.innerHTML = '';
  for (const area of State.areas) {
    const label = document.createElement('span');
    label.innerHTML = `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(areaLabel(area.name))}`;
    const select = document.createElement('select');
    select.dataset.area = area.name;
    for (const p of ['none', 'read', 'write']) {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = t('perm.' + p);
      select.appendChild(opt);
    }
    select.value = (u && u.areas[area.name]) || 'none';
    box.append(label, select);
  }
  syncAdminAreas();
  (u ? $('usr-display') : $('usr-name')).focus();
}

function syncAdminAreas() {
  const admin = $('usr-admin').checked;
  $('usr-areas').querySelectorAll('select').forEach(s => { s.disabled = admin; });
}

async function saveUser(ev) {
  ev.preventDefault();
  const areas = {};
  $('usr-areas').querySelectorAll('select').forEach(s => { if (s.value !== 'none') areas[s.dataset.area] = s.value; });
  const body = {
    display_name: $('usr-display').value,
    is_admin: $('usr-admin').checked,
    areas,
  };
  if ($('usr-pass').value) body.password = $('usr-pass').value;
  try {
    if (editing) {
      await api('users/' + encodeURIComponent(editing), { method: 'PATCH', body: JSON.stringify(body) });
    } else {
      body.name = $('usr-name').value.trim().toLowerCase();
      await api('users', { method: 'POST', body: JSON.stringify(body) });
    }
    $('usr-form').hidden = true;
    await loadUsers();
  } catch (e) {
    setMsg($('usr-msg'), errText(e), false);
  }
}

async function deleteUser(u) {
  if (!confirm(t('usr.delete.q', { name: u.name }))) return;
  try {
    await api('users/' + encodeURIComponent(u.name), { method: 'DELETE' });
    await loadUsers();
  } catch (e) {
    alert(errText(e));
  }
}

async function loadSystem() {
  const s = await api('status');
  const time = s.last_scan ? new Date(s.last_scan).toLocaleString(LANG) : '–';
  const rows = [
    ['sys.version', s.version],
    ['sys.mode', t(s.readonly ? 'sys.readonly' : 'sys.writable')],
    ['sys.docs', s.total],
    ['sys.scan', `${time} (${s.last_scan_seconds ?? '–'} s)`],
    ['sys.texts', `${s.texts.done} / ${s.texts.total}`],
    ['sys.ocrstate', t(s.ocr ? 'sys.on' : 'sys.off')],
    ['sys.ocr', s.texts.ocr_pages],
    ['sys.errors', s.texts.errors],
  ];
  $('sys-info').innerHTML = rows.map(([k, v]) => `<dt>${esc(t(k))}</dt><dd>${esc(v)}</dd>`).join('');
  loadTextErrors();
}

async function loadTextErrors() {
  const box = $('sys-errors');
  let items = [];
  try { items = (await api('text-errors')).items; } catch { /* keep empty */ }
  box.hidden = !items.length;
  if (!items.length) return;
  $('sys-err-list').innerHTML = items.map(d =>
    `<li><a href="#" data-id="${esc(d.id)}">${esc(d.title)}</a> <span class="doc-folder">${esc(areaLabel(d.area))} · ${esc(d.folder || t('tree.root'))}</span>` +
    `<div class="sys-err-why">${esc(t('sys.err.' + d.reason))}</div></li>`).join('');
  $('sys-err-list').querySelectorAll('a[data-id]').forEach(a => a.addEventListener('click', async ev => {
    ev.preventDefault();
    location.hash = '#/';
    openPreview(await api('documents/' + a.dataset.id));
  }));
  $('sys-err-retry').hidden = !State.me.is_admin;
}

// --------------------------------------------------------------- storage

let storage = null;

function statusHtml(s, files) {
  if (!s || !s.readable) return `<span class="status-bad">✕ ${esc(t('st.missing'))}</span>`;
  const base = s.writable ? `<span class="status-ok">✓ ${esc(t('st.ok.rw'))}</span>` : `<span class="status-warn">● ${esc(t('st.ok.ro'))}</span>`;
  return files == null ? base : `${base} · ${esc(t('st.files', { n: files }))}`;
}

async function loadStorage() {
  storage = await api('storage');
  $('st-archive').value = storage.archive_path;
  $('st-archive-status').innerHTML = statusHtml(storage.archive);
  $('st-reference').value = storage.reference_path || '';
  $('st-trash-days').value = storage.trash_days ?? 30;
  $('st-reference-status').innerHTML = storage.reference ? statusHtml(storage.reference) : '';
  $('st-msg').textContent = '';
  $('st-switch-msg').textContent = '';
  renderInboxes(storage.inboxes);
  renderAreaLabels();
}

function renderAreaLabels() {
  const box = $('st-areas');
  box.innerHTML = '';
  for (const area of State.areas.filter(a => a.name)) {
    const label = document.createElement('label');
    label.className = 'fd-form-label';
    label.innerHTML = `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(area.name)}`;
    const input = document.createElement('input');
    input.className = 'fd-input';
    input.dataset.area = area.name;
    input.value = storage.area_labels[area.name] || '';
    input.placeholder = area.label;
    const cell = document.createElement('div');
    cell.className = 'inline';
    cell.appendChild(input);
    if (!area.count) {                      // an empty area may go again
      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'fd-button fd-button--transparent';
      del.textContent = '✕';
      del.title = t('st.area.del');
      del.addEventListener('click', async () => {
        if (!confirm(t('st.area.del.q', { name: area.label || area.name }))) return;
        try {
          await api('areas/' + encodeURIComponent(area.name), { method: 'DELETE' });
          State.areas = await api('areas'); renderChips(); renderAreaLabels();
        } catch (e) { toast(esc(errText(e))); }
      });
      cell.appendChild(del);
    }
    box.append(label, cell);
  }
}

function renderInboxes(inboxes) {
  const box = $('st-inboxes');
  box.innerHTML = '';
  inboxes.forEach((ib, i) => box.appendChild(inboxCard(ib, i)));
}

function inboxCard(ib, i) {
  const el = document.createElement('div');
  el.className = 'inbox';
  el.dataset.id = ib.id || '';
  const areaOpts = [`<option value="">${esc(t('st.area.none'))}</option>`]
    .concat(State.areas.filter(a => a.name).map(a => `<option value="${esc(a.name)}"${a.name === ib.area ? ' selected' : ''}>${esc(areaLabel(a.name))}</option>`));
  el.innerHTML = `
    <div class="inbox-head">
      <input class="fd-input" data-f="name" value="${esc(ib.name || '')}" placeholder="${esc(t('st.name'))}">
      <label class="check"><input type="checkbox" data-f="enabled"${ib.enabled ? ' checked' : ''}> ${esc(t('st.enabled'))}</label>
      <button class="fd-button fd-button--transparent fd-button--negative" type="button" data-act="remove">${esc(t('st.remove'))}</button>
    </div>
    <div class="form-grid">
      <label class="fd-form-label">${esc(t('st.path'))}</label>
      <div>
        <div class="inline">
          <input class="fd-input" data-f="path" id="st-inbox-${i}" value="${esc(ib.path || '')}">
          <button class="fd-button" type="button" data-pick="st-inbox-${i}">${esc(t('st.browse'))}</button>
        </div>
        <div class="field-hint">${ib.status ? statusHtml(ib.status, ib.files) : ''}</div>
      </div>
      <label class="fd-form-label">${esc(t('st.area'))}</label>
      <select class="fd-input" data-f="area">${areaOpts.join('')}</select>
      <label class="fd-form-label">${esc(t('st.after'))}</label>
      <select class="fd-input" data-f="after_import">
        <option value="move"${ib.after_import !== 'keep' ? ' selected' : ''}>${esc(t('st.after.move'))}</option>
        <option value="keep"${ib.after_import === 'keep' ? ' selected' : ''}>${esc(t('st.after.keep'))}</option>
      </select>
    </div>
    <div class="picker" data-for="st-inbox-${i}" hidden></div>`;
  el.querySelector('[data-act="remove"]').addEventListener('click', () => el.remove());
  return el;
}

function collectInboxes() {
  return [...$('st-inboxes').querySelectorAll('.inbox')].map(el => {
    const v = f => el.querySelector(`[data-f="${f}"]`);
    return {
      id: el.dataset.id || null,
      name: v('name').value.trim(),
      path: v('path').value.trim(),
      area: v('area').value,
      enabled: v('enabled').checked,
      after_import: v('after_import').value,
    };
  }).filter(i => i.path);
}

async function saveStorage(ev) {
  ev.preventDefault();
  try {
    storage = await api('storage', { method: 'PUT', body: JSON.stringify({
      archive_path: $('st-archive').value.trim(),
      reference_path: $('st-reference').value.trim(),
      inboxes: collectInboxes(),
      area_labels: Object.fromEntries([...$('st-areas').querySelectorAll('input')].map(i => [i.dataset.area, i.value.trim()])),
      trash_days: Math.max(0, parseInt($('st-trash-days').value || '0', 10)),
    }) });
    State.areas = await api('areas');
    renderChips();
    renderTree();
    renderList();
    $('st-archive-status').innerHTML = statusHtml(storage.archive);
    $('st-reference-status').innerHTML = storage.reference ? statusHtml(storage.reference) : '';
    renderInboxes(storage.inboxes);
    setMsg($('st-msg'), t('st.saved'), true);
    loadStatus();
  } catch (e) {
    setMsg($('st-msg'), errText(e), false);
  }
}

async function switchArchive() {
  const target = $('st-switch').value.trim();
  if (!target) { $('st-switch').focus(); return; }
  if (!confirm(t('st.switch.q', { new: target, old: storage.archive_path }))) return;
  try {
    const r = await api('storage/switch', { method: 'POST', body: JSON.stringify({ archive_path: target }) });
    setMsg($('st-switch-msg'), t('st.switch.ok', { rules: r.rules_remapped, folders: r.folders_added }), true);
    Rules.tree = null;
    await loadStorage();
    setMsg($('st-switch-msg'), t('st.switch.ok', { rules: r.rules_remapped, folders: r.folders_added }), true);
    State.areas = await api('areas');
    renderChips();
    await Promise.all([loadTree(), loadDocs(), loadStatus()]);
  } catch (e) {
    setMsg($('st-switch-msg'), errText(e), false);
  }
}

// inline folder picker: lists the container's mounted folders, then their subfolders
async function showPicker(inputId) {
  const picker = document.querySelector(`.picker[data-for="${inputId}"]`);
  if (!picker.hidden) { picker.hidden = true; return; }
  picker.hidden = false;
  const input = $(inputId);
  const render = async path => {
    let html;
    if (!path) {
      const roots = await api('fs/roots');
      html = `<div class="picker-bar"><span class="picker-path">${esc(t('st.roots'))}</span></div><div class="picker-list">` +
        roots.map(r => `<button type="button" class="picker-item" data-go="${esc(r.path)}">📁 ${esc(r.path)}</button>`).join('') + '</div>';
    } else {
      let d;
      try { d = await api('fs/list?path=' + encodeURIComponent(path)); } catch { return render(''); }
      html = `<div class="picker-bar"><span class="picker-path" title="${esc(d.path)}">${esc(d.path)}</span>` +
        `<button type="button" class="fd-button fd-button--emphasized" data-choose="${esc(d.path)}">${esc(t('st.choose'))}</button></div>` +
        `<div class="picker-list"><button type="button" class="picker-item" data-go="${esc(d.parent || '')}">↑ ${esc(t('st.up'))}</button>` +
        (d.dirs.length ? d.dirs.map(n => `<button type="button" class="picker-item" data-go="${esc(d.path.replace(/\/$/, '') + '/' + n)}">📁 ${esc(n)}</button>`).join('')
          : `<div class="picker-empty">${esc(t('st.nodirs'))}</div>`) + '</div>';
    }
    picker.innerHTML = html;
    picker.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => render(b.dataset.go)));
    picker.querySelector('[data-choose]')?.addEventListener('click', ev => {
      input.value = ev.currentTarget.dataset.choose;
      picker.hidden = true;
    });
  };
  render(input.value.trim());
}

// ----------------------------------------------------------------- rules

const Rules = { tree: null, overview: null, open: new Set(store.get('rulesOpen', [])), folder: null, editing: null,
  view: store.get('rulesView', 'senders'),   // 'senders' (for everyone) | 'folders' (experts)
  senders: null, sendersShown: 40,
  // last suggestions per folder (AI ones cost money, so they are kept until the page is reloaded)
  suggestions: {} };

async function openRules(folder) {
  if (folder) Rules.view = 'folders';
  setRulesView(Rules.view);
  if (Rules.view === 'senders') { Rules.folder = null; await loadSenders(); return; }
  if (!Rules.tree) {
    [Rules.tree, Rules.overview] = await Promise.all([api('tree?template=true'), api('rules')]);
  }
  Rules.folder = folder;
  pollGeneration();
  folder.split('/').reduce((acc, part) => { const p = acc ? acc + '/' + part : part; if (part) Rules.open.add(p); return p; }, '');
  const folders = Object.values(Rules.overview.folders).filter(f => f.rules > 0).length;
  $('rules-summary').textContent = t('rules.summary', { n: Rules.overview.rule_count, f: folders });
  renderRulesTree();
  $('rules-empty').hidden = !!folder;
  $('rules-folder').hidden = !folder;
  if (folder) await loadRuleFolder(folder);
}

function setRulesView(view) {
  Rules.view = view;
  store.set('rulesView', view);
  const senders = view === 'senders';
  $('rv-senders').setAttribute('aria-selected', senders);
  $('rv-folders').setAttribute('aria-selected', !senders);
  $('snd-side').hidden = !senders;
  $('rules-expert-side').hidden = senders;
  $('rules-senders').hidden = !senders;
  if (senders) { $('rules-empty').hidden = true; $('rules-folder').hidden = true; }
}

let genTimer = null;
async function pollGeneration() {
  clearTimeout(genTimer);
  const g = await api('rules/generate');
  const btn = $('rules-generate');
  if (g.running) {
    btn.disabled = true;
    $('rules-gen-status').textContent = t('rules.gen.run', g);
    genTimer = setTimeout(async () => { await pollGeneration(); }, 3000);
    return;
  }
  btn.disabled = false;
  if (g.finished) {
    $('rules-gen-status').textContent = t('rules.gen.done', { rules: g.rules, fwr: g.folders_with_rules, covered: g.covered });
    await refreshRulesOverview();
    if (Rules.folder) loadRuleFolder(Rules.folder, true);
  }
}

async function refreshRulesOverview() {
  Rules.overview = await api('rules');
  const folders = Object.values(Rules.overview.folders).filter(f => f.rules > 0).length;
  $('rules-summary').textContent = t('rules.summary', { n: Rules.overview.rule_count, f: folders });
  renderRulesTree();
}

function renderRulesTree() {
  const box = $('rules-tree');
  box.innerHTML = '';
  const add = (node, depth) => {
    const hasKids = node.children.length > 0;
    const isOpen = Rules.open.has(node.path);
    const info = Rules.overview.folders[node.path];
    const row = document.createElement('div');
    row.className = 'tree-row' + (node.path === Rules.folder ? ' is-selected' : '');
    row.style.setProperty('--depth', depth);
    row.innerHTML = `<span class="tree-caret${isOpen ? ' is-open' : ''}">${hasKids ? '\u203A' : ''}</span>` +
      `<span class="tree-name">${esc(node.name)}</span>` +
      `<span class="tree-dots">${node.areas.map(a => `<span class="area-dot" style="--dot:${areaColor(a)}" title="${esc(areaLabel(a))}"></span>`).join('')}</span>` +
      (info && info.rules ? `<span class="rule-badge">${info.rules}</span>` : '') +
      `<span class="tree-count">${(Rules.overview.docs && Rules.overview.docs[node.path]) ?? node.own}</span>`;
    row.querySelector('.tree-caret').addEventListener('click', ev => {
      ev.stopPropagation();
      if (!hasKids) return;
      if (Rules.open.has(node.path)) Rules.open.delete(node.path); else Rules.open.add(node.path);
      store.set('rulesOpen', [...Rules.open]);
      renderRulesTree();
    });
    row.addEventListener('click', () => { location.hash = '#/regeln/' + encodeURIComponent(node.path); });
    box.appendChild(row);
    if (hasKids && isOpen) node.children.forEach(c => add(c, depth + 1));
  };
  Rules.tree.children.forEach(c => add(c, 0));
}

function condChips(conds) {
  return conds.map(c => `<span class="cond">${esc(t('cond.' + c.type))} <b>${esc(c.value)}</b></span>`)
    .join(`<span class="cond-and">${esc(t('rules.and'))}</span>`);
}

function statsHtml(s) {
  const out = s.outside ? `<span class="status-warn">${esc(t('rules.out', { n: s.outside }))}</span>`
    : `<span class="status-ok">${esc(t('rules.out0'))}</span>`;
  return `${esc(t('rules.stats', { inside: s.inside, total: s.inside_total }))} · ${out}`;
}

function docList(label, docs) {
  if (!docs || !docs.length) return '';
  return `<div class="field-hint">${esc(label)}</div><ul class="outliers">` + docs.map(d =>
    `<li><a href="api/${d.origin === 'reference' ? 'reference' : 'documents'}/${esc(d.id)}/file" target="_blank" rel="noopener">${esc(d.title)}</a> – ` +
    (d.origin === 'reference' ? `<span class="src-tag">${esc(t('rules.ref'))}</span> ` : '') +
    `${esc(areaLabel(d.area))} · ${esc(d.folder || t('tree.root'))}${d.date ? ' · ' + esc(formatDate(d.date)) : ''}</li>`).join('') + '</ul>';
}

async function loadRuleFolder(folder, keepSuggestions = false) {
  const view = await api('rules/folder?path=' + encodeURIComponent(folder));
  $('rf-title').textContent = folder.split('/').pop();
  $('rf-path').textContent = folder + ' · ' + t('rules.docs', { n: view.doc_count });
  $('rf-desc').value = view.description;
  $('rf-desc-msg').textContent = '';
  $('rf-editor').hidden = true;
  const empty = view.doc_count === 0;
  $('rf-suggest').disabled = empty;
  $('rf-ai').disabled = empty;
  if (empty) {
    $('rf-sugg-meta').textContent = '';
    $('rf-suggestions').innerHTML = `<p class="set-hint">${esc(t('rules.nodocs'))}</p>`;
  } else if (!keepSuggestions) {
    const cached = Rules.suggestions[folder];
    $('rf-sugg-meta').textContent = cached ? cached.meta : '';
    if (cached) renderSuggestions(cached.list, cached.empty); else $('rf-suggestions').innerHTML = '';
  }
  const box = $('rf-rules');
  box.innerHTML = view.rules.length ? '' : `<p class="set-hint">${esc(t('rules.none'))}</p>`;
  for (const r of view.rules) {
    const el = document.createElement('div');
    el.className = 'rule' + (r.enabled ? '' : ' is-off');
    el.innerHTML = `<div class="rule-main"><div class="rule-plain">${lamp(r.stats.grade)} ${esc(r.plain || '')}` +
      ` <span class="src-tag">${esc(t('src.' + r.source))}</span></div>` +
      `<div class="rule-conds rule-conds--small">${condChips(r.conditions)}</div>` +
      `<div class="rule-stats">${statsHtml(r.stats)}</div>` + thumbs(r.stats.examples) +
      docList(t('rules.outliers'), r.stats.outside_docs) + `</div>` +
      `<div class="rule-actions"><label class="check"><input type="checkbox"${r.enabled ? ' checked' : ''}> ${esc(t('rules.active'))}</label>` +
      `<button class="fd-button fd-button--transparent" data-act="edit">${esc(t('btn.edit'))}</button>` +
      `<button class="fd-button fd-button--transparent fd-button--negative" data-act="del">${esc(t('btn.delete'))}</button></div>`;
    el.querySelector('input').addEventListener('change', async ev => {
      await api('rules/' + r.id, { method: 'PATCH', body: JSON.stringify({ enabled: ev.target.checked }) });
      el.classList.toggle('is-off', !ev.target.checked);
    });
    el.querySelector('[data-act="edit"]').addEventListener('click', () => openRuleEditor(r.conditions, r.id));
    el.querySelector('[data-act="del"]').addEventListener('click', async () => {
      if (!confirm(t('rules.delete.q'))) return;
      await api('rules/' + r.id, { method: 'DELETE' });
      await refreshRulesOverview();
      loadRuleFolder(folder, true);
    });
    box.appendChild(el);
  }
}

function condRow(c = { type: 'contains', value: '' }) {
  const row = document.createElement('div');
  row.className = 're-cond';
  row.innerHTML = `<select class="fd-input">${['contains', 'id', 'regex'].map(tp =>
      `<option value="${tp}"${tp === c.type ? ' selected' : ''}>${esc(t('cond.' + tp))}</option>`).join('')}</select>` +
    `<input class="fd-input" value="${esc(c.value)}" autocomplete="off">` +
    `<button class="fd-button fd-button--transparent" type="button" aria-label="Entfernen">&#10005;</button>`;
  row.querySelector('button').addEventListener('click', () => row.remove());
  return row;
}

function openRuleEditor(conds, ruleId = null) {
  Rules.editing = ruleId;
  $('rf-editor').hidden = false;
  $('re-conds').innerHTML = '';
  (conds && conds.length ? conds : [{ type: 'contains', value: '' }]).forEach(c => $('re-conds').appendChild(condRow(c)));
  $('re-stats').innerHTML = '';
  $('re-msg').textContent = '';
  $('re-conds').querySelector('input').focus();
  $('rf-editor').scrollIntoView({ block: 'nearest' });
}

function editorConds() {
  return [...$('re-conds').querySelectorAll('.re-cond')].map(r => ({
    type: r.querySelector('select').value, value: r.querySelector('input').value.trim(),
  })).filter(c => c.value);
}

async function testRule() {
  try {
    const s = await api('rules/evaluate', { method: 'POST', body: JSON.stringify({ folder: Rules.folder, conditions: editorConds() }) });
    $('re-msg').textContent = '';
    $('re-stats').innerHTML = statsHtml(s) + docList(t('rules.outliers'), s.outside_docs) + docList(t('rules.missed'), s.missed_docs.slice(0, 8));
  } catch (e) {
    setMsg($('re-msg'), errText(e), false);
  }
}

async function saveRule(conditions = editorConds(), source = 'manual') {
  try {
    if (Rules.editing) {
      await api('rules/' + Rules.editing, { method: 'PATCH', body: JSON.stringify({ conditions }) });
    } else {
      await api('rules', { method: 'POST', body: JSON.stringify({ folder: Rules.folder, conditions, source }) });
    }
    Rules.editing = null;
    await refreshRulesOverview();
    await loadRuleFolder(Rules.folder, true);
  } catch (e) {
    setMsg($('re-msg'), errText(e), false);
    $('rf-editor').hidden = false;
  }
}

async function loadSuggestions() {
  const box = $('rf-suggestions');
  $('rf-sugg-meta').textContent = '';
  box.innerHTML = `<p class="set-hint">${esc(t('rules.suggest.busy'))}</p>`;
  const folder = Rules.folder;
  const list = await api('rules/suggest?path=' + encodeURIComponent(folder));
  if (folder !== Rules.folder) return;
  Rules.suggestions[folder] = { list, empty: t('rules.suggest.none'), meta: '' };
  renderSuggestions(list, t('rules.suggest.none'));
}

async function loadAISuggestions() {
  const box = $('rf-suggestions');
  $('rf-sugg-meta').textContent = '';
  box.innerHTML = `<p class="set-hint">${esc(t('rules.ai.busy'))}</p>`;
  $('rf-ai').disabled = true;
  const folder = Rules.folder;
  try {
    const res = await api('rules/ai-suggest?path=' + encodeURIComponent(folder), { method: 'POST' });
    if (folder !== Rules.folder) return;
    const meta = t('rules.ai.meta', { model: res.model, samples: res.samples, seconds: res.seconds, cost: res.cost.toFixed(3) });
    $('rf-sugg-meta').textContent = meta;
    Rules.suggestions[folder] = { list: res.suggestions, empty: t('rules.ai.none'), meta };
    renderSuggestions(res.suggestions, t('rules.ai.none'));
  } catch (e) {
    box.innerHTML = `<p class="form-msg is-error">${esc(errText(e))}</p>`;
  } finally {
    $('rf-ai').disabled = false;
  }
}

function renderSuggestions(list, emptyText) {
  const box = $('rf-suggestions');
  box.innerHTML = list.length ? '' : `<p class="set-hint">${esc(emptyText)}</p>`;
  for (const s of list) {
    const el = document.createElement('div');
    el.className = 'rule';
    el.innerHTML = `<div class="rule-main"><div class="rule-conds">${condChips(s.conditions)}</div>` +
      (s.reason ? `<div class="field-hint">KI: ${esc(s.reason)}</div>` : '') +
      `<div class="rule-stats">${statsHtml(s)}</div>${docList(t('rules.outliers'), s.outside_docs)}</div>` +
      `<div class="rule-actions"><button class="fd-button" data-act="adapt">${esc(t('rules.adapt'))}</button>` +
      `<button class="fd-button fd-button--emphasized" data-act="take">${esc(t('rules.take'))}</button></div>`;
    el.querySelector('[data-act="take"]').addEventListener('click', async () => {
      Rules.editing = null;
      await saveRule(s.conditions, s.kind === 'ai' ? 'ai' : 'suggestion');
      el.remove();
      const cached = Rules.suggestions[Rules.folder];
      if (cached) cached.list = cached.list.filter(x => x !== s);
    });
    el.querySelector('[data-act="adapt"]').addEventListener('click', () => openRuleEditor(s.conditions));
    box.appendChild(el);
  }
}

// ---------------------------------------------------------------- import

const Imp = { data: null };

async function loadImport() {
  const [data, tree, folders] = await Promise.all([api('import/plan'), api('import/tree'), api('folders')]);
  Imp.data = data;
  const s = data.summary;
  const kpi = (v, k) => `<div class="kpi"><b>${esc(v)}</b><span>${esc(t(k))}</span></div>`;
  $('imp-summary').innerHTML = kpi(s.documents, 'imp.k.docs') + kpi(s.folders_before, 'imp.k.before') +
    kpi(s.folders_after, 'imp.k.after') + kpi(s.moves, 'imp.k.moves') + kpi(s.no_area, 'imp.k.noarea') + kpi(s.open, 'imp.k.open');
  const targets = [...new Set(data.rows.map(r => r.target_folder).concat(folders.folders.map(f => f.path)).filter(Boolean))].sort();
  $('imp-targets').innerHTML = targets.map(f => `<option value="${esc(f)}">`).join('');
  renderImportRows();
  const box = $('imp-tree');
  box.innerHTML = '';
  const add = (node, depth) => {
    const row = document.createElement('div');
    row.className = 'tree-row';
    row.style.setProperty('--depth', depth);
    row.innerHTML = `<span class="tree-caret"></span><span class="tree-name">${esc(node.name)}</span><span class="tree-count">${node.count}</span>`;
    box.appendChild(row);
    node.children.forEach(c => add(c, depth + 1));
  };
  tree.children.forEach(c => add(c, 0));
}

function renderImportRows() {
  const filter = $('imp-filter').value;
  const q = fold($('imp-search').value);
  const box = $('imp-rows');
  box.innerHTML = '';
  const rows = Imp.data.rows.filter(r => {
    if (filter === 'todo' && !(r.moves || r.hints.length || r.reasons.length || !r.target_area)) return false;
    if (filter === 'open' && r.confirmed) return false;
    if (q && !fold(r.folder + ' ' + r.target_folder + ' ' + areaLabel(r.area)).includes(q)) return false;
    return true;
  });
  if (!rows.length) { box.innerHTML = `<p class="set-hint">${esc(t('imp.empty'))}</p>`; return; }
  for (const r of rows.slice(0, 400)) box.appendChild(importRow(r));
}

function fold(s) { return (s || '').normalize('NFC').toLowerCase(); }

function importRow(r) {
  const el = document.createElement('div');
  el.className = 'imp-row ' + (r.confirmed ? 'is-ok' : (r.hints.length || !r.target_area ? 'is-todo' : ''));
  const tags = r.reasons.map(x => `<span class="tag info">${esc(t('imp.r.' + x))}</span>`)
    .concat(r.hints.map(h => `<span class="tag warn">${esc(t('imp.h.' + h, { list: (r.same_name || []).join(', ') }))}</span>`));
  if (r.confirmed) tags.push(`<span class="tag">✓ ${esc(t('imp.ok'))}</span>`);
  const areaOpts = [`<option value="">–</option>`].concat(State.areas.filter(a => a.name).map(a =>
    `<option value="${esc(a.name)}"${a.name === r.target_area ? ' selected' : ''}>${esc(a.label || a.name)}</option>`));
  const parent = r.folder.includes('/') ? r.folder.split('/').slice(0, -1).join('/') : null;
  el.innerHTML = `<div class="imp-head"><span class="area-dot" style="--dot:${areaColor(r.area)}"></span>` +
    `<span class="imp-src">${esc(areaLabel(r.area))} / ${esc(r.folder || '–')}</span>` +
    `<span class="imp-count">${esc(t('imp.docs', { n: r.count }))}</span></div>` +
    (tags.length ? `<div class="imp-tags">${tags.join('')}</div>` : '') +
    `<div class="imp-target">→ <select class="fd-input">${areaOpts.join('')}</select>` +
    `<input class="fd-input" data-picker="imp-targets" autocomplete="off" value="${esc(r.target_folder)}">` +
    (r.hints.includes('single') && parent ? `<button class="fd-button fd-button--transparent" data-act="parent">${esc(t('imp.toparent'))}</button>` : '') +
    (r.manual ? `<button class="fd-button fd-button--transparent" data-act="reset">${esc(t('imp.reset'))}</button>` : '') +
    `<button class="fd-button${r.confirmed ? '' : ' fd-button--emphasized'}" data-act="ok">${esc(t('imp.confirm'))}</button></div>`;
  const save = async (folder) => {
    if (folder !== undefined) el.querySelector('input').value = folder;
    await api('import/plan/row', { method: 'PUT', body: JSON.stringify({
      area: r.area, folder: r.folder, target_area: el.querySelector('select').value,
      target_folder: el.querySelector('input').value, confirmed: true }) });
    loadImport();
  };
  el.querySelector('[data-act="ok"]').addEventListener('click', () => save());
  el.querySelector('input').addEventListener('keydown', ev => { if (ev.key === 'Enter') save(); });
  el.querySelector('[data-act="parent"]')?.addEventListener('click', () => save(parent));
  el.querySelector('[data-act="reset"]')?.addEventListener('click', async () => {
    await api('import/plan/row?area=' + encodeURIComponent(r.area) + '&folder=' + encodeURIComponent(r.folder), { method: 'DELETE' });
    loadImport();
  });
  return el;
}

// ----------------------------------------------------------------- inbox

const Inb = { data: null, key: null, shown: null, dirty: false, timer: null };

const srcTags = src => (src || '').split('+').filter(Boolean)
  .map(x => `<span class="tag ${x === 'rule' ? 'info' : ''}">${esc(t('ib.src.' + x))}</span>`).join('');

async function openInbox() {
  Inb.shown = null;
  await loadInbox();
}

async function loadInbox() {
  clearTimeout(Inb.timer);
  const status = $('ib-status').value;
  let data;
  try { data = await api('inbox?status=' + status); } catch (e) { $('ib-empty-text').textContent = errText(e); return; }
  Inb.data = data;
  const c = data.counts;
  $('ib-summary').textContent = t('ib.summary', c);
  $('ib-badge').hidden = !c.new;
  $('ib-badge').textContent = c.new;
  // uploading always works, so a missing inbox folder is no longer worth a warning
  const warn = !data.archive_writable ? t('ib.ro') : '';
  $('ib-warn').hidden = !warn;
  $('ib-warn').textContent = warn;
  $('ib-folders').innerHTML = data.folders.map(f => `<option value="${esc(f)}">`).join('');
  $('ib-bulk').hidden = status !== 'new' || !data.archive_writable;
  if (Inb.key && !data.items.some(i => i.key === Inb.key)) Inb.key = null;
  if (!Inb.key && data.items.length && window.innerWidth > 900) Inb.key = data.items[0].key;
  renderInboxList();
  const item = data.items.find(i => i.key === Inb.key);
  // refresh the form only when it shows another item or still waits for its text
  if (!item || Inb.shown !== item.key || (!Inb.dirty && Inb.shownReading && item.text)) showItem(item);
  if ($('inboxpage').hidden) return;
  Inb.timer = setTimeout(loadInbox, c.reading ? 5000 : 30000);
}

function renderInboxList() {
  const box = $('ib-list');
  box.innerHTML = '';
  for (const it of Inb.data.items) {
    const s = it.suggestion;
    const row = document.createElement('div');
    row.className = 'ib-row' + (it.key === Inb.key ? ' is-selected' : '');
    let sub;
    if (it.status === 'filed') sub = `<span class="mono">${esc(it.filed_path)}</span>`;
    else if (!it.text) sub = `<span class="ib-muted">${esc(t('ib.reading'))}</span>`;
    else if (s && s.folder) sub = `<span class="mono">${esc(s.folder)}</span> ${srcTags(s.source)}`;
    else sub = `<span class="ib-muted">${esc(t('ib.nosugg'))}</span>`;
    const flags = [];
    if (s && s.duplicate) flags.push(`<span class="tag warn">${esc(t('ib.dup'))}</span>`);
    if (s && s.conflict) flags.push(`<span class="tag warn">?</span>`);
    row.innerHTML = `<div class="ib-row-name">${esc(it.name)}</div><div class="ib-row-sub">${sub} ${flags.join('')}</div>`;
    row.addEventListener('click', () => { Inb.key = it.key; renderInboxList(); showItem(it); });
    box.appendChild(row);
  }
  const status = $('ib-status').value;
  $('ib-empty').hidden = !!Inb.key;
  $('ib-empty-text').textContent = Inb.data.items.length ? t('ib.pick') : (status === 'new' ? t('ib.empty') : t('imp.empty'));
}

function showItem(it) {
  Inb.shown = it ? it.key : null;
  Inb.shownReading = it ? !it.text : false;
  Inb.dirty = false;
  $('ib-detail').hidden = !it;
  $('ib-empty').hidden = !!it;
  $('ib-msg').textContent = '';
  if (!it) { $('ib-preview').innerHTML = ''; return; }
  const s = it.suggestion || {};
  $('ib-name').textContent = it.name;
  $('ib-rel').textContent = `${it.inbox_name} / ${it.rel}` + (it.text ? ' · ' + (it.text.chars
    ? t('ib.text', { pages: it.text.pages, method: it.text.method }) : t('ib.text.none')) : '');

  // why this suggestion
  const why = [];
  if (!it.text) why.push(t('ib.reading'));
  else if (!s.folder) why.push(t('ib.why.none'));
  if (s.conflict) why.push(`<span class="status-warn">${esc(t('ib.conflict'))}</span>`);
  $('ib-why').innerHTML = why.map(w => `<p class="set-hint">${w.startsWith('<') ? w : esc(w)}</p>`).join('');
  const cands = $('ib-cands');
  cands.innerHTML = '';
  for (const c of s.candidates || []) {
    const el = document.createElement('button');
    el.type = 'button';
    el.className = 'ib-cand' + (c.folder === s.folder ? ' is-active' : '');
    const detail = c.rules && c.rules.length ? condChips(c.rules[0].conditions)
      : (c.reason ? esc(c.reason) : (c.source === 'folder' ? esc(t('ib.why.folder', { folder: it.rel.split('/').slice(0, -1).join('/') })) : ''));
    el.innerHTML = `<div class="ib-cand-head"><span class="mono">${esc(c.folder)}</span> ${srcTags(c.source)}</div>` +
      (detail ? `<div class="ib-cand-why">${detail}</div>` : '');
    el.addEventListener('click', () => {
      $('ib-folder').value = c.folder;
      cands.querySelectorAll('.ib-cand').forEach(b => b.classList.toggle('is-active', b === el));
      Inb.dirty = true;
      updateFilename();
    });
    cands.appendChild(el);
  }
  const dup = $('ib-dup');
  dup.hidden = !s.duplicate;
  if (s.duplicate) {
    dup.innerHTML = `${esc(t('ib.dup.long', { path: s.duplicate.path }))} <button type="button" class="fd-button fd-button--transparent" id="ib-force">${esc(t('ib.dup.force'))}</button>`;
    $('ib-force').addEventListener('click', () => fileItem(true));
  }

  const areas = Inb.data.areas;
  $('ib-area').innerHTML = `<option value="">${esc(t('ib.area.pick'))}</option>` +
    areas.map(a => `<option value="${esc(a)}">${esc(areaLabel(a))}</option>`).join('');
  $('ib-area').value = s.area || '';
  $('ib-folder').value = s.folder || '';
  $('ib-title').value = s.title || '';
  $('ib-title').placeholder = s.title_fallback || '';
  $('ib-date').value = s.date || s.date_fallback || '';
  Inb.tags = [];
  tagEditor($('ib-tags'), [], async tags => { Inb.tags = tags; return tags; });
  const done = it.status !== 'new';
  ['ib-area', 'ib-folder', 'ib-title', 'ib-date', 'ib-submit', 'ib-ai'].forEach(id => { $(id).disabled = done || !Inb.data.archive_writable && id === 'ib-submit'; });
  $('ib-ai').disabled = done || !it.text;
  $('ib-dismiss').hidden = it.status === 'filed';
  $('ib-delete').hidden = it.status === 'filed';
  $('ib-dismiss').textContent = t(it.status === 'dismissed' ? 'ib.undismiss' : 'ib.dismiss');
  updateFilename();

  const url = `api/inbox/${it.key}/file`;
  const pv = $('ib-preview');
  if (it.ext === 'pdf') pv.innerHTML = `<iframe src="${url}#view=FitH" title="${esc(it.name)}"></iframe>`;
  else if (['png', 'jpg', 'jpeg'].includes(it.ext)) pv.innerHTML = `<img src="${url}" alt="${esc(it.name)}">`;
  else pv.innerHTML = `<p class="preview__none">${esc(t('pv.none'))}</p>`;
}

function updateFilename() {
  const it = Inb.data && Inb.data.items.find(i => i.key === Inb.shown);
  if (!it) return;
  if (document.activeElement && document.activeElement.closest && document.activeElement.closest('#ib-form')) Inb.dirty = true;
  const title = $('ib-title').value.trim() || $('ib-title').placeholder;
  const parts = [$('ib-area').value || '?', $('ib-folder').value.trim().replace(/^\/+|\/+$/g, '')].filter(Boolean);
  $('ib-filename').textContent = `${parts.join('/')}/${$('ib-date').value || '?'}_${title}_…​.${it.ext}`;
}

function nextItem() {
  const items = Inb.data.items;
  const i = items.findIndex(x => x.key === Inb.key);
  const next = items[i + 1] || items[i - 1];
  Inb.key = next ? next.key : null;
}

async function fileItem(force) {
  const key = Inb.shown;
  const body = {
    area: $('ib-area').value,
    folder: $('ib-folder').value.trim(),
    title: $('ib-title').value.trim() || $('ib-title').placeholder,
    date: $('ib-date').value,
    force,
    tags: $('ib-tags').flush ? $('ib-tags').flush() : (Inb.tags || []),
  };
  $('ib-submit').disabled = true;
  try {
    const r = await api(`inbox/${key}/file`, { method: 'POST', body: JSON.stringify(body) });
    nextItem();
    Inb.shown = null;
    await loadInbox();
    $('ib-msg').innerHTML = esc(t('ib.filed', { path: r.path }));
    $('ib-msg').className = 'form-msg is-ok';
    if (r.proposal) renderProposal($('ib-learn'), r.proposal); else $('ib-learn').innerHTML = '';
    Rules.tree = null;
  } catch (e) {
    setMsg($('ib-msg'), errText(e), false);
  } finally {
    $('ib-submit').disabled = false;
  }
}

async function fileAgreeing() {
  const n = Inb.data.items.filter(i => {
    const s = i.suggestion;
    return s && s.area && s.folder && !s.duplicate && !s.conflict && s.source.startsWith('rule+folder');
  }).length;
  if (!n) { alert(t('ib.agree.none')); return; }
  if (!confirm(t('ib.agree.q', { n }))) return;
  const r = await api('inbox/file-all', { method: 'POST', body: JSON.stringify({ mode: 'agree' }) });
  Inb.shown = null;
  await loadInbox();
  alert(t('ib.agree.done', { n: r.filed }) + (r.failed.length ? '\n\n' + r.failed.map(f => `${f.name}: ${errText(new Error(f.error))}`).join('\n') : ''));
}

// "KI fragen": pick one of the saved instructions (the default is preselected), Enter asks
async function askAI() {
  const key = Inb.shown;
  let cfg;
  try {
    cfg = await api('ai');
  } catch (e) {
    setMsg($('ib-msg'), errText(e), false);
    return;
  }
  const prompts = cfg.inbox_prompts || [];
  if (prompts.length <= 1) {                      // nothing to choose
    await runAI(key, prompts[0] ? prompts[0].name : null);
    return;
  }
  const dlg = $('ai-dlg');
  const list = $('ai-dlg-list');
  list.innerHTML = prompts.map((p, i) => {
    const first = p.text.split('\n').find(l => l.trim()) || '';
    const isDefault = p.name === cfg.inbox_default;
    return `<label class="ai-choice"><input type="radio" name="ai-choice" value="${i}"${isDefault ? ' checked' : ''}>` +
      `<span><span><b>${esc(p.name)}</b>${isDefault ? ` <em class="ai-choice-std">(${esc(t('ai.prompts.std'))})</em>` : ''}</span>` +
      `<small>${esc(first.length > 140 ? first.slice(0, 140) + ' …' : first)}</small></span></label>`;
  }).join('');
  const radios = [...list.querySelectorAll('input')];
  const current = radios.find(r => r.checked) || radios[0];
  current.checked = true;
  dlg.returnValue = '';
  dlg.onkeydown = ev => {
    if (ev.key === 'Enter' && !ev.isComposing && ev.target.tagName !== 'BUTTON' && ev.target.tagName !== 'A') {
      ev.preventDefault();
      dlg.close('ask');
    }
  };
  $('ai-dlg-edit').onclick = () => dlg.close('');
  dlg.onclose = async () => {
    if (dlg.returnValue !== 'ask') return;
    const picked = radios.find(r => r.checked);
    await runAI(key, prompts[picked ? Number(picked.value) : 0].name);
  };
  dlg.showModal();
  current.focus();
}

async function runAI(key, prompt) {
  $('ib-ai').disabled = true;
  setMsg($('ib-msg'), t('ib.ai.run'), true);
  try {
    const r = await api(`inbox/${key}/ai`, { method: 'POST', body: JSON.stringify(prompt ? { prompt } : {}) });
    const item = await api(`inbox/${key}`);
    const i = Inb.data.items.findIndex(x => x.key === key);
    if (i >= 0) Inb.data.items[i] = item;
    renderInboxList();
    showItem(item);
    if (r.folder) $('ib-folder').value = r.folder;
    if (r.title) $('ib-title').value = r.title;
    if (r.date) $('ib-date').value = r.date;
    updateFilename();
    setMsg($('ib-msg'), t('ib.ai.done', { cost: r.cost.toFixed(4) }), true);
  } catch (e) {
    setMsg($('ib-msg'), errText(e), false);
  } finally {
    $('ib-ai').disabled = false;
  }
}

async function dismissItem() {
  const key = Inb.shown;
  const it = Inb.data.items.find(i => i.key === key);
  try {
    await api(`inbox/${key}/dismiss`, { method: 'POST', body: JSON.stringify({ dismissed: it.status !== 'dismissed' }) });
    nextItem();
    Inb.shown = null;
    await loadInbox();
  } catch (e) {
    setMsg($('ib-msg'), errText(e), false);
  }
}

async function deleteItem() {
  const key = Inb.shown;
  const it = Inb.data.items.find(i => i.key === key);
  if (!it || !confirm(t('ib.delete.q', { name: it.name || it.rel }))) return;
  try {
    await api(`inbox/${key}`, { method: 'DELETE' });
    nextItem();
    Inb.shown = null;
    await loadInbox();
  } catch (e) {
    setMsg($('ib-msg'), errText(e), false);
  }
}

// --------------------------------------------------------------- folders

let Fo = null;

async function loadFolders() {
  Fo = await api('folders');
  $('fo-ro').hidden = Fo.writable;
  renderFolders();
}

function renderFolders() {
  const box = $('fo-tree');
  box.innerHTML = '';
  // docs below a folder (own + subfolders) to decide whether it may be deleted
  const below = {};
  for (const f of Fo.folders) {
    const parts = f.path.split('/');
    for (let i = 1; i <= parts.length; i++) {
      const p = parts.slice(0, i).join('/');
      below[p] = (below[p] || 0) + f.docs;
    }
  }
  for (const f of Fo.folders) {
    const depth = f.path.split('/').length - 1;
    const name = f.path.split('/').pop();
    const row = document.createElement('div');
    row.className = 'fo-row' + (below[f.path] ? '' : ' is-empty');
    row.style.setProperty('--depth', depth);
    row.innerHTML = `<span class="fo-name">${esc(name)}</span>` +
      `<span class="fo-count">${below[f.path] ? esc(t('fo.docs', { n: below[f.path] })) : esc(t('fo.empty'))}</span>` +
      `<span class="fo-actions">` +
      `<button class="fd-button fd-button--transparent" data-act="sub" title="${esc(t('fo.sub'))}">＋</button>` +
      `<button class="fd-button fd-button--transparent" data-act="ren" title="${esc(t('fo.rename'))}">✎</button>` +
      (below[f.path] ? '' : `<button class="fd-button fd-button--transparent fd-button--negative" data-act="del" title="${esc(t('fo.delete'))}">✕</button>`) +
      `</span>`;
    row.querySelector('[data-act="sub"]').addEventListener('click', () => inlineEdit(row, '', t('fo.sub.ph'), async v => {
      await api('folders', { method: 'POST', body: JSON.stringify({ path: f.path + '/' + v }) });
      return t('fo.added');
    }));
    row.querySelector('[data-act="ren"]').addEventListener('click', () => inlineEdit(row, f.path, '', async v => {
      const r = await api('folders', { method: 'PATCH', body: JSON.stringify({ old: f.path, new: v }) });
      return t('fo.renamed', { rules: r.rules });
    }));
    row.querySelector('[data-act="del"]')?.addEventListener('click', async () => {
      if (!confirm(t('fo.delete.q', { name: f.path }))) return;
      try { await api('folders?path=' + encodeURIComponent(f.path), { method: 'DELETE' }); await afterFolderChange(); }
      catch (e) { setMsg($('fo-msg'), errText(e), false); }
    });
    box.appendChild(row);
  }
}

function inlineEdit(row, value, placeholder, action) {
  if (row.querySelector('.fo-edit')) return;
  const input = document.createElement('input');
  input.className = 'fd-input fo-edit';
  input.value = value;
  input.placeholder = placeholder;
  row.querySelector('.fo-name').after(input);
  input.focus();
  input.addEventListener('keydown', async ev => {
    if (ev.key === 'Escape') { input.remove(); return; }
    if (ev.key !== 'Enter') return;
    try {
      const msg = await action(input.value.trim());
      setMsg($('fo-msg'), msg, true);
      await afterFolderChange();
    } catch (e) {
      setMsg($('fo-msg'), errText(e), false);
    }
  });
  input.addEventListener('blur', () => setTimeout(() => input.remove(), 200));
}

async function afterFolderChange() {
  Rules.tree = null;            // rules page rebuilds its tree
  await loadFolders();
}

// -------------------------------------------------------------------- AI

let aiConfig = null;

async function loadAI() {
  aiConfig = await api('ai');
  $('ai-enabled').checked = aiConfig.enabled;
  $('ai-provider').value = aiConfig.provider;
  $('ai-baseurl').value = aiConfig.base_url;
  fillModels(aiConfig.models.map(m => ({ ...m })), aiConfig.model);
  loadModels();
  $('ai-limit').value = aiConfig.monthly_limit_usd;
  $('ai-inbox-auto').checked = !!aiConfig.inbox_auto;
  renderPrompts(aiConfig.inbox_prompts, aiConfig.inbox_default);
  $('ai-key').value = '';
  $('ai-msg').textContent = '';
  const box = $('ai-exclude');
  box.innerHTML = '';
  for (const area of State.areas) {
    const label = document.createElement('label');
    label.className = 'check';
    label.innerHTML = `<input type="checkbox" value="${esc(area.name)}"${aiConfig.excluded_areas.includes(area.name) ? ' checked' : ''}> ` +
      `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(areaLabel(area.name))}`;
    box.appendChild(label);
  }
  syncAIForm();
}

// named instructions for "KI fragen"
function renderPrompts(prompts, def) {
  const box = $('ai-prompts');
  box.innerHTML = '';
  (prompts.length ? prompts : [{ name: 'Standard', text: aiConfig.inbox_prompt_default }])
    .forEach(p => addPrompt(p, p.name === def));
  if (!box.querySelector('input[type=radio]:checked')) box.querySelector('input[type=radio]').checked = true;
}

function addPrompt(p, isDefault) {
  const row = document.createElement('div');
  row.className = 'ai-prompt';
  row.innerHTML = `<div class="ai-prompt-head">
      <input class="fd-input ai-p-name" maxlength="60" placeholder="${esc(t('ai.prompts.name'))}" aria-label="${esc(t('ai.prompts.name'))}">
      <label class="check"><input type="radio" name="ai-p-default"> <span>${esc(t('ai.prompts.std'))}</span></label>
      <span class="spacer"></span>
      <button class="fd-button fd-button--transparent ai-p-tpl" type="button">${esc(t('ai.prompts.tpl'))}</button>
      <button class="fd-button fd-button--transparent ai-p-del" type="button">${esc(t('ai.prompts.del'))}</button>
    </div>
    <textarea class="fd-input ai-dlg-text ai-p-text" rows="8" spellcheck="true"></textarea>`;
  row.querySelector('.ai-p-name').value = p.name || '';
  row.querySelector('.ai-p-text').value = p.text || '';
  row.querySelector('input[type=radio]').checked = !!isDefault;
  row.querySelector('.ai-p-tpl').onclick = () => {
    const ta = row.querySelector('.ai-p-text');
    if (ta.value.trim() && !confirm(t('ai.prompts.tpl.ask'))) return;
    ta.value = aiConfig.inbox_prompt_default;
    ta.focus();
  };
  row.querySelector('.ai-p-del').onclick = () => {
    const box = $('ai-prompts');
    if (box.children.length <= 1) { setMsg($('ai-msg'), t('ai.prompts.last'), false); return; }
    const wasDefault = row.querySelector('input[type=radio]').checked;
    row.remove();
    if (wasDefault) box.querySelector('input[type=radio]').checked = true;
  };
  $('ai-prompts').appendChild(row);
  return row;
}

function promptsPayload() {
  const rows = [...$('ai-prompts').querySelectorAll('.ai-prompt')];
  const prompts = rows.map(r => ({ name: r.querySelector('.ai-p-name').value.trim(), text: r.querySelector('.ai-p-text').value.trim() }));
  const def = rows.find(r => r.querySelector('input[type=radio]').checked);
  return { inbox_prompts: prompts, inbox_default: def ? def.querySelector('.ai-p-name').value.trim() : '' };
}

function syncAIForm() {
  if (!aiConfig) return;
  const openai = $('ai-provider').value !== 'anthropic';
  document.querySelectorAll('.ai-openai-only').forEach(el => { el.hidden = !openai; });
  $('ai-key').placeholder = aiConfig.key_set ? t('ai.key.set', { hint: aiConfig.key_hint })
    : (openai ? t('ai.key.local') : t('ai.key.none'));
  $('ai-clear-key').hidden = !aiConfig.key_set;
  const price = aiConfig.prices[currentModel()];
  $('ai-price').textContent = price && !openai ? t('ai.price', price) : t('ai.price.none');
  const u = aiConfig.month_usage;
  $('ai-usage').textContent = t('ai.usage', { month: aiConfig.month, cost: (u.cost || 0).toFixed(2), calls: u.calls || 0 });
}

const OTHER = '__other__';

function fillModels(models, current) {
  const sel = $('ai-model-select');
  const list = models.slice();
  if (current && !list.some(m => m.id === current)) list.unshift({ id: current, label: current });
  sel.innerHTML = list.map(m => {
    const price = aiConfig.prices[m.id];
    const suffix = m.label !== m.id ? ` – ${m.id}` : '';
    return `<option value="${esc(m.id)}">${esc(m.label)}${esc(suffix)}${price ? ` (${price.input} / ${price.output} $)` : ''}</option>`;
  }).join('') + `<option value="${OTHER}">${esc(t('ai.other'))}</option>`;
  sel.value = current && list.length ? current : (list[0] ? list[0].id : OTHER);
  $('ai-model').hidden = sel.value !== OTHER;
}

let modelsToken = 0;
async function loadModels() {
  const token = ++modelsToken;
  $('ai-models-note').textContent = t('ai.models.loading');
  try {
    const res = await api('ai/models');
    if (token !== modelsToken) return;
    const keep = currentModel() || aiConfig.model;
    if (res.models.length) fillModels(res.models, keep);
    $('ai-models-note').textContent = res.source === 'provider'
      ? t('ai.models.live', { n: res.models.length })
      : t('ai.models.builtin', { reason: errText(new Error(res.error)) });
    syncAIForm();
  } catch (e) {
    $('ai-models-note').textContent = errText(e);
  }
}

function currentModel() {
  const sel = $('ai-model-select');
  return sel.value === OTHER ? $('ai-model').value.trim() : sel.value;
}

function aiPayload() {
  const body = {
    enabled: $('ai-enabled').checked,
    provider: $('ai-provider').value,
    base_url: $('ai-baseurl').value.trim(),
    model: currentModel(),
    monthly_limit_usd: Number($('ai-limit').value || 0),
    excluded_areas: [...$('ai-exclude').querySelectorAll('input:checked')].map(i => i.value),
    inbox_auto: $('ai-inbox-auto').checked,
    ...promptsPayload(),
  };
  if ($('ai-key').value.trim()) body.api_key = $('ai-key').value.trim();
  return body;
}

async function saveAI(ev) {
  if (ev) ev.preventDefault();
  try {
    aiConfig = await api('ai', { method: 'PUT', body: JSON.stringify(aiPayload()) });
    renderPrompts(aiConfig.inbox_prompts, aiConfig.inbox_default);
    const keyChanged = !!$('ai-key').value.trim();
    $('ai-key').value = '';
    syncAIForm();
    setMsg($('ai-msg'), t('ai.saved'), true);
    if (keyChanged) loadModels();
    return true;
  } catch (e) {
    setMsg($('ai-msg'), errText(e), false);
    return false;
  }
}

async function testAI() {
  if (!(await saveAI())) return;
  setMsg($('ai-msg'), t('ai.testing'), true);
  try {
    const r = await api('ai/test', { method: 'POST' });
    setMsg($('ai-msg'), t('ai.test.ok', { model: r.model, seconds: r.seconds, text: r.text, cost: r.cost.toFixed(4) }), true);
    aiConfig = await api('ai');
    syncAIForm();
  } catch (e) {
    setMsg($('ai-msg'), errText(e), false);
  }
}

// ----------------------------------------------------------------- wire

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

document.addEventListener('DOMContentLoaded', async () => {
  applyI18n();
  applyTheme(theme);
  initLayout();

  $('btn-theme').addEventListener('click', () => {
    theme = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    store.set('theme', theme);
    applyTheme(theme);
  });

  $('login-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    $('login-error').hidden = true;
    const res = await fetch('api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: $('login-user').value.trim(), password: $('login-pass').value }),
    });
    if (!res.ok) { $('login-error').hidden = false; return; }
    $('login-pass').value = '';
    showApp();
  });

  $('acc-logout').addEventListener('click', () => $('btn-logout').click());
  $('btn-logout').addEventListener('click', async () => {
    await fetch('api/logout', { method: 'POST' });
    showLogin();
  });

  $('search').addEventListener('input', debounce(ev => {
    State.query = ev.target.value;
    loadDocs();
  }, 250));

  $('chk-recursive').addEventListener('change', ev => {
    State.recursive = ev.target.checked;
    store.set('recursive', State.recursive);
    loadDocs();
  });

  $('btn-more').addEventListener('click', () => loadDocs(true));
  window.addEventListener('hashchange', route);
  $('fo-add').addEventListener('click', async () => {
    try {
      await api('folders', { method: 'POST', body: JSON.stringify({ path: $('fo-new').value }) });
      $('fo-new').value = '';
      setMsg($('fo-msg'), t('fo.added'), true);
      await afterFolderChange();
    } catch (e) { setMsg($('fo-msg'), errText(e), false); }
  });
  $('fo-new').addEventListener('keydown', ev => { if (ev.key === 'Enter') $('fo-add').click(); });
  $('fo-starter').addEventListener('click', async () => {
    if (!confirm(t('fo.starter.q'))) return;
    const r = await api('folders/starter', { method: 'POST' });
    setMsg($('fo-msg'), t('fo.starter.ok', { n: r.added }), true);
    await afterFolderChange();
  });
  $('imp-filter').addEventListener('change', renderImportRows);
  $('imp-search').addEventListener('input', debounce(renderImportRows, 200));
  $('imp-confirm-all').addEventListener('click', async () => {
    if (!confirm(t('imp.confirmall.q'))) return;
    await api('import/plan/confirm-all', { method: 'POST' });
    loadImport();
    updateImportButton();
  });
  $('rf-new').addEventListener('click', () => openRuleEditor(null));
  $('rules-generate').addEventListener('click', async () => {
    if (!confirm(t('rules.gen.q'))) return;
    await api('rules/generate', { method: 'POST' });
    setTimeout(pollGeneration, 1000);
  });
  $('rules-starter').addEventListener('click', async () => {
    const preview = await api('rules/starter?adapt=true&dry_run=true', { method: 'POST' });
    if (!preview.added) { alert(t('rules.starter.done', preview)); return; }
    const list = preview.rules.map(r => `• ${r.conditions.map(c => c.value).join(' + ')} → ${r.folder} (${r.inside}/${r.inside + r.outside})`).join('\n');
    if (!confirm(t('rules.starter.q') + '\n\n' + list)) return;
    const r = await api('rules/starter?adapt=true', { method: 'POST' });
    $('rules-gen-status').textContent = t('rules.starter.done', r);
    await refreshRulesOverview();
    if (Rules.folder) loadRuleFolder(Rules.folder, true);
  });
  $('re-add').addEventListener('click', () => $('re-conds').appendChild(condRow()));
  $('re-cancel').addEventListener('click', () => { $('rf-editor').hidden = true; Rules.editing = null; });
  $('re-test').addEventListener('click', testRule);
  $('re-save').addEventListener('click', () => saveRule());
  $('rf-suggest').addEventListener('click', loadSuggestions);
  $('rf-ai').addEventListener('click', loadAISuggestions);
  $('rf-desc-save').addEventListener('click', async () => {
    await api('rules/folder', { method: 'PUT', body: JSON.stringify({ folder: Rules.folder, description: $('rf-desc').value }) });
    setMsg($('rf-desc-msg'), t('rules.saved'), true);
    refreshRulesOverview();
  });
  $('st-form').addEventListener('submit', saveStorage);
  $('st-switch-go').addEventListener('click', switchArchive);
  $('ib-status').addEventListener('change', () => { Inb.key = null; loadInbox(); });
  $('ib-rescan').addEventListener('click', async () => { await api('inbox/rescan', { method: 'POST' }); setTimeout(loadInbox, 3000); });
  $('ib-file-agree').addEventListener('click', fileAgreeing);
  $('ib-form').addEventListener('submit', ev => { ev.preventDefault(); fileItem(false); });
  $('ib-ai').addEventListener('click', askAI);
  initPicker();
  initTags();
  initSenders();
  $('ib-dismiss').addEventListener('click', dismissItem);
  $('ib-delete').addEventListener('click', deleteItem);
  ['ib-area', 'ib-folder', 'ib-title', 'ib-date'].forEach(id => $(id).addEventListener('input', updateFilename));
  $('st-add').addEventListener('click', () => {
    const i = $('st-inboxes').children.length + Date.now() % 1000;
    $('st-inboxes').appendChild(inboxCard({ name: '', path: '', area: '', enabled: false, after_import: 'move' }, i));
  });
  $('settings').addEventListener('click', ev => {
    const btn = ev.target.closest('[data-pick]');
    if (btn) showPicker(btn.dataset.pick);
  });
  $('ai-form').addEventListener('submit', saveAI);
  $('ai-prompt-add').addEventListener('click', () => addPrompt({ name: '', text: '' }, false).querySelector('.ai-p-name').focus());
  $('ai-test').addEventListener('click', testAI);
  $('ai-provider').addEventListener('change', async () => {
    syncAIForm();
    if (await saveAI()) loadModels();
  });
  $('ai-model').addEventListener('input', syncAIForm);
  $('ai-model-select').addEventListener('change', () => {
    $('ai-model').hidden = $('ai-model-select').value !== OTHER;
    if (!$('ai-model').hidden) $('ai-model').focus();
    syncAIForm();
  });
  $('ai-reload-models').addEventListener('click', async () => { if (await saveAI()) loadModels(); });
  $('ai-clear-key').addEventListener('click', async () => {
    aiConfig = await api('ai', { method: 'PUT', body: JSON.stringify({ clear_key: true }) });
    syncAIForm();
  });
  $('usr-new').addEventListener('click', () => editUser(null));
  $('usr-cancel').addEventListener('click', () => { $('usr-form').hidden = true; });
  $('usr-form').addEventListener('submit', saveUser);
  $('usr-admin').addEventListener('change', syncAdminAreas);
  $('sys-rescan').addEventListener('click', async () => {
    await api('rescan', { method: 'POST' });
    $('sys-rescan').textContent = t('sys.rescan.ok');
    setTimeout(() => { $('sys-rescan').textContent = t('sys.rescan'); loadSystem(); }, 4000);
  });
  $('pw-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    try {
      await api('me/password', { method: 'POST', body: JSON.stringify({ old: $('pw-old').value, new: $('pw-new').value }) });
      $('pw-old').value = ''; $('pw-new').value = '';
      setMsg($('pw-msg'), t('acc.ok'), true);
    } catch (e) {
      setMsg($('pw-msg'), errText(e), false);
    }
  });
  $('pv-close').addEventListener('click', closePreview);
  $('acc-lang').value = LANG;
  $('acc-lang').addEventListener('change', async () => {
    const language = $('acc-lang').value;
    try { await api('me/prefs', { method: 'PUT', body: JSON.stringify({ language }) }); } catch { /* keep local */ }
    store.set('lang', language);
    location.reload();
  });
  initEditor();
  initDocOps();
  initMeta();
  initUpload();
  $('st-area-add').addEventListener('click', async () => {
    const name = $('st-area-name').value.trim().toLowerCase();
    if (!name) { $('st-area-name').focus(); return; }
    try {
      const r = await api('areas', { method: 'POST', body: JSON.stringify({ name, label: $('st-area-label').value.trim() }) });
      $('st-area-name').value = ''; $('st-area-label').value = '';
      State.areas = await api('areas');
      State.active.add(r.name);
      store.set('areas', [...State.active]);
      storage = await api('storage');
      renderChips(); renderAreaLabels();
      toast(esc(t('st.area.added', { name: r.label })), null, 6000);
    } catch (e) { toast(esc(errText(e))); }
  });
  $('sys-err-retry').addEventListener('click', async () => {
    const r = await api('text-errors/retry', { method: 'POST' });
    toast(esc(t('sys.err.retried', { n: r.retried })), null, 4000);
    setTimeout(loadSystem, 4000);
  });
  $('mappe-new').addEventListener('click', newMappe);
  $('btn-tree').addEventListener('click', () => $('tree-panel').classList.toggle('is-open'));
  $('tree-expand').addEventListener('click', () => setAllOpen(true));
  $('tree-collapse').addEventListener('click', () => setAllOpen(false));
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Escape' || !$('editor').hidden) return;
    if (!$('settings').hidden) location.hash = '#/';
    else if (State.selected) closePreview();
  });

  try {
    await api('me');
    await showApp();
  } catch {
    showLogin();
  }
});


// ------------------------------------------------------------ folder picker
// A large, searchable folder list for inputs with data-picker="<datalist id>" – the browser's
// own datalist popup is tiny (Safari) and cannot be styled. The datalist stays the source.
const Picker = { input: null, box: null, items: [], active: -1 };

function pickerOptions(input) {
  const list = document.getElementById(input.dataset.picker);
  return list ? [...list.options].map(o => o.value) : [];
}

function pickerRender() {
  const { input, box } = Picker;
  const all = pickerOptions(input);
  const q = input.value.trim().toLowerCase();
  const exact = all.some(f => f.toLowerCase() === q);
  const words = exact ? [] : q.split(/[\s/]+/).filter(Boolean);
  Picker.items = all.filter(f => words.every(w => f.toLowerCase().includes(w)));
  Picker.active = Picker.items.findIndex(f => f.toLowerCase() === q);
  if (!Picker.items.length) { box.hidden = true; return; }
  box.innerHTML = Picker.items.map((f, i) => {
    const cut = f.lastIndexOf('/');
    const head = cut >= 0 ? `<span class="picker-head">${esc(f.slice(0, cut + 1))}</span>` : '';
    return `<div class="picker-item${i === Picker.active ? ' active' : ''}" data-i="${i}" role="option">${head}${esc(f.slice(cut + 1))}</div>`;
  }).join('');
  const r = input.getBoundingClientRect();
  const below = window.innerHeight - r.bottom - 12;
  const above = r.top - 12;
  const up = below < 240 && above > below;
  box.style.left = `${Math.max(8, Math.min(r.left, window.innerWidth - Math.max(r.width, 420) - 8))}px`;
  box.style.minWidth = `${Math.max(r.width, 420)}px`;
  box.style.maxHeight = `${Math.min(window.innerHeight * 0.6, up ? above : below)}px`;
  box.style.top = up ? '' : `${r.bottom + 4}px`;
  box.style.bottom = up ? `${window.innerHeight - r.top + 4}px` : '';
  box.hidden = false;
  pickerScroll();
}

function pickerScroll() {
  const el = Picker.box.querySelector('.picker-item.active');
  if (el) el.scrollIntoView({ block: 'nearest' });
}

function pickerChoose(i) {
  const { input } = Picker;
  input.value = Picker.items[i];
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  Picker.box.hidden = true;
}

function initPicker() {
  const box = document.createElement('div');
  box.className = 'picker';
  box.setAttribute('role', 'listbox');
  box.hidden = true;
  document.body.appendChild(box);
  Picker.box = box;
  // mousedown, not click: keep the focus in the input
  box.addEventListener('mousedown', e => {
    const el = e.target.closest('.picker-item');
    e.preventDefault();
    if (el) pickerChoose(+el.dataset.i);
  });
  document.addEventListener('focusin', e => {
    if (e.target.matches('input[data-picker]') && !e.target.disabled) { Picker.input = e.target; pickerRender(); }
  });
  document.addEventListener('focusout', e => {
    if (e.target === Picker.input) box.hidden = true;
  });
  document.addEventListener('input', e => {
    if (e.target === Picker.input && document.activeElement === e.target) pickerRender();
  });
  document.addEventListener('keydown', e => {
    if (e.target !== Picker.input) return;
    if (box.hidden && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) { pickerRender(); e.preventDefault(); return; }
    if (box.hidden) return;
    const n = Picker.items.length;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      Picker.active = (Picker.active + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
      box.querySelectorAll('.picker-item').forEach((el, i) => el.classList.toggle('active', i === Picker.active));
      pickerScroll();
      e.preventDefault();
    } else if (e.key === 'Enter' && Picker.active >= 0) {
      pickerChoose(Picker.active);
      e.preventDefault();
    } else if (e.key === 'Escape') {
      box.hidden = true;
      e.preventDefault();
    }
  });
  window.addEventListener('resize', () => { box.hidden = true; });
  document.addEventListener('scroll', e => { if (!box.contains(e.target)) box.hidden = true; }, true);
}


// The import planner only matters while moving in from an old archive: show its button
// when there is a learning set with folders not yet planned (it stays reachable via #/import).
async function updateImportButton() {
  const btn = $('btn-import');
  if (!State.me || !State.me.is_admin) { btn.hidden = true; return; }
  try {
    const status = State.status || await api('status');
    if (!status.reference) { btn.hidden = true; return; }
    const plan = await api('import/plan');
    btn.hidden = !(plan.summary && plan.summary.open > 0);
  } catch { /* keep as is */ }
}

// ------------------------------------------------------------------- tags

async function loadTags() {
  loadMappen();
  try {
    State.tagList = await api('tags?' + areaParam());
  } catch { return; }
  $('tag-list').innerHTML = State.tagList.map(x => `<option value="${esc(x.name)}">`).join('');
  const mappenKeys = new Set((State.mappen || []).map(m => m.name.toLowerCase()));
  const plain = State.tagList.filter(x => !mappenKeys.has(x.name.toLowerCase()));
  $('tag-panel').hidden = !plain.length;
  const cloud = $('tag-cloud');
  cloud.innerHTML = plain.map(x =>
    `<button type="button" class="tag tag--cloud" data-tag="${esc(x.name)}" aria-pressed="${State.tags.has(x.name)}">` +
    `${esc(x.name)} <span class="tag__n">${x.count}</span></button>`).join('');
  cloud.querySelectorAll('[data-tag]').forEach(b => b.addEventListener('click', () => toggleTagFilter(b.dataset.tag)));
}

function toggleTagFilter(tag) {
  if (State.mappe) { State.tags.delete(State.mappe); State.mappe = null; renderMappen(); }
  if (State.tags.has(tag)) State.tags.delete(tag); else State.tags.add(tag);
  $('tree-panel').classList.remove('is-open');
  loadDocs();
  loadTags();
}

// Chips with × plus an input (folder-picker style suggestions from #tag-list).
// onSave(tags) persists and returns the stored tags. box.flush() adds what is still typed.
function tagEditor(box, tags, onSave) {
  let current = [...tags];
  let keepFocus = false;
  const render = () => {
    const focused = keepFocus || box.contains(document.activeElement);
    keepFocus = false;
    box.innerHTML = current.map((x, i) =>
      `<span class="tag">${esc(x)}<button type="button" class="tag__x" data-i="${i}" aria-label="${esc(t('tags.del'))}">×</button></span>`).join('') +
      `<input class="tag-input" data-picker="tag-list" autocomplete="off" placeholder="${esc(t('tags.new'))}">`;
    box.querySelectorAll('.tag__x').forEach(b => b.addEventListener('click', () => save(current.filter((_, i) => i !== +b.dataset.i))));
    const input = box.querySelector('input');
    input.addEventListener('keydown', ev => {
      if (ev.key === 'Enter' || ev.key === ',') {
        if (ev.key === 'Enter' && !Picker.box.hidden && Picker.active >= 0) return;   // the picker takes it
        ev.preventDefault();
        add(input.value);
      } else if (ev.key === 'Backspace' && !input.value && current.length) {
        save(current.slice(0, -1));
      }
    });
    input.addEventListener('change', () => add(input.value));
    if (focused) input.focus();
  };
  const add = value => {
    const tag = value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim();
    const input = box.querySelector('input');
    if (!tag || current.some(x => x.toLowerCase() === tag.toLowerCase())) { if (input) input.value = ''; return; }
    save([...current, tag]);
  };
  const save = async next => {
    keepFocus = box.contains(document.activeElement);
    try {
      current = await onSave(next);
    } catch (e) {
      alert(errText(e));
    }
    render();
  };
  box.flush = () => {
    const input = box.querySelector('input');
    const tag = input ? input.value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim() : '';
    return tag && !current.some(x => x.toLowerCase() === tag.toLowerCase()) ? [...current, tag] : current;
  };
  render();
}

function renderBulk() {
  const visible = new Set(State.items.map(d => d.id));
  [...State.sel].forEach(id => { if (!visible.has(id)) State.sel.delete(id); });
  $('bulk').hidden = !State.sel.size;
  $('bulk-count').textContent = t('tags.sel', { n: State.sel.size });
  const all = $('chk-all');
  all.checked = State.items.length > 0 && State.sel.size === State.items.length;
  all.indeterminate = State.sel.size > 0 && !all.checked;
}

async function bulkTag(mode) {
  const tag = $('bulk-tag').value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim();
  if (!tag || !State.sel.size) { $('bulk-tag').focus(); return; }
  try {
    const r = await api('tags/change', { method: 'POST', body: JSON.stringify({ ids: [...State.sel], [mode]: [tag] }) });
    setMsg($('bulk-msg'), t('tags.done', { n: r.changed }), true);
    $('bulk-tag').value = '';
    await Promise.all([loadDocs(), loadTags()]);
  } catch (e) {
    setMsg($('bulk-msg'), errText(e), false);
  }
}

function initTags() {
  $('chk-all').addEventListener('change', ev => {
    State.items.forEach(d => { if (ev.target.checked) State.sel.add(d.id); else State.sel.delete(d.id); });
    renderList();
  });
  $('bulk-add').addEventListener('click', () => bulkTag('add'));
  $('bulk-remove').addEventListener('click', () => bulkTag('remove'));
  $('bulk-clear').addEventListener('click', () => { State.sel.clear(); renderList(); });
  $('bulk-tag').addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && (Picker.box.hidden || Picker.active < 0)) { ev.preventDefault(); bulkTag('add'); }
  });
}


// ------------------------------------------------------- learning, senders
// Rules for people: a question in plain words after filing, a traffic light, examples to look at.

const lamp = grade => `<span class="lamp lamp--${esc(grade || 'red')}" title="${esc(t('grade.' + (grade || 'red')))}"></span>`;
const prettyFolder = f => esc(f).split('/').join(' › ');

function thumbs(docs) {
  if (!docs || !docs.length) return '';
  return `<div class="thumbs">` + docs.map(d =>
    `<a class="thumb" href="api/documents/${esc(d.id)}/file" target="_blank" rel="noopener" title="${esc(d.title)}">` +
    `<img src="api/documents/${esc(d.id)}/thumb" alt="" loading="lazy" onerror="this.remove()">` +
    `<span>${esc(d.title)}${d.date ? ' · ' + esc(formatDate(d.date)) : ''}</span></a>`).join('') + `</div>`;
}

// The question "Soll Ordnung! sich das merken?" with Ja/Nein; used after filing and in the sender list.
function renderProposal(box, p, done) {
  const card = document.createElement('div');
  card.className = 'learn';
  const folder = prettyFolder(p.folder);
  card.innerHTML =
    `<div class="learn-q">${t('learn.q', { label: esc(p.label), folder })}</div>` +
    `<div class="learn-meta">${lamp('green')} ${esc(p.inside ? t('learn.meta', { n: p.inside }) : t('learn.meta0'))}</div>` +
    (p.examples && p.examples.length ? `<div class="field-hint">${esc(t('learn.examples'))}</div>` + thumbs(p.examples) : '') +
    (p.sender ? `<label class="learn-name">${esc(t('learn.name'))} <input class="fd-input" value="${esc(p.sender_name)}"> <span class="mono">${esc(p.sender)}</span></label>` : '') +
    `<div class="form-actions"><button class="fd-button" type="button" data-a="no">${esc(t('learn.no'))}</button>` +
    `<button class="fd-button fd-button--emphasized" type="button" data-a="yes">${esc(t('learn.yes'))}</button></div>`;
  box.innerHTML = '';
  box.appendChild(card);
  card.querySelector('[data-a="no"]').addEventListener('click', async () => {
    if (p.sender) await api(`senders/${encodeURIComponent(p.sender)}/decline`, { method: 'POST', body: JSON.stringify({ folder: p.folder }) }).catch(() => {});
    box.innerHTML = '';
    if (done) done(false);
  });
  card.querySelector('[data-a="yes"]').addEventListener('click', async () => {
    let label = p.label;
    const input = card.querySelector('.learn-name input');
    try {
      if (input && input.value.trim() && input.value.trim() !== p.sender_name) {
        const r = await api(`senders/${encodeURIComponent(p.sender)}`, { method: 'PATCH', body: JSON.stringify({ name: input.value.trim() }) });
        label = label.replace(p.sender_name, r.name);
      }
      await api('rules', { method: 'POST', body: JSON.stringify({
        folder: p.folder, conditions: p.conditions, source: 'learned', label }) });
      card.innerHTML = `<div class="learn-q">${lamp('green')} ${esc(t('learn.done', { label, folder: p.folder.split('/').join(' › ') }))}</div>`;
      Rules.tree = null;
      Rules.senders = null;
      if (done) done(true);
    } catch (e) {
      alert(errText(e));
    }
  });
}

async function loadSenders(force = false) {
  if (!Rules.senders || force) {
    $('snd-list').innerHTML = `<p class="set-hint">…</p>`;
    Rules.senders = (await api('senders?' + areaParam())).senders;
  }
  renderSenders();
}

function renderSenders() {
  const q = $('snd-search').value.trim().toLowerCase();
  const all = Rules.senders.filter(x => !q || x.name.toLowerCase().includes(q) || x.domain.includes(q));
  const shown = all.slice(0, Rules.sendersShown);
  const box = $('snd-list');
  box.innerHTML = shown.length ? '' : `<p class="set-hint">${esc(t('snd.none'))}</p>`;
  for (const snd of shown) box.appendChild(senderCard(snd));
  $('snd-more').hidden = all.length <= shown.length;
}

function senderCard(snd) {
  const el = document.createElement('div');
  el.className = 'snd';
  const top = snd.folders.slice(0, 4);
  el.innerHTML =
    `<div class="snd-head">${lamp(snd.grade)} <b class="snd-name">${esc(snd.name)}</b>` +
    ` <span class="mono snd-domain">${esc(snd.domain)}</span> <span class="list-count">${esc(t('snd.docs', { n: snd.docs }))}</span>` +
    `<span class="snd-tools"><button class="fd-button fd-button--transparent" type="button" data-a="rename">${esc(t('snd.rename'))}</button>` +
    `<button class="fd-button fd-button--transparent" type="button" data-a="own">${esc(t('snd.own'))}</button></span></div>` +
    top.map((f, i) => `<div class="snd-folder" data-i="${i}">${lamp(f.grade)} <span class="snd-path">${prettyFolder(f.folder)}</span>` +
      ` <span class="list-count">${esc(t('snd.docs', { n: f.docs }))}</span>` +
      (f.grade !== 'green' ? ` <button class="fd-button fd-button--transparent" type="button" data-a="propose">${esc(t('snd.propose'))}</button>` : '') +
      `<div class="snd-learn"></div></div>`).join('') +
    (snd.folders.length > top.length ? `<div class="field-hint">${esc(t('snd.more', { n: snd.folders.length - top.length }))}</div>` : '');
  el.querySelector('[data-a="rename"]').addEventListener('click', async () => {
    const name = prompt(t('snd.rename'), snd.name);
    if (name === null) return;
    const r = await api(`senders/${encodeURIComponent(snd.domain)}`, { method: 'PATCH', body: JSON.stringify({ name }) });
    snd.name = r.name;
    el.replaceWith(senderCard(snd));
  });
  el.querySelector('[data-a="own"]').addEventListener('click', async () => {
    if (!confirm(t('snd.own.q', { name: snd.name, domain: snd.domain }))) return;
    await api(`senders/${encodeURIComponent(snd.domain)}`, { method: 'PATCH', body: JSON.stringify({ own: true }) });
    Rules.senders = Rules.senders.filter(x => x.domain !== snd.domain);
    el.remove();
  });
  el.querySelectorAll('[data-a="propose"]').forEach(btn => btn.addEventListener('click', async () => {
    const row = btn.closest('.snd-folder');
    const f = top[+row.dataset.i];
    const box = row.querySelector('.snd-learn');
    btn.disabled = true;
    const p = await api(`senders/${encodeURIComponent(snd.domain)}/propose?folder=${encodeURIComponent(f.folder)}`);
    btn.disabled = false;
    if (!p) { box.innerHTML = `<p class="set-hint">${esc(t('snd.propose.none', { name: snd.name }))}</p>`; return; }
    renderProposal(box, p, ok => {
      if (!ok) return;
      btn.remove();
      // fresh numbers for the whole sender (name, overall light) once the confirmation was seen
      setTimeout(async () => {
        const fresh = (await api('senders?' + areaParam())).senders;
        const mine = fresh.find(x => x.domain === snd.domain);
        Rules.senders = fresh;
        if (mine) el.replaceWith(senderCard(mine));
      }, 2500);
    });
  }));
  return el;
}

function initSenders() {
  $('rv-senders').addEventListener('click', () => { location.hash = '#/regeln'; setRulesView('senders'); openRules(''); });
  $('rv-folders').addEventListener('click', () => { setRulesView('folders'); openRules(Rules.folder || ''); });
  $('snd-search').addEventListener('input', debounce(() => { Rules.sendersShown = 40; renderSenders(); }, 200));
  $('snd-more').addEventListener('click', () => { Rules.sendersShown += 40; renderSenders(); });
}

// ------------------------------------------------- move, trash, undo

const canWrite = doc => !!doc && (State.me.write_areas || []).includes(doc.area);

function toast(html, action, ms = 8000) {
  const box = $('toast');
  clearTimeout(box._timer);
  box.innerHTML = `<span>${html}</span>`;
  if (action) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'fd-button fd-button--transparent toast__action';
    b.textContent = action.label;
    b.addEventListener('click', () => { box.hidden = true; action.run(); });
    box.appendChild(b);
  }
  const x = document.createElement('button');
  x.type = 'button';
  x.className = 'fd-button fd-button--transparent toast__close';
  x.textContent = '✕';
  x.addEventListener('click', () => { box.hidden = true; });
  box.appendChild(x);
  box.hidden = false;
  box._timer = setTimeout(() => { box.hidden = true; }, ms);
}

async function refreshArchive() {
  await Promise.all([loadDocs(), loadTree(), loadStatus()].map(p => p.catch(() => null)));
}

async function trashSelected() {
  const doc = State.selected;
  if (!doc) return;
  try {
    const r = await api(`documents/${doc.id}/trash`, { method: 'POST' });
    closePreview();
    State.sel.delete(doc.id);
    await refreshArchive();
    toast(esc(t('op.trashed', { title: doc.title })), {
      label: t('op.undo'),
      run: async () => {
        try {
          await api('trash/restore', { method: 'POST', body: JSON.stringify({ trash_path: r.trash_path }) });
          await refreshArchive();
          toast(esc(t('op.restored')), null, 3000);
        } catch (e) { toast(esc(e.message)); }
      },
    });
  } catch (e) {
    toast(esc(e.message));
  }
}

const DRAG_TYPE = 'application/x-ordnung-docs';
let dragIds = [];

function docDragStart(ev, doc) {
  const picked = State.sel.has(doc.id)
    ? State.items.filter(d => State.sel.has(d.id) && canWrite(d)) : [doc];
  dragIds = picked.map(d => d.id);
  ev.dataTransfer.effectAllowed = 'linkMove';
  ev.dataTransfer.setData(DRAG_TYPE, JSON.stringify(dragIds));
  ev.dataTransfer.setData('text/plain', picked.map(d => d.title).join('\n'));
  if (picked.length > 1) {
    const ghost = document.createElement('div');
    ghost.className = 'drag-ghost';
    ghost.textContent = t('op.drag', { n: picked.length });
    document.body.appendChild(ghost);
    ev.dataTransfer.setDragImage(ghost, 10, 10);
    setTimeout(() => ghost.remove(), 0);
  }
  document.body.classList.add('dragging-docs');
}

function docDragEnd() {
  dragIds = [];
  document.body.classList.remove('dragging-docs');
  document.querySelectorAll('.tree-row.is-drop').forEach(r => r.classList.remove('is-drop'));
}

function treeDropTarget(row, node, closed) {
  let openTimer = null;
  row.addEventListener('dragover', ev => {
    if (!ev.dataTransfer.types.includes(DRAG_TYPE)) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = 'move';
    if (!row.classList.contains('is-drop')) {
      row.classList.add('is-drop');
      // hovering a closed folder opens it, so deeper folders can be reached
      if (closed) openTimer = setTimeout(() => { State.open.add(node.path); saveOpen(); renderTree(); }, 800);
    }
  });
  row.addEventListener('dragleave', () => { row.classList.remove('is-drop'); clearTimeout(openTimer); });
  row.addEventListener('drop', async ev => {
    ev.preventDefault();
    clearTimeout(openTimer);
    row.classList.remove('is-drop');
    let ids = dragIds;
    try { ids = JSON.parse(ev.dataTransfer.getData(DRAG_TYPE)) || ids; } catch { /* keep */ }
    docDragEnd();
    await moveDocs(ids, node.path, node.path ? node.name : t('tree.root'));
  });
}

async function moveDocs(ids, folder, label) {
  let ok = 0;
  const failed = [];
  for (const id of ids) {
    const doc = State.items.find(d => d.id === id);
    if (doc && (doc.folder || '') === folder) continue;
    try {
      await api(`documents/${id}/move`, { method: 'POST', body: JSON.stringify({ folder }) });
      ok++;
    } catch (e) { failed.push(e.message); }
  }
  if (!ok && !failed.length) return;
  if (State.selected && ids.includes(State.selected.id)) closePreview();
  State.sel.clear();
  await refreshArchive();
  let msg = esc(t('op.moved', { n: ok, folder: label }));
  if (failed.length) msg += '<br>' + esc(t('op.moved.fail', { n: failed.length, err: failed[0] }));
  toast(msg, null, failed.length ? 12000 : 5000);
}

function initDocOps() {
  $('pv-trash').addEventListener('click', trashSelected);
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Delete' || !State.selected || !canWrite(State.selected)) return;
    if (!$('editor').hidden || document.querySelector('dialog[open]')) return;
    if (ev.target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName)) return;
    if ($('archive-layout').hidden) return;
    trashSelected();
  });
}

// ----------------------------------------------------- title and date

function initMeta() {
  $('pv-meta').addEventListener('click', () => {
    const doc = State.selected;
    if (!doc) return;
    $('pv-meta-title').value = doc.title;
    $('pv-meta-date').value = doc.date || new Date().toISOString().slice(0, 10);
    $('pv-meta-msg').textContent = '';
    $('pv-meta-form').hidden = false;
    $('pv-meta-title').focus();
  });
  $('pv-meta-cancel').addEventListener('click', () => { $('pv-meta-form').hidden = true; });
  $('pv-meta-form').addEventListener('keydown', ev => { if (ev.key === 'Escape') { ev.stopPropagation(); $('pv-meta-form').hidden = true; } });
  $('pv-meta-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    const doc = State.selected;
    try {
      await api(`documents/${doc.id}`, { method: 'PATCH', body: JSON.stringify({
        title: $('pv-meta-title').value, date: $('pv-meta-date').value }) });
      await refreshArchive();
      openPreview(await api(`documents/${doc.id}`));
    } catch (e) {
      $('pv-meta-msg').textContent = e.message;
    }
  });
}

// ------------------------------------------------------------- trash

async function loadTrash() {
  const { items, days } = await api('trash');
  $('trash-rule').textContent = days ? t('tr.rule', { n: days }) : t('tr.rule0');
  const rows = $('trash-rows');
  rows.innerHTML = '';
  $('trash-empty').hidden = items.length > 0;
  for (const it of items) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    const url = 'api/trash/file?path=' + encodeURIComponent(it.trash_path);
    const where = [areaLabel(it.area), it.folder || t('tree.root')].join(' · ');
    tr.innerHTML =
      `<td class="fd-table__cell col-date">${esc(formatDate(it.deleted))}${days ? `<div class="doc-folder">${esc(trashLeft(it.deleted, days))}</div>` : ''}</td>` +
      `<td class="fd-table__cell"><div class="doc-title">${esc(it.title)}</div><div class="doc-folder">${esc(formatDate(it.date))}</div></td>` +
      `<td class="fd-table__cell"><span class="doc-area"><span class="area-dot" style="--dot:${areaColor(it.area)}"></span>${esc(where)}</span></td>` +
      `<td class="fd-table__cell trash-actions"><a class="fd-button fd-button--transparent" target="_blank" rel="noopener" href="${esc(url)}">${esc(t('tr.view'))}</a>` +
      (canWrite({ area: it.area }) ? `<button type="button" class="fd-button">${esc(t('tr.restore'))}</button>` : '') + '</td>';
    const btn = tr.querySelector('button');
    if (btn) btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        await api('trash/restore', { method: 'POST', body: JSON.stringify({ trash_path: it.trash_path }) });
        toast(esc(t('tr.restored', { title: it.title, folder: it.folder || t('tree.root') })), null, 5000);
        refreshArchive();
        loadTrash();
      } catch (e) { btn.disabled = false; toast(esc(e.message)); }
    });
    rows.appendChild(tr);
  }
}

// ------------------------------------------------------- folder menu

function folderMenu(anchor, node) {
  document.querySelector('.fo-menu')?.remove();
  const menu = document.createElement('div');
  menu.className = 'fo-menu';
  menu.setAttribute('role', 'menu');
  const entries = node.path
    ? [['new', t('fo.new')], ['rename', t('fo.rename')], ['delete', t('fo.delete'), node.count > 0]]
    : [['new', t('fo.newtop')]];
  menu.innerHTML = entries.map(([k, label, off]) =>
    `<button type="button" role="menuitem" data-k="${k}"${off ? ` disabled title="${esc(t('fo.notempty'))}"` : ''}>${esc(label)}</button>`).join('');
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.left = Math.min(r.left, innerWidth - menu.offsetWidth - 8) + 'px';
  menu.style.top = (r.bottom + 4) + 'px';
  const close = ev => { if (!menu.contains(ev.target)) { menu.remove(); removeEventListener('pointerdown', close, true); } };
  addEventListener('pointerdown', close, true);
  menu.addEventListener('click', async ev => {
    const k = ev.target.dataset.k;
    if (!k) return;
    menu.remove();
    removeEventListener('pointerdown', close, true);
    try {
      if (k === 'new') {
        const name = prompt(node.path ? t('fo.new.q', { folder: node.path }) : t('fo.newtop.q'));
        if (!name || !name.trim()) return;
        const path = (node.path ? node.path + '/' : '') + name.trim().replace(/^\/+|\/+$/g, '');
        await api('folders', { method: 'POST', body: JSON.stringify({ path }) });
        if (node.path) State.open.add(node.path);
        saveOpen();
      } else if (k === 'rename') {
        const target = prompt(t('fo.rename.q'), node.path);
        if (!target || !target.trim() || target.trim() === node.path) return;
        const r = await api('folders', { method: 'PATCH', body: JSON.stringify({ old: node.path, new: target.trim() }) });
        if (State.folder === node.path || State.folder.startsWith(node.path + '/')) {
          State.folder = target.trim() + State.folder.slice(node.path.length);
          store.set('folder', State.folder);
        }
        toast(esc(t('fo.renamed', { rules: r.rules ?? 0 })), null, 5000);
      } else if (k === 'delete') {
        if (!confirm(t('fo.delete.q', { folder: node.path, name: node.path }))) return;
        await api('folders?path=' + encodeURIComponent(node.path), { method: 'DELETE' });
        if (State.folder === node.path || State.folder.startsWith(node.path + '/')) selectFolder('');
      }
      await refreshArchive();
    } catch (e) {
      toast(esc(e.message));
    }
  });
}

// ------------------------------------------------------------ Mappen

async function loadMappen() {
  try { State.mappen = await api('mappen?' + areaParam()); } catch { return; }
  if (State.mappe && !State.mappen.some(m => m.name === State.mappe)) State.mappe = null;
  renderMappen();
}

function renderMappen() {
  const box = $('mappen');
  if (!box) return;
  const list = State.mappen || [];
  box.innerHTML = list.length ? '' : `<p class="mappen-empty">${esc(t('mp.empty'))}</p>`;
  for (const m of list) {
    const row = document.createElement('div');
    row.className = 'tree-row mappe-row' + (State.mappe === m.name ? ' is-selected' : '') + (m.count ? '' : ' is-empty');
    row.style.setProperty('--depth', 0);
    row.setAttribute('role', 'treeitem');
    row.title = areaLabel(m.area);
    row.innerHTML = `<span class="tree-caret">📎</span><span class="tree-name">${esc(m.name)}</span>` +
      `<span class="area-dot" style="--dot:${areaColor(m.area)}"></span>` +
      `<span class="tree-count">${m.count}</span>` +
      `<button type="button" class="tree-menu" aria-label="${esc(t('fo.menu'))}">⋯</button>`;
    row.addEventListener('click', () => selectMappe(m.name));
    const menuBtn = row.querySelector('.tree-menu');
    if (menuBtn) menuBtn.addEventListener('click', ev => { ev.stopPropagation(); mappeMenu(menuBtn, m); });
    mappeDropTarget(row, m);
    box.appendChild(row);
  }
}

function selectMappe(name) {
  State.mappe = name;
  State.tags = new Set([name]);
  State.query = '';
  $('search').value = '';
  $('tree-panel').classList.remove('is-open');
  renderTree();
  renderMappen();
  loadDocs();
}

async function newMappe() {
  const r = await mappeDialog(null);
  if (!r) return;
  await loadMappen();
  selectMappe(r.name);
}

// New or existing Mappe: name and the area it belongs to. Resolves {name} or null.
function mappeDialog(m) {
  const dlg = $('mp-dlg');
  const writable = State.areas.map(a => a.name).filter(a => a && (State.me.write_areas || []).includes(a));
  const preferred = m ? m.area
    : (State.active.size === 1 ? [...State.active][0] : (writable.includes('gemeinsam') ? 'gemeinsam' : writable[0]));
  $('mp-dlg-title').textContent = m ? t('mp.edit') : t('mp.new');
  $('mp-name').value = m ? m.name : '';
  $('mp-area').innerHTML = writable.map(a => `<option value="${esc(a)}">${esc(areaLabel(a))}</option>`).join('');
  $('mp-area').value = writable.includes(preferred) ? preferred : writable[0] || '';
  $('mp-msg').textContent = '';
  return new Promise(resolve => {
    let done = null;
    $('mp-cancel').onclick = () => dlg.close();
    $('mp-form').onsubmit = async ev => {
      ev.preventDefault();
      const name = $('mp-name').value.trim(), area = $('mp-area').value;
      try {
        if (m) {
          await api('mappen', { method: 'PATCH', body: JSON.stringify({ old: m.name, new: name, area }) });
          done = { name };
        } else {
          done = await api('mappen', { method: 'POST', body: JSON.stringify({ name, area }) });
        }
        dlg.close();
      } catch (e) { $('mp-msg').textContent = e.message; }
    };
    dlg.onclose = () => resolve(done);
    dlg.showModal();
    $('mp-name').focus();
  });
}

function mappeDropTarget(row, m) {
  row.addEventListener('dragover', ev => {
    if (!ev.dataTransfer.types.includes(DRAG_TYPE)) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = 'link';
    row.classList.add('is-drop');
  });
  row.addEventListener('dragleave', () => row.classList.remove('is-drop'));
  row.addEventListener('drop', async ev => {
    ev.preventDefault();
    row.classList.remove('is-drop');
    let ids = dragIds;
    try { ids = JSON.parse(ev.dataTransfer.getData(DRAG_TYPE)) || ids; } catch { /* keep */ }
    docDragEnd();
    try {
      await api('tags/change', { method: 'POST', body: JSON.stringify({ ids, add: [m.name] }) });
      toast(esc(t('mp.added', { n: ids.length, name: m.name })), null, 4000);
      loadTags();
      loadDocs();
    } catch (e) { toast(esc(e.message)); }
  });
}

function mappeMenu(anchor, m) {
  document.querySelector('.fo-menu')?.remove();
  const menu = document.createElement('div');
  menu.className = 'fo-menu';
  menu.setAttribute('role', 'menu');
  const q = 'api/mappen/download?name=' + encodeURIComponent(m.name);
  menu.innerHTML =
    `<a role="menuitem" href="${esc(q)}&format=zip"${m.count ? '' : ' aria-disabled="true"'}>${esc(t('mp.zip'))}</a>` +
    `<a role="menuitem" href="${esc(q)}&format=pdf"${m.count ? '' : ' aria-disabled="true"'}>${esc(t('mp.pdf'))}</a>` +
    (m.writable ? `<button type="button" role="menuitem" data-k="rename">${esc(t('mp.rename'))}</button>` +
    `<button type="button" role="menuitem" data-k="delete">${esc(t('mp.delete'))}</button>` : '');
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.left = Math.min(r.left, innerWidth - menu.offsetWidth - 8) + 'px';
  menu.style.top = Math.min(r.bottom + 4, innerHeight - menu.offsetHeight - 8) + 'px';
  const close = ev => { if (!menu.contains(ev.target)) { menu.remove(); removeEventListener('pointerdown', close, true); } };
  addEventListener('pointerdown', close, true);
  menu.addEventListener('click', async ev => {
    const el = ev.target.closest('[role=menuitem]');
    if (!el) return;
    if (el.getAttribute('aria-disabled') === 'true') { ev.preventDefault(); return; }
    menu.remove();
    removeEventListener('pointerdown', close, true);
    const k = el.dataset.k;
    if (!k) return;                 // download links do their own thing
    try {
      if (k === 'rename') {
        const r = await mappeDialog(m);
        if (!r) return;
        if (State.mappe === m.name) { State.mappe = r.name; State.tags = new Set([r.name]); }
      } else if (k === 'delete') {
        if (!confirm(t('mp.delete.q', { name: m.name }))) return;
        await api('mappen?name=' + encodeURIComponent(m.name), { method: 'DELETE' });
        if (State.mappe === m.name) { State.mappe = null; State.tags.clear(); }
      }
      await loadTags();
      loadDocs();
    } catch (e) { toast(esc(e.message)); }
  });
}

function trashLeft(deleted, days) {
  const gone = new Date(deleted + 'T00:00:00');
  gone.setDate(gone.getDate() + days);
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const left = Math.round((gone - today) / 86400000);
  return left > 0 ? t('tr.left', { n: left }) : t('tr.today');
}

// ------------------------------------------------------------ upload

const readB64 = file => new Promise((resolve, reject) => {
  const r = new FileReader();
  r.onload = () => resolve(String(r.result).split(',', 2)[1] || '');
  r.onerror = () => reject(r.error);
  r.readAsDataURL(file);
});

function initUpload() {
  $('ib-upload').addEventListener('click', () => { $('ib-file').value = ''; $('ib-file').click(); });
  $('ib-file').addEventListener('change', async () => {
    const files = [...$('ib-file').files];
    if (!files.length) return;
    const joinable = files.every(f => /\.(pdf|jpe?g|png|heic|heif|tiff?|webp)$/i.test(f.name) || f.type.startsWith('image/'));
    const combine = files.length > 1 && joinable && confirm(t('ib.up.combine.q', { n: files.length }));
    const btn = $('ib-upload');
    btn.disabled = true;
    toast(esc(t('ib.up.busy', { n: files.length })), null, 60000);
    try {
      const payload = { combine, files: [] };
      for (const f of files) {
        // iOS sometimes hands over camera pictures as "image.jpg" without a usable name
        const name = /\.[a-z0-9]+$/i.test(f.name) ? f.name : (f.name || 'Foto') + '.' + ((f.type.split('/')[1] || 'jpg').replace('jpeg', 'jpg'));
        payload.files.push({ name, data: await readB64(f) });
      }
      const r = await api('inbox/upload', { method: 'POST', body: JSON.stringify(payload) });
      toast(esc(t('ib.up.done', { n: r.names.length })), null, 4000);
      $('ib-status').value = 'new';
      setTimeout(async () => {
        await loadInbox();
        const hit = (Inb.data?.items || []).find(i => r.names.includes(i.name));
        if (hit) { Inb.key = hit.key; renderInboxList(); showItem(hit); }
      }, 800);
    } catch (e) {
      toast(esc(errText(e)), null, 10000);
    } finally {
      btn.disabled = false;
    }
  });
}
