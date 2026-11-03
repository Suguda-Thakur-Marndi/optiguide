/**
 * Speech synthesis service for voice-guided questions
 * PRD Reference: FR-04 Voice-assisted questionnaire
 */

export const speakText = (text: string, lang: 'en' | 'hi' | 'or' = 'en'): Promise<void> => {
  return new Promise((resolve) => {
    if (!('speechSynthesis' in window)) {
      resolve();
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95; // Slightly slower for clarity
    utterance.pitch = 1.0;

    if (lang === 'hi') {
      utterance.lang = 'hi-IN';
    } else if (lang === 'or') {
      utterance.lang = 'hi-IN'; // Fallback to Indian accent if Odia TTS voice is unavailable
    } else {
      utterance.lang = 'en-IN';
    }

    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();

    window.speechSynthesis.speak(utterance);
  });
};

export const stopSpeech = () => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

