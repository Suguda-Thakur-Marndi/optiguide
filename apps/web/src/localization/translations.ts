export type LanguageCode = 'en' | 'hi' | 'or';

export interface TranslationDictionary {
  appName: string;
  tagline: string;
  clinicalNotice: string;
  clinicalDisclaimerText: string;
  nav: {
    home: string;
    howItWorks: string;
    screening: string;
    forShops: string;
    about: string;
    login: string;
    logout: string;
    dashboard: string;
    startScreening: string;
  };
  hero: {
    headline: string;
    subheadline: string;
    startCta: string;
    howCta: string;
    ruralNotice: string;
  };
  screening: {
    title: string;
    stepIntro: string;
    stepReadiness: string;
    stepQuestionnaire: string;
    stepDistance: string;
    stepNear: string;
    stepAstigmatism: string;
    stepColor: string;
    stepPD: string;
    stepResults: string;
    preliminaryNotice: string;
    replayAudio: string;
    next: string;
    previous: string;
    finish: string;
  };
  roles: {
    individual: string;
    shopkeeper: string;
    admin: string;
    optometrist: string;
    guest: string;
  };
}

export const translations: Record<LanguageCode, TranslationDictionary> = {
  en: {
    appName: 'OptiGuide',
    tagline: 'Accessible Vision Care for Everyone',
    clinicalNotice: 'Important Medical Notice',
    clinicalDisclaimerText:
      'OptiGuide provides preliminary vision screening and eyewear guidance only. It is not a diagnostic device and cannot confirm a medical diagnosis or prescribe corrective lenses. Please consult a registered optometrist or ophthalmologist for a comprehensive eye examination.',
    nav: {
      home: 'Home',
      howItWorks: 'How It Works',
      screening: 'Screening',
      forShops: 'For Shops',
      about: 'About',
      login: 'Sign In',
      logout: 'Sign Out',
      dashboard: 'Dashboard',
      startScreening: 'Start Screening',
    },
    hero: {
      headline: 'Accessible Vision Care for Everyone',
      subheadline:
        'A browser-based vision screening platform connecting rural and community clinics with optical shopkeepers and certified eye care professionals.',
      startCta: 'Start Vision Screening',
      howCta: 'Explore How It Works',
      ruralNotice: 'Optimized for community outreach, low bandwidth networks, and local Indian languages.',
    },
    screening: {
      title: 'Vision Screening Process',
      stepIntro: 'Introduction',
      stepReadiness: 'Readiness & Calibration',
      stepQuestionnaire: 'Symptom Questionnaire',
      stepDistance: 'Distance Vision Test',
      stepNear: 'Near Vision Test',
      stepAstigmatism: 'Astigmatism Screen',
      stepColor: 'Colour Vision Test',
      stepPD: 'Pupillary Distance (PD)',
      stepResults: 'Screening Results',
      preliminaryNotice: 'All observations are preliminary screening results.',
      replayAudio: 'Listen to Question',
      next: 'Next Step',
      previous: 'Previous',
      finish: 'Generate Screening Summary',
    },
    roles: {
      individual: 'Individual User',
      shopkeeper: 'Optical Shopkeeper',
      admin: 'Administrator',
      optometrist: 'Eye Care Professional',
      guest: 'Guest Screening',
    },
  },
  hi: {
    appName: 'ऑप्टीगाइड',
    tagline: 'सभी के लिए सुलभ दृष्टि देखभाल',
    clinicalNotice: 'महत्वपूर्ण चिकित्सा सूचना',
    clinicalDisclaimerText:
      'ऑप्टीगाइड केवल प्रारंभिक दृष्टि जांच और चश्मा मार्गदर्शन प्रदान करता है। यह कोई नैदानिक उपकरण नहीं है और चिकित्सा निदान की पुष्टि या सुधारात्मक लेंस नहीं लिख सकता है। कृपया पूर्ण जांच के लिए किसी योग्य नेत्र रोग विशेषज्ञ से मिलें।',
    nav: {
      home: 'होम',
      howItWorks: 'यह कैसे काम करता है',
      screening: 'दृष्टि जांच',
      forShops: 'दुकानदारों के लिए',
      about: 'हमारे बारे में',
      login: 'साइन इन करें',
      logout: 'साइन आउट',
      dashboard: 'डैशबोर्ड',
      startScreening: 'जांच शुरू करें',
    },
    hero: {
      headline: 'सभी के लिए सुलभ दृष्टि देखभाल',
      subheadline:
        'एक आधुनिक डिजिटल दृष्टि जांच प्रणाली जो ग्रामीण और सामुदायिक केंद्रों को चश्मा विक्रेताओं और नेत्र चिकित्सकों से जोड़ती है।',
      startCta: 'दृष्टि जांच शुरू करें',
      howCta: 'प्रक्रिया समझें',
      ruralNotice: 'धीमी इंटरनेट गति और स्थानीय भाषाओं के अनुकूल।',
    },
    screening: {
      title: 'दृष्टि जांच प्रक्रिया',
      stepIntro: 'परिचय',
      stepReadiness: 'उपकरण तैयारी',
      stepQuestionnaire: 'लक्षण प्रश्नावली',
      stepDistance: 'दूर दृष्टि परीक्षण',
      stepNear: 'निकट दृष्टि परीक्षण',
      stepAstigmatism: 'दृष्टिवैषम्य जांच',
      stepColor: 'वर्ण दृष्टि परीक्षण',
      stepPD: 'पुतली की दूरी (PD)',
      stepResults: 'जांच परिणाम',
      preliminaryNotice: 'सभी निष्कर्ष केवल प्रारंभिक जांच अवलोकन हैं।',
      replayAudio: 'प्रश्न दोबारा सुनें',
      next: 'आगे बढ़ें',
      previous: 'पीछे जाएं',
      finish: 'जांच सारांश देखें',
    },
    roles: {
      individual: 'व्यक्तिगत उपयोगकर्ता',
      shopkeeper: 'ऑप्टिकल दुकानदार',
      admin: 'प्रशासक',
      optometrist: 'नेत्र चिकित्सक',
      guest: 'अतिथि जांच',
    },
  },
  or: {
    appName: 'ଅପ୍ଟିଗାଇଡ୍',
    tagline: 'ସମସ୍ତଙ୍କ ପାଇଁ ସୁଲଭ ଦୃଷ୍ଟି ଯତ୍ନ',
    clinicalNotice: 'ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ଚିକିତ୍ସା ସୂଚନା',
    clinicalDisclaimerText:
      'ଅପ୍ଟିଗାଇଡ୍ କେବଳ ପ୍ରାଥମିକ ଦୃଷ୍ଟି ପରୀକ୍ଷା ଏବଂ ଚଷମା ପରାମର୍ଶ ପ୍ରଦାନ କରେ। ଏହା କୌଣସି ଡାକ୍ତରୀ ପ୍ରେସକ୍ରିପସନ୍ ନୁହେଁ। ପୂର୍ଣ୍ଣ ଚକ୍ଷୁ ପରୀକ୍ଷା ପାଇଁ କୌଣସି ଯୋଗ୍ୟ ଚକ୍ଷୁ ବିଶେଷଜ୍ଞଙ୍କ ସହ ପରାମର୍ଶ କରନ୍ତୁ।',
    nav: {
      home: 'ମୂଳପୃଷ୍ଠା',
      howItWorks: 'କିପରି କାମ କରେ',
      screening: 'ଦୃଷ୍ଟି ପରୀକ୍ଷା',
      forShops: 'ଦୋକାନୀଙ୍କ ପାଇଁ',
      about: 'ଆମ ବିଷୟରେ',
      login: 'ଲଗ୍ ଇନ୍',
      logout: 'ଲଗ୍ ଆଉଟ୍',
      dashboard: 'ଡ୍ୟାସବୋର୍ଡ',
      startScreening: 'ପରୀକ୍ଷା ଆରମ୍ଭ କରନ୍ତୁ',
    },
    hero: {
      headline: 'ସମସ୍ତଙ୍କ ପାଇଁ ସୁଲଭ ଦୃଷ୍ଟି ଯତ୍ନ',
      subheadline:
        'ଏକ ସହଜ ଡିଜିଟାଲ୍ ଚକ୍ଷୁ ପରୀକ୍ଷା ମାଧ୍ୟମ ଯାହା ଗ୍ରାମାଞ୍ଚଳ ଲୋକଙ୍କୁ ଚଷମା ଦୋକାନୀ ଏବଂ ଚକ୍ଷୁ ଡାକ୍ତରଙ୍କ ସହ ଯୋଡ଼ିଥାଏ।',
      startCta: 'ଦୃଷ୍ଟି ପରୀକ୍ଷା ଆରମ୍ଭ କରନ୍ତୁ',
      howCta: 'ପ୍ରଣାଳୀ ଦେଖନ୍ତୁ',
      ruralNotice: 'ସ୍ୱଳ୍ପ ଇଣ୍ଟରନେଟ୍ ଏବଂ ଓଡ଼ିଆ ଭାଷା ସହାୟତା ପାଇଁ ପ୍ରସ୍ତୁତ।',
    },
    screening: {
      title: 'ଦୃଷ୍ଟି ପରୀକ୍ଷା ପ୍ରକ୍ରିୟା',
      stepIntro: 'ପରିଚୟ',
      stepReadiness: 'ଉପକରଣ ପ୍ରସ୍ତୁତି',
      stepQuestionnaire: 'ଲକ୍ଷଣ ପ୍ରଶ୍ନାବଳୀ',
      stepDistance: 'ଦୂର ଦୃଷ୍ଟି ପରୀକ୍ଷା',
      stepNear: 'ନିକଟ ଦୃଷ୍ଟି ପରୀକ୍ଷା',
      stepAstigmatism: 'ଅସ୍ପଷ୍ଟତା ଯାଞ୍ଚ',
      stepColor: 'ରଙ୍ଗ ଦୃଷ୍ଟି ପରୀକ୍ଷା',
      stepPD: 'ଚକ୍ଷୁ ମଧ୍ୟବର୍ତ୍ତୀ ଦୂରତା (PD)',
      stepResults: 'ପରୀକ୍ଷା ଫଳାଫଳ',
      preliminaryNotice: 'ଏହା କେବଳ ପ୍ରାଥମିକ ପରୀକ୍ଷଣ ପର୍ଯ୍ୟବେକ୍ଷଣ।',
      replayAudio: 'ପ୍ରଶ୍ନ ପୁନର୍ବାର ଶୁଣନ୍ତୁ',
      next: 'ପରବର୍ତ୍ତୀ',
      previous: 'ପୂର୍ବବର୍ତ୍ତୀ',
      finish: 'ଫଳାଫଳ ପ୍ରସ୍ତୁତ କରନ୍ତୁ',
    },
    roles: {
      individual: 'ବ୍ୟକ୍ତିଗତ ବ୍ୟବହାରକାରୀ',
      shopkeeper: 'ଅପ୍ଟିକାଲ୍ ଦୋକାନୀ',
      admin: 'ପ୍ରଶାସକ',
      optometrist: 'ଚକ୍ଷୁ ଚିକିତ୍ସକ',
      guest: 'ଅତିଥି ପରୀକ୍ଷଣ',
    },
  },
};

