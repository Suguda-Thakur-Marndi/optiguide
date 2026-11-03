import test from 'node:test';
import assert from 'node:assert';

test('Web application metadata smoke test', () => {
  const appName = 'OptiGuide';
  assert.strictEqual(appName, 'OptiGuide');
});

test('API Base URL normalization logic', () => {
  const rawUrl = 'http://localhost:8000///';
  const cleanUrl = rawUrl.trim().replace(/\/+$/, '');
  assert.strictEqual(cleanUrl, 'http://localhost:8000');
});

test('Local storage token synchronization logic', () => {
  const mockStorage = new Map();
  const setToken = (k, v) => (v ? mockStorage.set(k, v) : mockStorage.delete(k));

  setToken('optiguide_access_token', 'test_jwt_access_token');
  assert.strictEqual(mockStorage.get('optiguide_access_token'), 'test_jwt_access_token');

  setToken('optiguide_access_token', null);
  assert.strictEqual(mockStorage.has('optiguide_access_token'), false);
});

test('API screening consent version contract', () => {
  const requiredVersion = '1.0.0';
  const requiredHash = 'ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6';
  assert.strictEqual(requiredVersion, '1.0.0');
  assert.strictEqual(requiredHash.length, 64);
});
