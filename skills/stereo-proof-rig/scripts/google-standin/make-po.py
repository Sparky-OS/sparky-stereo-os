#!/usr/bin/python3
"""make-po.py PO_DIR: the desktop integration's strings in the edition's ten languages (English in the code).

Appends to po/pt_BR.po the entries it lacks and writes po/LANG.po for pl, fr, de, es, ja, ko, zh_CN and zh_TW with these
strings only (the rest of DriveSync stays English there until its author's catalogues exist). Every {placeholder} of the
English sentence must be in each translation; the script stops otherwise.
"""
import os
import re
import sys

LANGS = ['pl', 'pt_BR', 'fr', 'de', 'es', 'ja', 'ko', 'zh_CN', 'zh_TW']
PLURAL = {'pl': 'nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);',
	'pt_BR': 'nplurals=2; plural=(n > 1);', 'fr': 'nplurals=2; plural=(n > 1);', 'de': 'nplurals=2; plural=(n != 1);',
	'es': 'nplurals=2; plural=(n != 1);', 'ja': 'nplurals=1; plural=0;', 'ko': 'nplurals=1; plural=0;',
	'zh_CN': 'nplurals=1; plural=0;', 'zh_TW': 'nplurals=1; plural=0;'}
TEAM = {'pl': 'Polish', 'pt_BR': 'Brazilian Portuguese', 'fr': 'French', 'de': 'German', 'es': 'Spanish', 'ja': 'Japanese',
	'ko': 'Korean', 'zh_CN': 'Chinese (simplified)', 'zh_TW': 'Chinese (traditional)'}

T = {
'Synchronization is not running': ['Synchronizacja nie jest uruchomiona', 'A sincronização não está em execução', "La synchronisation n'est pas en cours", 'Die Synchronisation läuft nicht', 'La sincronización no está en marcha', '同期は実行されていません', '동기화가 실행되고 있지 않습니다', '同步未在运行', '同步未在執行'],
'Google Drive is up to date': ['Dysk Google jest aktualny', 'O Google Drive está atualizado', 'Google Drive est à jour', 'Google Drive ist auf dem neuesten Stand', 'Google Drive está al día', 'Google ドライブは最新の状態です', 'Google 드라이브가 최신 상태입니다', 'Google 云端硬盘已是最新', 'Google 雲端硬碟已是最新狀態'],
'Synchronizing with Google Drive…': ['Synchronizowanie z Dyskiem Google…', 'Sincronizando com o Google Drive…', 'Synchronisation avec Google Drive…', 'Wird mit Google Drive synchronisiert …', 'Sincronizando con Google Drive…', 'Google ドライブと同期しています…', 'Google 드라이브와 동기화하는 중…', '正在与 Google 云端硬盘同步…', '正在與 Google 雲端硬碟同步…'],
'A file changed on both sides': ['Plik zmienił się po obu stronach', 'Um arquivo mudou nos dois lados', 'Un fichier a changé des deux côtés', 'Eine Datei wurde auf beiden Seiten geändert', 'Un archivo cambió en ambos lados', 'ファイルが両側で変更されました', '파일이 양쪽에서 변경되었습니다', '有文件在两端都被更改', '有檔案在兩端都被變更'],
'DriveSync needs your decision': ['DriveSync potrzebuje Twojej decyzji', 'O DriveSync precisa da sua decisão', 'DriveSync attend votre décision', 'DriveSync braucht Ihre Entscheidung', 'DriveSync necesita tu decisión', 'DriveSync はあなたの判断を必要としています', 'DriveSync에 결정이 필요합니다', 'DriveSync 需要你做出决定', 'DriveSync 需要您做出決定'],
'Synchronization failed': ['Synchronizacja nie powiodła się', None, 'La synchronisation a échoué', 'Synchronisation fehlgeschlagen', 'La sincronización falló', '同期に失敗しました', '동기화에 실패했습니다', '同步失败', '同步失敗'],
'Google Drive': ['Dysk Google', 'Google Drive', 'Google Drive', 'Google Drive', 'Google Drive', 'Google ドライブ', 'Google 드라이브', 'Google 云端硬盘', 'Google 雲端硬碟'],
'Synchronization waits because the connection is metered.': ['Synchronizacja czeka, ponieważ połączenie jest taryfowe.', 'A sincronização aguarda porque a conexão é limitada.', 'La synchronisation attend, car la connexion est limitée.', 'Die Synchronisation wartet, weil die Verbindung getaktet ist.', 'La sincronización espera porque la conexión es de uso medido.', '接続が従量制課金のため、同期は待機しています。', '데이터 통신 연결이므로 동기화가 대기 중입니다.', '由于连接按流量计费，同步正在等待。', '由於連線為計量付費，同步正在等候。'],
'Open DriveSync': ['Otwórz DriveSync', 'Abrir o DriveSync', 'Ouvrir DriveSync', 'DriveSync öffnen', 'Abrir DriveSync', 'DriveSync を開く', 'DriveSync 열기', '打开 DriveSync', '開啟 DriveSync'],
'{account}: the changes were synchronized.': ['{account}: zmiany zostały zsynchronizowane.', '{account}: as alterações foram sincronizadas.', '{account} : les modifications ont été synchronisées.', '{account}: Die Änderungen wurden synchronisiert.', '{account}: los cambios se sincronizaron.', '{account}: 変更を同期しました。', '{account}: 변경 사항을 동기화했습니다.', '{account}：更改已同步。', '{account}：變更已同步。'],
'{account}: an item could not be synchronized. It stays listed in DriveSync until it is resolved.': ['{account}: nie udało się zsynchronizować elementu. Pozostaje on na liście w DriveSync, dopóki problem nie zostanie rozwiązany.', '{account}: um item não pôde ser sincronizado. Ele continua listado no DriveSync até ser resolvido.', "{account} : un élément n'a pas pu être synchronisé. Il reste listé dans DriveSync jusqu'à ce qu'il soit résolu.", '{account}: Ein Element konnte nicht synchronisiert werden. Es bleibt in DriveSync aufgeführt, bis es gelöst ist.', '{account}: no se pudo sincronizar un elemento. Seguirá en la lista de DriveSync hasta que se resuelva.', '{account}: 項目を同期できませんでした。解決するまで DriveSync に表示されたままになります。', '{account}: 항목을 동기화할 수 없습니다. 해결될 때까지 DriveSync 목록에 남아 있습니다.', '{account}：有一个项目无法同步。在解决之前，它会一直列在 DriveSync 中。', '{account}：有一個項目無法同步。在解決之前，它會一直列在 DriveSync 中。'],
'{account}: choose which version to keep. Nothing was overwritten.': ['{account}: wybierz, którą wersję zachować. Nic nie zostało nadpisane.', '{account}: escolha qual versão manter. Nada foi sobrescrito.', "{account} : choisissez la version à conserver. Rien n'a été écrasé.", '{account}: Wählen Sie, welche Version behalten werden soll. Nichts wurde überschrieben.', '{account}: elige qué versión conservar. No se sobrescribió nada.', '{account}: 残すバージョンを選んでください。何も上書きされていません。', '{account}: 유지할 버전을 선택하세요. 아무것도 덮어쓰지 않았습니다.', '{account}：请选择要保留的版本。没有任何内容被覆盖。', '{account}：請選擇要保留的版本。沒有任何內容被覆寫。'],
'{account}: synchronization waits until you review the folder in DriveSync.': ['{account}: synchronizacja czeka, aż przejrzysz folder w DriveSync.', '{account}: a sincronização aguarda até você revisar a pasta no DriveSync.', '{account} : la synchronisation attend que vous vérifiiez le dossier dans DriveSync.', '{account}: Die Synchronisation wartet, bis Sie den Ordner in DriveSync überprüfen.', '{account}: la sincronización espera hasta que revises la carpeta en DriveSync.', '{account}: DriveSync でフォルダーを確認するまで同期は待機します。', '{account}: DriveSync에서 폴더를 검토할 때까지 동기화가 대기합니다.', '{account}：在你于 DriveSync 中检查该文件夹之前，同步会一直等待。', '{account}：在您於 DriveSync 中檢查該資料夾之前，同步會一直等候。'],
'Synchronization waits': ['Synchronizacja czeka', 'A sincronização aguarda', 'La synchronisation attend', 'Die Synchronisation wartet', 'La sincronización espera', '同期は待機中です', '동기화 대기 중', '同步正在等待', '同步正在等候'],
'The connection is metered, so DriveSync does not download or upload. It continues by itself on a connection that is not metered, or when you allow metered connections in Preferences.': ['Połączenie jest taryfowe, więc DriveSync niczego nie pobiera ani nie wysyła. Wznowi pracę samodzielnie po połączeniu, które nie jest taryfowe, albo gdy zezwolisz na połączenia taryfowe w Preferencjach.', 'A conexão é limitada, então o DriveSync não baixa nem envia nada. Ele continua sozinho em uma conexão que não seja limitada ou quando você permitir conexões limitadas nas Preferências.', "La connexion est limitée : DriveSync ne télécharge ni n'envoie rien. Il reprend de lui-même sur une connexion non limitée, ou lorsque vous autorisez les connexions limitées dans les Préférences.", 'Die Verbindung ist getaktet, daher lädt DriveSync nichts herunter oder hoch. Es setzt von selbst fort, sobald die Verbindung nicht mehr getaktet ist oder wenn Sie getaktete Verbindungen in den Einstellungen erlauben.', 'La conexión es de uso medido, así que DriveSync no descarga ni sube nada. Continuará por sí solo en una conexión que no sea de uso medido, o cuando permitas las conexiones de uso medido en Preferencias.', '接続が従量制課金のため、DriveSync はダウンロードもアップロードも行いません。従量制課金ではない接続になるか、設定で従量制課金接続を許可すると、自動的に再開します。', '데이터 통신 연결이므로 DriveSync는 다운로드나 업로드를 하지 않습니다. 데이터 통신 연결이 아닌 연결에서, 또는 환경 설정에서 데이터 통신 연결을 허용하면 자동으로 계속합니다.', '当前连接按流量计费，因此 DriveSync 不会下载或上传。连接不再按流量计费时，或你在“首选项”中允许按流量计费的连接后，它会自动继续。', '目前連線為計量付費，因此 DriveSync 不會下載或上傳。連線不再計量付費時，或您在「偏好設定」中允許計量付費連線後，它會自動繼續。'],
'Synchronization waits: the connection is metered': ['Synchronizacja czeka: połączenie jest taryfowe', 'A sincronização aguarda: a conexão é limitada', 'La synchronisation attend : la connexion est limitée', 'Die Synchronisation wartet: Die Verbindung ist getaktet', 'La sincronización espera: la conexión es de uso medido', '同期は待機中です: 接続が従量制課金です', '동기화 대기 중: 데이터 통신 연결입니다', '同步正在等待：连接按流量计费', '同步正在等候：連線為計量付費'],
'Quit': ['Zakończ', None, 'Quitter', 'Beenden', 'Salir', '終了', '끝내기', '退出', '結束'],
'Network': ['Sieć', 'Rede', 'Réseau', 'Netzwerk', 'Red', 'ネットワーク', '네트워크', '网络', '網路'],
'Synchronize on Metered Connections': ['Synchronizuj przez połączenia taryfowe', 'Sincronizar em conexões limitadas', 'Synchroniser sur les connexions limitées', 'Über getaktete Verbindungen synchronisieren', 'Sincronizar en conexiones de uso medido', '従量制課金接続で同期する', '데이터 통신 연결에서 동기화', '在按流量计费的连接上同步', '在計量付費連線上同步'],
'When off, synchronization waits while the connection is metered and continues by itself afterwards': ['Gdy wyłączone, synchronizacja czeka, dopóki połączenie jest taryfowe, a potem wznawia się samoczynnie', 'Quando desativado, a sincronização aguarda enquanto a conexão for limitada e depois continua sozinha', "Si désactivé, la synchronisation attend tant que la connexion est limitée, puis reprend d'elle-même", 'Wenn ausgeschaltet, wartet die Synchronisation, solange die Verbindung getaktet ist, und setzt danach von selbst fort', 'Si está desactivado, la sincronización espera mientras la conexión sea de uso medido y después continúa por sí sola', 'オフのときは、接続が従量制課金の間は同期を待機し、その後自動的に再開します', '끄면 데이터 통신 연결인 동안 동기화가 대기하고 이후 자동으로 계속합니다', '关闭时，连接按流量计费期间同步会等待，之后自动继续', '關閉時，連線為計量付費期間同步會等候，之後自動繼續'],
'Add local folder to Places': ['Dodaj lokalny folder do Miejsc', 'Adicionar a pasta local aos Locais', 'Ajouter le dossier local aux Emplacements', 'Lokalen Ordner zu den Orten hinzufügen', 'Añadir la carpeta local a Lugares', 'ローカルフォルダーを場所に追加', '로컬 폴더를 위치에 추가', '将本地文件夹添加到位置', '將本機資料夾加入位置'],
'Google Drive ({account})': ['Dysk Google ({account})', 'Google Drive ({account})', 'Google Drive ({account})', 'Google Drive ({account})', 'Google Drive ({account})', 'Google ドライブ ({account})', 'Google 드라이브 ({account})', 'Google 云端硬盘（{account}）', 'Google 雲端硬碟（{account}）'],
'The local folder was added to Places.': ['Lokalny folder został dodany do Miejsc.', 'A pasta local foi adicionada aos Locais.', 'Le dossier local a été ajouté aux Emplacements.', 'Der lokale Ordner wurde zu den Orten hinzugefügt.', 'La carpeta local se añadió a Lugares.', 'ローカルフォルダーを場所に追加しました。', '로컬 폴더를 위치에 추가했습니다.', '本地文件夹已添加到位置。', '本機資料夾已加入位置。'],
'The local folder is already in Places.': ['Lokalny folder jest już w Miejscach.', 'A pasta local já está nos Locais.', 'Le dossier local est déjà dans les Emplacements.', 'Der lokale Ordner ist bereits unter den Orten.', 'La carpeta local ya está en Lugares.', 'ローカルフォルダーはすでに場所にあります。', '로컬 폴더가 이미 위치에 있습니다.', '本地文件夹已在位置中。', '本機資料夾已在位置中。'],
'Places could not be changed. Nothing was written.': ['Nie udało się zmienić Miejsc. Nic nie zostało zapisane.', 'Não foi possível alterar os Locais. Nada foi gravado.', "Impossible de modifier les Emplacements. Rien n'a été écrit.", 'Die Orte konnten nicht geändert werden. Es wurde nichts geschrieben.', 'No se pudieron cambiar los Lugares. No se escribió nada.', '場所を変更できませんでした。何も書き込まれていません。', '위치를 변경할 수 없습니다. 아무것도 기록하지 않았습니다.', '无法更改位置。未写入任何内容。', '無法變更位置。未寫入任何內容。'],
'Preferences': ['Preferencje', None, 'Préférences', 'Einstellungen', 'Preferencias', '設定', '환경 설정', '首选项', '偏好設定'],
'The configuration is incomplete.': ['Konfiguracja jest niekompletna.', None, 'La configuration est incomplète.', 'Die Konfiguration ist unvollständig.', 'La configuración está incompleta.', '設定が不完全です。', '구성이 완료되지 않았습니다.', '配置不完整。', '設定不完整。'],
'Saved configuration could not be read. Your account has been preserved.': ['Nie udało się odczytać zapisanej konfiguracji. Twoje konto zostało zachowane.', None, "La configuration enregistrée n'a pas pu être lue. Votre compte a été conservé.", 'Die gespeicherte Konfiguration konnte nicht gelesen werden. Ihr Konto wurde beibehalten.', 'No se pudo leer la configuración guardada. Tu cuenta se ha conservado.', '保存された設定を読み込めませんでした。アカウントは保持されています。', '저장된 구성을 읽을 수 없습니다. 계정은 그대로 유지됩니다.', '无法读取已保存的配置。你的账户已保留。', '無法讀取已儲存的設定。您的帳戶已保留。'],
}


def quote(text):
	return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def entry(msgid, msgstr):
	return f'msgid {quote(msgid)}\nmsgstr {quote(msgstr)}\n'


def main(po_dir):
	for msgid, row in T.items():
		assert len(row) == len(LANGS), msgid
		want = set(re.findall(r'\{\w+\}', msgid))
		for lang, text in zip(LANGS, row):
			if text is not None and set(re.findall(r'\{\w+\}', text)) != want:
				sys.exit(f'{lang}: placeholders differ for {msgid!r}')
	for index, lang in enumerate(LANGS):
		path = os.path.join(po_dir, f'{lang}.po')
		if lang == 'pt_BR':
			text = open(path, encoding='utf-8').read()
			add = [entry(m, row[index]) for m, row in T.items() if row[index] is not None and f'msgid {quote(m)}\n' not in text]
			with open(path, 'a', encoding='utf-8') as f:
				f.write('\n' + '\n'.join(add))
			print(f'{lang}: {len(add)} entries appended')
			continue
		head = ('msgid ""\nmsgstr ""\n"Project-Id-Version: DriveSync\\n"\n"Report-Msgid-Bugs-To: \\n"\n"PO-Revision-Date: 2026-11-27 00:00+0000\\n"\n'
			'"Last-Translator: Sparky Stereo OS\\n"\n'
			f'"Language-Team: {TEAM[lang]}\\n"\n"Language: {lang}\\n"\n"MIME-Version: 1.0\\n"\n'
			'"Content-Type: text/plain; charset=UTF-8\\n"\n"Content-Transfer-Encoding: 8bit\\n"\n'
			f'"Plural-Forms: {PLURAL[lang]}\\n"\n')
		body = [entry(m, row[index]) for m, row in T.items()]
		with open(path, 'w', encoding='utf-8') as f:
			f.write(head + '\n' + '\n'.join(body))
		print(f'{lang}: {len(body)} entries written')


main(sys.argv[1])
