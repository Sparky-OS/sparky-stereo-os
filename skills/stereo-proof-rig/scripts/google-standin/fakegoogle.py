#!/usr/bin/python3
"""fakegoogle.py: a local stand-in for the Google endpoints DriveSync calls, for proofs without a Google account.

Serves, on one TLS port (the rig maps the four host names to 127.0.0.1 and trusts the rig's own CA):
  accounts.google.com            /o/oauth2/v2/auth (consent granted at once: 302 to the loopback redirect with code and
                                 state), /.well-known/openid-configuration
  oauth2.googleapis.com          /token (authorization_code with PKCE S256, refresh_token), /revoke
  openidconnect.googleapis.com   /v1/userinfo
  www.googleapis.com             /oauth2/v3/certs, Drive v3 files, changes, generateIds, about, Drive v2 file reads and
                                 conditional PATCH (strong ETags), resumable uploads on /upload/drive/v3 and /upload/drive/v2
The requests and responses follow Google's public references (Drive API v3 and v2, OAuth 2.0 for installed apps, OpenID
Connect) and the shapes DriveSync's provider parses (engine/src/providers/google). One synthetic user; nothing is real.
A plain HTTP admin port (loopback) lets the test driver read the log and the tree, change remote files, make the next
upload fail with Drive's own storageQuotaExceeded error, and set the access token lifetime.
Usage: fakegoogle.py CERT KEY STATE_DIR [TLS_PORT [ADMIN_PORT]]
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import ssl
import sys
import threading
import time
import urllib.parse

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

CERT, KEY, STATE = sys.argv[1], sys.argv[2], sys.argv[3]
TLS_PORT = int(sys.argv[4]) if len(sys.argv) > 4 else 443
ADMIN_PORT = int(sys.argv[5]) if len(sys.argv) > 5 else 8099
os.makedirs(STATE, exist_ok=True)
LOCK = threading.RLock()
FOLDER = 'application/vnd.google-apps.folder'
ROOT = '0AFakeRootFolderIdRig299AAA'
SUBJECT = '109876543210987654321'
EMAIL = 'drivesync-rig@example.invalid'
AUTH = 'https://accounts.google.com/o/oauth2/v2/auth'

signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KID = 'rig299-' + secrets.token_hex(4)


def b64u(data):
	return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def jwk():
	numbers = signing_key.public_key().public_numbers()
	n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, 'big')
	e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, 'big')
	return {'kty': 'RSA', 'alg': 'RS256', 'use': 'sig', 'kid': KID, 'n': b64u(n), 'e': b64u(e)}


def id_token(audience, nonce=None):
	now = int(time.time())
	claims = {'iss': 'https://accounts.google.com', 'aud': audience, 'azp': audience, 'sub': SUBJECT, 'email': EMAIL,
		'email_verified': True, 'name': 'Rig Person', 'iat': now, 'exp': now + 3600}
	if nonce:
		claims['nonce'] = nonce
	head = b64u(json.dumps({'alg': 'RS256', 'kid': KID, 'typ': 'JWT'}).encode())
	body = b64u(json.dumps(claims).encode())
	signature = signing_key.sign(f'{head}.{body}'.encode(), padding.PKCS1v15(), hashes.SHA256())
	return f'{head}.{body}.{b64u(signature)}'


def stamp(t=None):
	return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(t or time.time()))


class Drive:
	def __init__(self):
		self.files = {ROOT: {'id': ROOT, 'name': 'My Drive', 'mimeType': FOLDER, 'parents': [], 'trashed': False,
			'version': 1, 'created': time.time(), 'modified': time.time(), 'content': None,
			'appProperties': {}, 'properties': {}}}
		self.changes = []
		self.counter = 0
		self.uploads = {}
		self.codes = {}
		self.access = {}
		self.refresh = {}
		self.ttl = 3600
		self.fail_upload = set()
		self.log = []
		self.issued = []

	def new_id(self):
		self.counter += 1
		return f'fake{self.counter:06d}' + secrets.token_hex(6)

	def touch(self, f, content_changed=False):
		f['version'] += 1
		f['modified'] = time.time()
		if content_changed:
			f['revision'] = secrets.token_hex(8)
		self.changes.append(f['id'])

	def etag(self, f):
		return '"' + hashlib.sha1(f"{f['id']}:{f['version']}".encode()).hexdigest() + '"'

	def v3(self, f):
		out = {'kind': 'drive#file', 'id': f['id'], 'name': f['name'], 'mimeType': f['mimeType'],
			'parents': list(f['parents']), 'trashed': f['trashed'], 'explicitlyTrashed': f['trashed'],
			'version': str(f['version']), 'createdTime': stamp(f['created']), 'modifiedTime': stamp(f['modified']),
			'appProperties': dict(f['appProperties']), 'properties': dict(f['properties']),
			'webViewLink': f"https://drive.google.com/file/d/{f['id']}/view",
			'capabilities': {k: True for k in ('canEdit', 'canTrash', 'canUntrash', 'canRename', 'canAddChildren',
				'canDelete', 'canDownload', 'canModifyContent', 'canMoveItemWithinDrive', 'canRemoveChildren',
				'canReadRevisions', 'canTrashChildren', 'canListChildren', 'canCopy')},
			'ownedByMe': True, 'spaces': ['drive']}
		if f['id'] == ROOT:
			out['parents'] = []
		if f['content'] is not None:
			data = f['content']
			out.update({'size': str(len(data)), 'quotaBytesUsed': str(len(data)), 'md5Checksum': hashlib.md5(data).hexdigest(),
				'sha1Checksum': hashlib.sha1(data).hexdigest(), 'sha256Checksum': hashlib.sha256(data).hexdigest(),
				'headRevisionId': f.get('revision', 'r0')})
		return out

	def v2(self, f):
		v3 = self.v3(f)
		out = {'kind': 'drive#file', 'id': f['id'], 'etag': self.etag(f), 'title': f['name'], 'mimeType': f['mimeType'],
			'labels': {'trashed': f['trashed']}, 'parents': [{'id': p} for p in f['parents']], 'version': str(f['version']),
			'createdDate': v3['createdTime'], 'modifiedDate': v3['modifiedTime'],
			'properties': [{'key': k, 'value': v, 'visibility': 'PRIVATE'} for k, v in f['appProperties'].items()]
			+ [{'key': k, 'value': v, 'visibility': 'PUBLIC'} for k, v in f['properties'].items()],
			'capabilities': v3['capabilities']}
		for k in ('md5Checksum', 'sha256Checksum', 'headRevisionId'):
			if k in v3:
				out[k] = v3[k]
		if 'size' in v3:
			out['fileSize'] = v3['size']
		return out

	def resolve(self, fid):
		return ROOT if fid == 'root' else fid


D = Drive()


def matches(f, q):
	if not q:
		return not f['trashed'] and f['id'] != ROOT
	for clause in q.split(' and '):
		clause = clause.strip()
		if clause.endswith(' in parents'):
			want = D.resolve(clause[:-len(' in parents')].strip().strip("'").replace("\\'", "'"))
			if want not in f['parents']:
				return False
		elif clause.startswith('name = '):
			if f['name'] != clause[len('name = '):].strip("'").replace("\\'", "'"):
				return False
		elif clause.startswith('mimeType = '):
			if f['mimeType'] != clause[len('mimeType = '):].strip("'"):
				return False
		elif clause.startswith('trashed = '):
			if f['trashed'] != (clause[len('trashed = '):].strip() == 'true'):
				return False
		else:
			raise ValueError(f'unsupported q clause {clause!r}')
	return True


def google_error(code, reason, message):
	return code, {'error': {'code': code, 'message': message, 'errors': [{'domain': 'global', 'reason': reason,
		'message': message}], 'status': {400: 'INVALID_ARGUMENT', 401: 'UNAUTHENTICATED', 403: 'PERMISSION_DENIED',
		404: 'NOT_FOUND', 412: 'FAILED_PRECONDITION'}.get(code, 'UNKNOWN')}}


class Handler(http.server.BaseHTTPRequestHandler):
	protocol_version = 'HTTP/1.1'
	server_version = 'fakegoogle'

	def log_message(self, *args):
		pass

	def reply(self, code, body=None, headers=None, raw=None, ctype='application/json; charset=UTF-8'):
		data = raw if raw is not None else (json.dumps(body).encode() if body is not None else b'')
		self.send_response(code)
		for k, v in (headers or {}).items():
			self.send_header(k, v)
		if data or code not in (204, 304):
			self.send_header('Content-Type', ctype)
		self.send_header('Content-Length', str(len(data)))
		self.end_headers()
		if self.command != 'HEAD':
			self.wfile.write(data)
		host = (self.headers.get('Host') or '').split(':')[0]
		with LOCK:
			D.log.append({'t': round(time.time(), 3), 'host': host, 'method': self.command,
				'path': urllib.parse.urlsplit(self.path).path, 'query': urllib.parse.urlsplit(self.path).query[:300],
				'status': code})

	def body(self):
		n = int(self.headers.get('Content-Length') or 0)
		return self.rfile.read(n) if n else b''

	def bearer(self):
		value = self.headers.get('Authorization') or ''
		token = value[7:] if value.startswith('Bearer ') else None
		with LOCK:
			expiry = D.access.get(token)
		return token if expiry and expiry > time.time() else None

	def do_GET(self):
		self.route('GET')

	def do_POST(self):
		self.route('POST')

	def do_PATCH(self):
		self.route('PATCH')

	def do_PUT(self):
		self.route('PUT')

	def do_DELETE(self):
		self.route('DELETE')

	def route(self, method):
		url = urllib.parse.urlsplit(self.path)
		query = dict(urllib.parse.parse_qsl(url.query, keep_blank_values=True))
		host = (self.headers.get('Host') or '').split(':')[0]
		path = url.path
		try:
			with LOCK:
				if host == 'accounts.google.com':
					return self.accounts(method, path, query)
				if host == 'oauth2.googleapis.com':
					return self.oauth(method, path)
				if host == 'openidconnect.googleapis.com' and path == '/v1/userinfo':
					if not self.bearer():
						return self.reply(*google_error(401, 'authError', 'Invalid Credentials'))
					return self.reply(200, {'sub': SUBJECT, 'email': EMAIL, 'email_verified': True, 'name': 'Rig Person'})
				if host == 'www.googleapis.com':
					if path == '/oauth2/v3/certs':
						return self.reply(200, {'keys': [jwk()]})
					if not self.bearer():
						return self.reply(*google_error(401, 'authError', 'Invalid Credentials'))
					return self.drive(method, path, query)
				return self.reply(404, {'error': 'unknown host ' + host})
		except ValueError as error:
			return self.reply(*google_error(400, 'invalid', str(error)))

	def accounts(self, method, path, query):
		if path == '/.well-known/openid-configuration':
			return self.reply(200, {'issuer': 'https://accounts.google.com', 'authorization_endpoint': AUTH,
				'token_endpoint': 'https://oauth2.googleapis.com/token',
				'userinfo_endpoint': 'https://openidconnect.googleapis.com/v1/userinfo',
				'revocation_endpoint': 'https://oauth2.googleapis.com/revoke',
				'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs', 'response_types_supported': ['code'],
				'subject_types_supported': ['public'], 'id_token_signing_alg_values_supported': ['RS256']})
		if path == '/o/oauth2/v2/auth':
			redirect = query.get('redirect_uri', '')
			host = urllib.parse.urlsplit(redirect).hostname
			if query.get('response_type') != 'code' or host not in ('127.0.0.1', 'localhost', '::1') \
					or query.get('code_challenge_method') != 'S256' or 'https://www.googleapis.com/auth/drive' not in query.get('scope', ''):
				return self.reply(400, {'error': 'invalid_request'})
			code = secrets.token_urlsafe(24)
			D.codes[code] = {'challenge': query['code_challenge'], 'client': query.get('client_id'), 'redirect': redirect,
				'nonce': query.get('nonce')}
			target = redirect + ('&' if '?' in redirect else '?') + urllib.parse.urlencode({'code': code, 'state': query.get('state', ''), 'scope': query.get('scope', '')})
			return self.reply(302, headers={'Location': target})
		return self.reply(404, {'error': 'not found'})

	def tokens(self, client, refresh=None, nonce=None, first=False):
		access = 'ya29.rig-' + secrets.token_urlsafe(24)
		D.access[access] = time.time() + D.ttl
		D.issued.append({'t': round(time.time(), 3), 'grant': 'refresh_token' if refresh is None and not first else 'authorization_code',
			'access_sha256_12': hashlib.sha256(access.encode()).hexdigest()[:12], 'expires_in': D.ttl})
		out = {'access_token': access, 'expires_in': D.ttl, 'token_type': 'Bearer',
			'scope': 'openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/drive',
			'id_token': id_token(client, nonce)}
		if first:
			refresh = '1//rig-' + secrets.token_urlsafe(24)
			D.refresh[refresh] = client
			out['refresh_token'] = refresh
		return out

	def oauth(self, method, path):
		form = dict(urllib.parse.parse_qsl(self.body().decode()))
		if path == '/revoke':
			D.access.pop(form.get('token'), None)
			D.refresh.pop(form.get('token'), None)
			return self.reply(200, {})
		if path != '/token' or method != 'POST':
			return self.reply(404, {'error': 'not found'})
		grant = form.get('grant_type')
		if grant == 'authorization_code':
			entry = D.codes.pop(form.get('code', ''), None)
			verifier = form.get('code_verifier', '')
			if not entry or b64u(hashlib.sha256(verifier.encode()).digest()) != entry['challenge'] \
					or entry['redirect'] != form.get('redirect_uri') or entry['client'] != form.get('client_id'):
				return self.reply(400, {'error': 'invalid_grant'})
			return self.reply(200, self.tokens(form['client_id'], nonce=entry['nonce'], first=True))
		if grant == 'refresh_token':
			client = D.refresh.get(form.get('refresh_token', ''))
			if not client or client != form.get('client_id'):
				return self.reply(400, {'error': 'invalid_grant'})
			return self.reply(200, self.tokens(client))
		return self.reply(400, {'error': 'unsupported_grant_type'})

	def file_or_404(self, fid):
		f = D.files.get(D.resolve(fid))
		if not f:
			raise LookupError(fid)
		return f

	def drive(self, method, path, query):
		try:
			return self.drive_routes(method, path, query)
		except LookupError as missing:
			return self.reply(*google_error(404, 'notFound', f'File not found: {missing}.'))

	def apply_write(self, f, body, query):
		if 'name' in body:
			f['name'] = body['name']
		if 'title' in body:
			f['name'] = body['title']
		if 'mimeType' in body and body['mimeType']:
			f['mimeType'] = body['mimeType']
		if 'trashed' in body:
			f['trashed'] = bool(body['trashed'])
		if isinstance(body.get('labels'), dict) and 'trashed' in body['labels']:
			f['trashed'] = bool(body['labels']['trashed'])
		if isinstance(body.get('appProperties'), dict):
			f['appProperties'].update({k: v for k, v in body['appProperties'].items() if v is not None})
		if isinstance(body.get('properties'), dict):
			f['properties'].update({k: v for k, v in body['properties'].items() if v is not None})
		if isinstance(body.get('properties'), list):
			for p in body['properties']:
				(f['appProperties'] if p.get('visibility', 'PRIVATE') == 'PRIVATE' else f['properties'])[p['key']] = p.get('value')
		for p in [x for x in query.get('removeParents', '').split(',') if x]:
			if D.resolve(p) in f['parents']:
				f['parents'].remove(D.resolve(p))
		for p in [x for x in query.get('addParents', '').split(',') if x]:
			if D.resolve(p) not in f['parents']:
				f['parents'].append(D.resolve(p))

	def create(self, body, content=None):
		fid = body.get('id') or D.new_id()
		parents = [D.resolve(p) for p in (body.get('parents') or [ROOT])]
		mime = body.get('mimeType') or ('application/octet-stream' if content is not None else 'application/octet-stream')
		f = {'id': fid, 'name': body.get('name') or 'Untitled', 'mimeType': mime, 'parents': parents, 'trashed': False,
			'version': 0, 'created': time.time(), 'modified': time.time(),
			'content': None if mime == FOLDER else (content if content is not None else b''),
			'appProperties': dict(body.get('appProperties') or {}), 'properties': dict(body.get('properties') or {})}
		D.files[fid] = f
		D.touch(f, content_changed=True)
		return f

	def drive_routes(self, method, path, query):
		parts = [urllib.parse.unquote(p) for p in path.strip('/').split('/')]
		if parts[:2] == ['drive', 'v3'] and parts[2:] == ['about']:
			used = sum(len(f['content'] or b'') for f in D.files.values())
			return self.reply(200, {'user': {'emailAddress': EMAIL, 'displayName': 'Rig Person', 'me': True},
				'storageQuota': {'limit': str(15 * 2**30), 'usage': str(used)}})
		if parts[:3] == ['drive', 'v3', 'changes']:
			if parts[3:] == ['startPageToken']:
				return self.reply(200, {'kind': 'drive#startPageToken', 'startPageToken': str(len(D.changes) + 1)})
			start = int(query.get('pageToken', '1'))
			size = int(query.get('pageSize', '100'))
			ids = D.changes[start - 1:start - 1 + size]
			out = {'kind': 'drive#changeList', 'changes': [{'kind': 'drive#change', 'changeType': 'file', 'fileId': i,
				'removed': i not in D.files, 'time': stamp(), **({'file': D.v3(D.files[i])} if i in D.files else {})} for i in ids]}
			nxt = start + len(ids)
			if nxt <= len(D.changes):
				out['nextPageToken'] = str(nxt)
			else:
				out['newStartPageToken'] = str(nxt)
			return self.reply(200, out)
		if parts[:3] == ['drive', 'v3', 'files']:
			rest = parts[3:]
			if rest == ['generateIds']:
				count = int(query.get('count', '10'))
				return self.reply(200, {'kind': 'drive#generatedIds', 'space': 'drive', 'ids': [D.new_id() for _ in range(count)]})
			if not rest:
				if method == 'GET':
					found = sorted((f for f in D.files.values() if f['id'] != ROOT and matches(f, query.get('q'))), key=lambda f: f['name'])
					size = int(query.get('pageSize', '100'))
					start = int(query.get('pageToken', '0') or 0)
					out = {'kind': 'drive#fileList', 'incompleteSearch': False, 'files': [D.v3(f) for f in found[start:start + size]]}
					if start + size < len(found):
						out['nextPageToken'] = str(start + size)
					return self.reply(200, out)
				if method == 'POST':
					body = json.loads(self.body() or b'{}')
					return self.reply(200, D.v3(self.create(body)))
			if len(rest) == 1:
				f = self.file_or_404(rest[0])
				if method == 'GET':
					if query.get('alt') == 'media':
						if f['content'] is None:
							return self.reply(*google_error(403, 'fileNotDownloadable', 'Only files with binary content can be downloaded.'))
						data = f['content']
						rng = self.headers.get('Range')
						if rng and rng.startswith('bytes='):
							a, _, b = rng[6:].partition('-')
							a = int(a)
							b = int(b) if b else len(data) - 1
							part = data[a:b + 1]
							return self.reply(206, raw=part, ctype='application/octet-stream',
								headers={'Content-Range': f'bytes {a}-{a + len(part) - 1}/{len(data)}'})
						return self.reply(200, raw=data, ctype='application/octet-stream')
					return self.reply(200, D.v3(f))
				if method == 'PATCH':
					body = json.loads(self.body() or b'{}')
					self.apply_write(f, body, query)
					D.touch(f)
					return self.reply(200, D.v3(f))
		if parts[:3] == ['drive', 'v2', 'files'] and len(parts) == 4:
			f = self.file_or_404(parts[3])
			if method == 'GET':
				return self.reply(200, D.v2(f), headers={'ETag': D.etag(f)})
			if method == 'PATCH':
				if self.headers.get('If-Match') != D.etag(f):
					return self.reply(*google_error(412, 'conditionNotMet', 'Precondition Failed'))
				self.apply_write(f, json.loads(self.body() or b'{}'), query)
				D.touch(f)
				return self.reply(200, D.v2(f), headers={'ETag': D.etag(f)})
		if parts[:1] == ['upload']:
			return self.upload(method, parts, query)
		return self.reply(*google_error(404, 'notFound', 'Unknown Drive path ' + path))

	def upload(self, method, parts, query):
		version = parts[2] if len(parts) > 2 else ''
		target = parts[4] if len(parts) > 4 else None
		if 'upload_id' in query:
			session = D.uploads.get(query['upload_id'])
			if not session:
				return self.reply(*google_error(404, 'notFound', 'Upload session not found'))
			data = self.body()
			rng = self.headers.get('Content-Range', '')
			total = session['total']
			if rng.startswith('bytes */'):
				pass
			elif rng.startswith('bytes '):
				span, _, tot = rng[6:].partition('/')
				a, _, b = span.partition('-')
				if int(a) != len(session['data']) or int(b) - int(a) + 1 != len(data):
					return self.reply(400, {'error': 'bad range'})
				session['data'] += data
				if tot != '*':
					total = session['total'] = int(tot)
			if total is not None and len(session['data']) >= total:
				return self.finish_upload(query['upload_id'], session)
			headers = {'Range': f"bytes=0-{len(session['data']) - 1}"} if session['data'] else {}
			return self.reply(308, headers=headers)
		body = json.loads(self.body() or b'{}')
		name = body.get('name') or body.get('title') or (D.files.get(target) or {}).get('name')
		if name in D.fail_upload:
			D.fail_upload.discard(name)
			return self.reply(*google_error(403, 'storageQuotaExceeded', "The user's Drive storage quota has been exceeded."))
		if target:
			f = self.file_or_404(target)
			if method == 'PUT' and self.headers.get('If-Match') != D.etag(f):
				return self.reply(*google_error(412, 'conditionNotMet', 'Precondition Failed'))
		total = self.headers.get('X-Upload-Content-Length')
		upload_id = secrets.token_urlsafe(16)
		D.uploads[upload_id] = {'version': version, 'target': target, 'meta': body, 'query': query,
			'data': b'', 'total': int(total) if total is not None else None}
		location = f"https://www.googleapis.com/upload/drive/{version}/files" + (f'/{target}' if target else '') \
			+ '?' + urllib.parse.urlencode({'uploadType': 'resumable', 'upload_id': upload_id})
		return self.reply(200, headers={'Location': location})

	def finish_upload(self, upload_id, session):
		D.uploads.pop(upload_id, None)
		if session['target']:
			f = self.file_or_404(session['target'])
			f['content'] = session['data']
			self.apply_write(f, session['meta'], session['query'])
			D.touch(f, content_changed=True)
		else:
			f = self.create(session['meta'], session['data'])
		return self.reply(200, D.v2(f) if session['version'] == 'v2' else D.v3(f))


class Admin(http.server.BaseHTTPRequestHandler):
	protocol_version = 'HTTP/1.1'

	def log_message(self, *args):
		pass

	def reply(self, body):
		data = json.dumps(body, indent=1, default=str).encode()
		self.send_response(200)
		self.send_header('Content-Type', 'application/json')
		self.send_header('Content-Length', str(len(data)))
		self.end_headers()
		self.wfile.write(data)

	def do_GET(self):
		with LOCK:
			if self.path == '/log':
				return self.reply(D.log)
			if self.path == '/issued':
				return self.reply(D.issued)
			if self.path == '/tree':
				return self.reply({f['id']: {'name': f['name'], 'parents': f['parents'], 'trashed': f['trashed'],
					'version': f['version'], 'size': None if f['content'] is None else len(f['content']),
					'md5': None if f['content'] is None else hashlib.md5(f['content']).hexdigest()} for f in D.files.values()})
			return self.reply({'error': 'unknown'})

	def do_POST(self):
		n = int(self.headers.get('Content-Length') or 0)
		body = json.loads(self.rfile.read(n) or b'{}')
		with LOCK:
			if self.path == '/ttl':
				D.ttl = int(body['seconds'])
				return self.reply({'ttl': D.ttl})
			if self.path == '/fail-upload':
				D.fail_upload.add(body['name'])
				return self.reply({'fail_upload': sorted(D.fail_upload)})
			if self.path == '/expire-access':
				for token in D.access:
					D.access[token] = 0
				return self.reply({'expired': len(D.access)})
			if self.path == '/put':
				parent = D.resolve(body.get('parent', 'root'))
				existing = [f for f in D.files.values() if parent in f['parents'] and f['name'] == body['name'] and not f['trashed']]
				content = body['content'].encode()
				if existing:
					f = existing[0]
					f['content'] = content
					D.touch(f, content_changed=True)
				else:
					f = Handler.create(None, {'name': body['name'], 'parents': [parent],
						'mimeType': body.get('mimeType', 'text/plain')}, content)
				return self.reply(D.v3(f))
			if self.path == '/mkdir':
				f = Handler.create(None, {'name': body['name'], 'parents': [D.resolve(body.get('parent', 'root'))], 'mimeType': FOLDER})
				return self.reply(D.v3(f))
			return self.reply({'error': 'unknown'})


def serve_tls():
	server = http.server.ThreadingHTTPServer(('127.0.0.1', TLS_PORT), Handler)
	context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	context.load_cert_chain(CERT, KEY)
	context.set_alpn_protocols(['http/1.1'])
	server.socket = context.wrap_socket(server.socket, server_side=True)
	server.serve_forever()


threading.Thread(target=serve_tls, daemon=True).start()
print(f'fakegoogle: TLS on 127.0.0.1:{TLS_PORT}, admin on 127.0.0.1:{ADMIN_PORT}', flush=True)
http.server.ThreadingHTTPServer(('127.0.0.1', ADMIN_PORT), Admin).serve_forever()
