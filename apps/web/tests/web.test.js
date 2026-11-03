import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';

test('OptiGuide Core Tokens follow PRD Section 2 palette', () => {
  const tokenFile = fs.readFileSync(path.resolve('../../shared/tokens/index.ts'), 'utf-8');
  assert.ok(tokenFile.includes('#073F35'), 'Forest green token defined');
  assert.ok(tokenFile.includes('#092D28'), 'Deep green token defined');
  assert.ok(tokenFile.includes('#4F8278'), 'Muted teal token defined');
  assert.ok(tokenFile.includes('#F7F4EC'), 'Warm ivory token defined');
  assert.ok(tokenFile.includes('#E9E5DA'), 'Stone token defined');
  assert.ok(tokenFile.includes('#202823'), 'Charcoal token defined');
  assert.ok(tokenFile.includes('#28734F'), 'Success token defined');
  assert.ok(tokenFile.includes('#B77932'), 'Warning token defined');
  assert.ok(tokenFile.includes('#A9473E'), 'Error token defined');
});

test('Multilingual translations contain English, Hindi, and Odia dictionaries', () => {
  const transFile = fs.readFileSync(path.resolve('./src/localization/translations.ts'), 'utf-8');
  assert.ok(transFile.includes("appName: 'OptiGuide'"), 'English dictionary present');
  assert.ok(transFile.includes("appName: 'ऑप्टीगाइड'"), 'Hindi dictionary present');
  assert.ok(transFile.includes("appName: 'ଅପ୍ଟିଗାଇଡ୍'"), 'Odia dictionary present');
});

test('PRD Constraint 9: No em dash (—) character in website copy', () => {
  const transFile = fs.readFileSync(path.resolve('./src/localization/translations.ts'), 'utf-8');
  assert.strictEqual(transFile.includes('—'), false, 'English and localized copy must not contain em dash');
});

test('Product catalogue has frames with Indian Rupee pricing and face shapes', () => {
  const mockFile = fs.readFileSync(path.resolve('./src/services/mockData.ts'), 'utf-8');
  assert.ok(mockFile.includes('INITIAL_PRODUCTS'), 'Product list defined');
  assert.ok(mockFile.includes('priceINR: 1199'), 'Frame has price in INR');
  assert.ok(mockFile.includes('faceShapeCompatibility'), 'Frame defines face shape compatibility');
});

test('Customer records are initialized for optical shopkeeper kiosk', () => {
  const mockFile = fs.readFileSync(path.resolve('./src/services/mockData.ts'), 'utf-8');
  assert.ok(mockFile.includes('Ramesh Chandra Sahu'), 'Customer record present');
  assert.ok(mockFile.includes('+91 94371 88204'), 'Customer has contact number');
});

test('Interactive Demo Tumbling E levels are calibrated', () => {
  const demoFile = fs.readFileSync(path.resolve('./src/components/live-demo/InteractiveDemo.tsx'), 'utf-8');
  assert.ok(demoFile.includes("snellen: '20/100'"), 'Has 20/100 optotype level');
  assert.ok(demoFile.includes("snellen: '20/20'"), 'Has 20/20 optotype level');
  assert.ok(demoFile.includes('targetOrientation'), 'Supports orientation rotation');
});
test('API client provides full backend authentication, user profile, and screening methods', () => {
  const clientFile = fs.readFileSync(path.resolve('./src/services/apiClient.ts'), 'utf-8');
  assert.ok(clientFile.includes('checkBackendHealth'), 'Has checkBackendHealth');
  assert.ok(clientFile.includes('checkDatabaseHealth'), 'Has checkDatabaseHealth');
  assert.ok(clientFile.includes('register('), 'Has register method');
  assert.ok(clientFile.includes('login('), 'Has login method');
  assert.ok(clientFile.includes('refreshTokens('), 'Has refreshTokens method');
  assert.ok(clientFile.includes('logout('), 'Has logout method');
  assert.ok(clientFile.includes('logoutAll('), 'Has logoutAll method');
  assert.ok(clientFile.includes('getMe('), 'Has getMe method');
  assert.ok(clientFile.includes('updateProfile('), 'Has updateProfile method');
  assert.ok(clientFile.includes('getUserSessions('), 'Has getUserSessions method');
  assert.ok(clientFile.includes('getClinicalReviewAccess('), 'Has getClinicalReviewAccess method');
  assert.ok(clientFile.includes('getScreeningConsent('), 'Has getScreeningConsent method');
  assert.ok(clientFile.includes('acceptScreeningConsent('), 'Has acceptScreeningConsent method');
  assert.ok(clientFile.includes('createScreeningSession('), 'Has createScreeningSession method');
  assert.ok(clientFile.includes('completeScreeningSession('), 'Has completeScreeningSession method');
  assert.ok(clientFile.includes('cancelScreeningSession('), 'Has cancelScreeningSession method');
  assert.ok(clientFile.includes('recordVisualAcuity('), 'Has recordVisualAcuity method');
  assert.ok(clientFile.includes('getVisualAcuity('), 'Has getVisualAcuity method');
  assert.ok(clientFile.includes('recordAstigmatism('), 'Has recordAstigmatism method');
  assert.ok(clientFile.includes('getAstigmatism('), 'Has getAstigmatism method');
  assert.ok(clientFile.includes('recordColorVision('), 'Has recordColorVision method');
  assert.ok(clientFile.includes('getColorVision('), 'Has getColorVision method');
  assert.ok(clientFile.includes('getSessionSummary('), 'Has getSessionSummary method');
});

test('AuthModal component integrates login, registration, and user session management', () => {
  const modalFile = fs.readFileSync(path.resolve('./src/components/layout/AuthModal.tsx'), 'utf-8');
  assert.ok(modalFile.includes('handleLogin'), 'Has handleLogin handler');
  assert.ok(modalFile.includes('handleRegister'), 'Has handleRegister handler');
  assert.ok(modalFile.includes('handleUpdateProfile'), 'Has handleUpdateProfile handler');
  assert.ok(modalFile.includes('handleLogout'), 'Has handleLogout handler');
  assert.ok(modalFile.includes('handleLogoutAll'), 'Has handleLogoutAll handler');
});

test('ScreeningFlowPage integrates backend screening consent, clinical assessments, and session completion', () => {
  const pageFile = fs.readFileSync(path.resolve('./src/pages/ScreeningFlowPage.tsx'), 'utf-8');
  assert.ok(pageFile.includes('apiClient.acceptScreeningConsent'), 'Calls acceptScreeningConsent');
  assert.ok(pageFile.includes('apiClient.createScreeningSession'), 'Calls createScreeningSession');
  assert.ok(pageFile.includes('apiClient.recordVisualAcuity'), 'Calls recordVisualAcuity');
  assert.ok(pageFile.includes('apiClient.recordAstigmatism'), 'Calls recordAstigmatism');
  assert.ok(pageFile.includes('apiClient.recordColorVision'), 'Calls recordColorVision');
  assert.ok(pageFile.includes('apiClient.completeScreeningSession'), 'Calls completeScreeningSession');
});
