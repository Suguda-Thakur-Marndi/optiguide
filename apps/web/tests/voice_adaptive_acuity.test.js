import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';

test('VoiceRecorder service provides 16kHz PCM WAV encoding & mic lifecycle controls', () => {
  const recorderFile = fs.readFileSync(path.resolve('./src/services/voiceRecorder.ts'), 'utf-8');
  assert.ok(recorderFile.includes('class VoiceRecorderService'), 'VoiceRecorderService defined');
  assert.ok(recorderFile.includes('encodeWav'), 'Has encodeWav method');
  assert.ok(recorderFile.includes("'RIFF'"), 'Writes standard RIFF header');
  assert.ok(recorderFile.includes("'WAVE'"), 'Writes WAVE header');
  assert.ok(recorderFile.includes('16000'), 'Standard 16,000 Hz sample rate');
  assert.ok(recorderFile.includes('getTracks().forEach'), 'Cleans up microphone media tracks');
  assert.ok(recorderFile.includes('autoStopTimeout'), 'Enforces auto-timeout safeguards');
});

test('API Client exposes complete interactive adaptive acuity & voice methods', () => {
  const clientFile = fs.readFileSync(path.resolve('./src/services/apiClient.ts'), 'utf-8');
  assert.ok(clientFile.includes('startAdaptiveAcuityTest('), 'Has startAdaptiveAcuityTest');
  assert.ok(clientFile.includes('getAdaptiveAcuityChallenge('), 'Has getAdaptiveAcuityChallenge');
  assert.ok(clientFile.includes('submitAdaptiveAcuityResponse('), 'Has submitAdaptiveAcuityResponse');
  assert.ok(clientFile.includes('submitAdaptiveAcuityVoiceResponse('), 'Has submitAdaptiveAcuityVoiceResponse');
  assert.ok(clientFile.includes('submitAdaptiveAcuityVoiceBlob('), 'Has submitAdaptiveAcuityVoiceBlob');
  assert.ok(clientFile.includes('completeAdaptiveAcuityTest('), 'Has completeAdaptiveAcuityTest');
  assert.ok(clientFile.includes('cancelAdaptiveAcuityTest('), 'Has cancelAdaptiveAcuityTest');
  assert.ok(clientFile.includes('getAdaptiveAcuityResult('), 'Has getAdaptiveAcuityResult');
  assert.ok(clientFile.includes('ensureAuthenticatedPatient('), 'Has ensureAuthenticatedPatient helper');
});

test('ScreeningFlowPage implements all 8 required screens of the vision testing workflow', () => {
  const flowFile = fs.readFileSync(path.resolve('./src/pages/ScreeningFlowPage.tsx'), 'utf-8');

  // Screen A: Welcome
  assert.ok(flowFile.includes("stage === 'welcome'"), 'Has Welcome Screen A');
  assert.ok(flowFile.includes('Start Vision Test'), 'Has Start Vision Test CTA');
  assert.ok(flowFile.includes('Audio Voice Instructions'), 'Has voice instructions option');

  // Screen B: Preparation
  assert.ok(flowFile.includes("stage === 'preparation'"), 'Has Preparation Screen B');
  assert.ok(flowFile.includes('Viewing Distance & Posture'), 'Has distance posture checklist');
  assert.ok(flowFile.includes('Eye Occlusion (Cover One Eye)'), 'Has occlusion checklist');
  assert.ok(flowFile.includes('handleTestMicrophone'), 'Has microphone check trigger');

  // Screen C: Screen Calibration
  assert.ok(flowFile.includes("stage === 'calibration'"), 'Has Calibration Screen C');
  assert.ok(flowFile.includes('STANDARD REFERENCE CARD'), 'Provides standard reference card slider');
  assert.ok(flowFile.includes('85.6'), 'Calibrated to 85.6 mm card standard');
  assert.ok(flowFile.includes('handleConfirmCalibration'), 'Handles physical calibration confirmation');

  // Screen D: Eye Selection
  assert.ok(flowFile.includes("stage === 'eye_selection'"), 'Has Eye Selection Screen D');
  assert.ok(flowFile.includes('Right Eye (OD)'), 'Supports Right Eye testing');
  assert.ok(flowFile.includes('Left Eye (OS)'), 'Supports Left Eye testing');
  assert.ok(flowFile.includes('Both Eyes (OU)'), 'Supports Binocular testing');
  assert.ok(flowFile.includes('TUMBLING_E'), 'Supports Tumbling E optotypes');
  assert.ok(flowFile.includes('LANDOLT_C'), 'Supports Landolt C optotypes');
  assert.ok(flowFile.includes('SLOAN'), 'Supports Sloan letters');

  // Screen E & F: Interactive Test & Voice Interaction
  assert.ok(flowFile.includes("stage === 'testing'"), 'Has Interactive Testing Screen E/F');
  assert.ok(flowFile.includes('renderOptotypeStimulus'), 'Renders server-directed optotype stimulus');
  assert.ok(flowFile.includes('triggerVoiceListening'), 'Triggers real microphone speech capture');
  assert.ok(flowFile.includes('submitRecordedAudio'), 'Uploads recorded audio to backend');

  // Screen G: Adaptive Feedback & Speech Ambiguity Handling
  assert.ok(flowFile.includes('lastSpeechFeedback'), 'Renders adaptive feedback banner');
  assert.ok(flowFile.includes('retryRequired'), 'Handles speech retry without attempt penalty');
  assert.ok(flowFile.includes('handleManualResponse'), 'Provides manual response fallback buttons');

  // Screen H: Final Results
  assert.ok(flowFile.includes("stage === 'results'"), 'Has Final Results Screen H');
  assert.ok(flowFile.includes('finalResult.final_snellen'), 'Renders final Snellen score');
  assert.ok(flowFile.includes('finalResult.final_logmar'), 'Renders final LogMAR score');
  assert.ok(flowFile.includes('finalResult.calibration_status'), 'Renders calibration status');
});

test('ScreeningFlowPage strictly enforces non-prescriptive medical safety boundaries', () => {
  const flowFile = fs.readFileSync(path.resolve('./src/pages/ScreeningFlowPage.tsx'), 'utf-8');
  assert.ok(flowFile.includes('IMPORTANT STATUTORY MEDICAL NOTICE'), 'Displays statutory medical disclaimer');
  assert.ok(flowFile.includes('not a certified medical diagnosis'), 'Explicit non-prescriptive boundary');
  assert.ok(flowFile.includes('consult a licensed optometrist'), 'Mandatory referral to eye care professional');
  assert.strictEqual(flowFile.includes('SPH:'), false, 'Never fabricates SPH lens power');
  assert.strictEqual(flowFile.includes('CYL:'), false, 'Never fabricates CYL lens power');
  assert.strictEqual(flowFile.includes('AXIS:'), false, 'Never fabricates AXIS lens angle');
});
