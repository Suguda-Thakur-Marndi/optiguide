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
