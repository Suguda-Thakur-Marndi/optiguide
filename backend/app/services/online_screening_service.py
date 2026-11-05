"""Complete Online Vision Screening Service.

Implements the multi-test interactive screening workflow inspired by digital
vision screening protocols across 7 modular assessment engines:
  1. Visual Acuity (OD, OS, OU, Distance & Near)
  2. Astigmatism Radial Clock Dial Screening
  3. Contrast / Light Sensitivity Discrimination
  4. Near Vision Reading Acuity (Paragraph scales)
  5. Near Vision Duochrome (Red/Green longitudinal chromatic focus)
  6. Color Vision (Pseudoisochromatic plates)
  7. Central Vision / Amsler Distortion Questionnaire
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConsentRequiredException,
    EntityNotFoundException,
    ForbiddenException,
    InvalidSessionTransitionException,
    ValidationException,
)
from app.models.online_screening import (
    ScreeningCalibration,
    ScreeningFinalReport,
    ScreeningTestInstance,
    ScreeningTestResponse,
)
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.repositories.online_screening_repository import OnlineScreeningRepository
from app.repositories.screening_repository import ScreeningRepository
from app.schemas.online_screening import (
    CalibrationResponse,
    CalibrationSubmitRequest,
    FinalScreeningReportResponse,
    ScreeningHistoryItem,
    ScreeningHistoryResponse,
    ScreeningPlatformConfigResponse,
    TestCancelRequest,
    TestChallengeResponse,
    TestModuleDefinition,
    TestResponseSubmitRequest,
    TestResultResponse,
    TestStartRequest,
    TestStepResponse,
)

CLINICAL_DISCLAIMER_TEXT = (
    "OptiGuide online vision screening is a preliminary functional observation aid. "
    "It is NOT a medical diagnosis, clinical evaluation, or ophthalmic prescription. "
    "All observations are non-diagnostic and do not replace an in-person clinical eye "
    "examination by a licensed, certified eye care professional (optometrist or ophthalmologist)."
)

# -----------------------------------------------------------------------------
# Multilingual Content Dictionary (English, Hindi, Odia)
# -----------------------------------------------------------------------------

LOCALIZED_MODULE_METADATA: dict[str, dict[str, Any]] = {
    "VISUAL_ACUITY": {
        "title": {
            "en": "Visual Acuity Screening",
            "hi": "दृष्टि तीक्ष्णता जांच (Visual Acuity)",
            "or": "ଦୃଷ୍ଟି ତୀକ୍ଷ୍ଣତା ପରୀକ୍ଷା (Visual Acuity)",
        },
        "description": {
            "en": "Evaluates distance and near visual acuity using adaptive optotype progression.",
            "hi": "दूरी और निकट दृष्टि तीक्ष्णता का अनुकूली परीक्षण करता है।",
            "or": "ଦୂର ଏବଂ ନିକଟ ଦୃଷ୍ଟି ତୀକ୍ଷ୍ଣତାର ଅନୁକୂଳ ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 300.0,
        "supported_eyes": ["OD", "OS", "OU"],
        "instructions": {
            "en": [
                "Sit comfortably at the calibrated distance (3 meters / 10 feet).",
                "Cover one eye gently with the palm of your hand without pressing on the eyelid.",
                "Identify the direction of the opening or character shown on the screen.",
            ],
            "hi": [
                "मापी गई दूरी (3 मीटर) पर आराम से बैठें।",
                "एक आंख को बिना दबाए हथेली से ढकें।",
                "स्क्रीन पर प्रदर्शित चिन्ह की दिशा बताएं।",
            ],
            "or": [
                "ନିର୍ଦ୍ଦିଷ୍ଟ ଦୂରତା (୩ ମିଟର) ରେ ଆରାମରେ ବସନ୍ତୁ।",
                "ଗୋଟିଏ ଆଖିକୁ ବିନା ଚାପରେ ପାପୁଲିରେ ଘୋଡାନ୍ତୁ।",
                "ପରଦାରେ ଦେଖାଯାଉଥିବା ଚିହ୍ନର ଦିଗ କୁହନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 120,
        "protocol_version": "OPTIGUIDE_VA_V1",
    },
    "ASTIGMATISM": {
        "title": {
            "en": "Astigmatism Clock Dial Screening",
            "hi": "दृष्टि विषमता जांच (Astigmatism Clock Dial)",
            "or": "ଦୃଷ୍ଟି ବିଷମତା ପରୀକ୍ଷା (Astigmatism Clock Dial)",
        },
        "description": {
            "en": "Screens for meridian clarity variance using a standardized radial clock dial chart.",
            "hi": "घड़ी के डायल जैसे रेखापुंज से सभी दिशाओं में स्पष्टता की जांच करता है।",
            "or": "ଘଣ୍ଟା ଡାଏଲ୍ ଭଳି ରେଖା ମାଧ୍ୟମରେ ଦୃଷ୍ଟି ସ୍ପଷ୍ଟତାର ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 60.0,
        "supported_eyes": ["OD", "OS"],
        "instructions": {
            "en": [
                "Sit at 60 cm from your screen with both eyes or test one eye at a time.",
                "Look at the central fixation point of the radiating radial lines.",
                "Observe whether all spoke lines appear equally dark and sharp, or if some stand out.",
            ],
            "hi": [
                "स्क्रीन से 60 सेमी की दूरी पर बैठें।",
                "केंद्र बिंदु को देखें और बताएं कि क्या सभी रेखाएं एक समान गहरी दिखती हैं।",
            ],
            "or": [
                "ପରଦା ଠାରୁ ୬୦ ସେମି ଦୂରରେ ବସନ୍ତୁ।",
                "କେନ୍ଦ୍ର ବିନ୍ଦୁକୁ ଦେଖନ୍ତୁ ଏବଂ ସବୁ ରେଖା ସମାନ ଗାଢ଼ କି ନାହିଁ ଲକ୍ଷ୍ୟ କରନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 60,
        "protocol_version": "OPTIGUIDE_ASTIG_V1",
    },
    "CONTRAST_SENSITIVITY": {
        "title": {
            "en": "Contrast & Light Sensitivity",
            "hi": "कंट्रास्ट एवं प्रकाश संवेदनशीलता (Contrast Sensitivity)",
            "or": "କଣ୍ଟ୍ରାଷ୍ଟ ଏବଂ ଆଲୋକ ସମ୍ବେଦନଶୀଳତା (Contrast Sensitivity)",
        },
        "description": {
            "en": "Screens visual discrimination under diminishing contrast conditions.",
            "hi": "घटते कंट्रास्ट में आकृतियों को पहचानने की क्षमता की प्रारंभिक जांच करता है।",
            "or": "କମୁଥିବା କଣ୍ଟ୍ରାଷ୍ଟରେ ଆକୃତି ଚିହ୍ନିବାର କ୍ଷମତା ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 60.0,
        "supported_eyes": ["OD", "OS", "OU"],
        "instructions": {
            "en": [
                "Keep screen brightness at standard normal level without glare.",
                "Identify the faint letters or symbols displayed as contrast progressively decreases.",
            ],
            "hi": [
                "स्क्रीन की चमक सामान्य रखें।",
                "हल्के और कम कंट्रास्ट वाले अक्षरों को पहचानें।",
            ],
            "or": [
                "ପରଦାର ଉଜ୍ଜ୍ୱଳତା ସାଧାରଣ ରଖନ୍ତୁ।",
                "ଧୀରେ ଧୀରେ ହାଲୁକା ହେଉଥିବା ଅକ୍ଷରଗୁଡିକୁ ଚିହ୍ନଟ କରନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 60,
        "protocol_version": "OPTIGUIDE_CS_V1",
    },
    "NEAR_VISION_READING": {
        "title": {
            "en": "Near Vision Reading Acuity",
            "hi": "निकट दृष्टि पठन परीक्षण (Near Vision Reading)",
            "or": "ନିକଟ ଦୃଷ୍ଟି ପଠନ ପରୀକ୍ଷା (Near Vision Reading)",
        },
        "description": {
            "en": "Assesses comfort and clarity reading diminishing near paragraphs at 40 cm.",
            "hi": "40 सेमी की दूरी पर छोटे पाठ्य को पढ़ने की स्पष्टता की जांच करता है।",
            "or": "୪୦ ସେମି ଦୂରତାରେ ଛୋଟ ଅକ୍ଷର ପଢିବାର ସ୍ପଷ୍ଟତା ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 40.0,
        "supported_eyes": ["OU", "OD", "OS"],
        "instructions": {
            "en": [
                "Hold your screen at your normal reading distance (approximately 40 cm / 16 inches).",
                "Wear reading glasses if you routinely use them for reading.",
                "Identify the smallest paragraph you can comfortably read without squinting.",
            ],
            "hi": [
                "स्क्रीन को पढ़ने की सामान्य दूरी (40 सेमी) पर रखें।",
                "यदि आप पढ़ने के चश्मे का उपयोग करते हैं तो उन्हें पहनें।",
                "सबसे छोटे पैराग्राफ को चुनें जिसे आप बिना तनाव के पढ़ सकते हैं।",
            ],
            "or": [
                "ପରଦାକୁ ପଢିବା ଦୂରତା (୪୦ ସେମି) ରେ ରଖନ୍ତୁ।",
                "ପଢିବା ଚଷମା ବ୍ୟବହାର କରୁଥିଲେ ପିନ୍ଧନ୍ତୁ।",
                "ଆପଣ ସହଜରେ ପଢିପାରୁଥିବା ସବୁଠାରୁ ଛୋଟ ଅନୁଚ୍ଛେଦ ବାଛନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 60,
        "protocol_version": "OPTIGUIDE_NV_READING_V1",
    },
    "NEAR_VISION_DUOCHROME": {
        "title": {
            "en": "Near Vision Duochrome (Red/Green) Comparison",
            "hi": "डुओक्रोम लाल/हरा परीक्षण (Duochrome Test)",
            "or": "ଡୁଓକ୍ରୋମ ନାଲି/ସବୁଜ ପରୀକ୍ଷା (Duochrome Test)",
        },
        "description": {
            "en": "Explores chromatic balance by comparing letter sharpness on red versus green backgrounds.",
            "hi": "लाल और हरे पृष्ठभूमि पर अक्षरों की तीक्ष्णता की तुलना करता है।",
            "or": "ନାଲି ଏବଂ ସବୁଜ ପୃଷ୍ଠଭୂମିରେ ଅକ୍ଷରର ସ୍ପଷ୍ଟତା ତୁଳନା କରେ।",
        },
        "target_viewing_distance_cm": 40.0,
        "supported_eyes": ["OU", "OD", "OS"],
        "instructions": {
            "en": [
                "Hold screen at 40 cm.",
                "Compare the symbols on the red background and the green background.",
                "Indicate which background displays sharper, clearer letters.",
            ],
            "hi": [
                "स्क्रीन को 40 सेमी पर रखें।",
                "लाल और हरे रंग की पृष्ठभूमि पर लिखे अक्षरों की तुलना करें।",
            ],
            "or": [
                "ପରଦାକୁ ୪୦ ସେମି ରେ ରଖନ୍ତୁ।",
                "ନାଲି ଏବଂ ସବୁଜ ପୃଷ୍ଠଭୂମିର ଅକ୍ଷରଗୁଡିକୁ ତୁଳନା କରନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 45,
        "protocol_version": "OPTIGUIDE_DUOCHROME_V1",
    },
    "COLOR_VISION": {
        "title": {
            "en": "Color Vision Screening",
            "hi": "रंग दृष्टि परीक्षण (Color Vision Plates)",
            "or": "ରଙ୍ଗ ଦୃଷ୍ଟି ପରୀକ୍ଷା (Color Vision Plates)",
        },
        "description": {
            "en": "Screens for red-green and general chromatic discrimination using pseudoisochromatic plates.",
            "hi": "स्यूडोआइसोक्रोमैटिक प्लेट्स द्वारा रंग पहचानने की क्षमता की जांच करता है।",
            "or": "ସୁଡୋଆଇସୋକ୍ରୋମାଟିକ ପ୍ଲେଟ ଦ୍ୱାରା ରଙ୍ଗ ଚିହ୍ନିବା କ୍ଷମତା ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 60.0,
        "supported_eyes": ["OU"],
        "instructions": {
            "en": [
                "Ensure your display color profile is standard and disable night light or blue-light filters.",
                "Enter the numeral you distinguish within each colored dot matrix plate within 5 seconds.",
                "If no numeral is visible, choose 'No Number Visible'.",
            ],
            "hi": [
                "नाइट लाइट या ब्लू लाइट फिल्टर बंद करें।",
                "प्रत्येक प्लेट में दिखने वाली संख्या दर्ज करें या 'कोई संख्या नहीं' चुनें।",
            ],
            "or": [
                "ନାଇଟ୍ ଲାଇଟ୍ ବନ୍ଦ କରନ୍ତୁ।",
                "ପ୍ରତ୍ୟେକ ପ୍ଲେଟରେ ଥିବା ସଂଖ୍ୟା ଲେଖନ୍ତୁ କିମ୍ବା 'କୌଣସି ସଂଖ୍ୟା ଦିଶୁନାହିଁ' ବାଛନ୍ତୁ।",
            ],
        },
        "estimated_duration_seconds": 60,
        "protocol_version": "OPTIGUIDE_COLOR_V1",
    },
    "CENTRAL_VISION_AMSLER": {
        "title": {
            "en": "Central Vision & Macular Distortion Questionnaire",
            "hi": "केंद्रीय दृष्टि एवं विकृति प्रश्नावली (Amsler Grid)",
            "or": "କେନ୍ଦ୍ରୀୟ ଦୃଷ୍ଟି ବିକୃତି ପରୀକ୍ଷା (Amsler Grid)",
        },
        "description": {
            "en": "Screens for central visual distortion (metamorphopsia) or scotoma using an Amsler grid stimulus.",
            "hi": "केंद्रीय दृष्टि में रेखाओं के मुड़ने या काले धब्बों की प्रारंभिक जांच करता है।",
            "or": "କେନ୍ଦ୍ରୀୟ ଦୃଷ୍ଟିରେ ରେଖା ବଙ୍କା ହେବା କିମ୍ବା ଅନ୍ଧାର ଦାଗର ପରୀକ୍ଷା କରେ।",
        },
        "target_viewing_distance_cm": 30.0,
        "supported_eyes": ["OD", "OS"],
        "instructions": {
            "en": [
                "Hold screen at 30 cm wearing your reading glasses if you use them.",
                "Cover one eye gently. Stare directly at the white center dot on the grid.",
                "While keeping your focus strictly on the center dot, answer whether any lines appear wavy, missing, or distorted.",
            ],
            "hi": [
                "30 सेमी की दूरी पर रखें और एक आंख ढकें।",
                "केंद्र के सफेद बिंदु पर ध्यान केंद्रित रखें और बताएं कि क्या कोई रेखाएं मुड़ी या गायब दिखती हैं।",
            ],
            "or": [
                "୩୦ ସେମି ଦୂରତାରେ ରଖନ୍ତୁ ଏବଂ ଗୋଟିଏ ଆଖି ଘୋଡାନ୍ତୁ।",
                "କେନ୍ଦ୍ର ବିନ୍ଦୁକୁ ଦେଖି କୁହନ୍ତୁ କୌଣସି ରେଖା ବଙ୍କା କିମ୍ବା ଅଦୃଶ୍ୟ ଦିଶୁଛି କି।",
            ],
        },
        "estimated_duration_seconds": 60,
        "protocol_version": "OPTIGUIDE_AMSLER_V1",
    },
}

MODULE_SEQUENCE_ORDER = [
    "VISUAL_ACUITY",
    "ASTIGMATISM",
    "CONTRAST_SENSITIVITY",
    "NEAR_VISION_READING",
    "NEAR_VISION_DUOCHROME",
    "COLOR_VISION",
    "CENTRAL_VISION_AMSLER",
]


class OnlineScreeningService:
    """Core domain service for the 7-module online vision screening engine."""

    # -------------------------------------------------------------------------
    # Platform Configuration & Module Catalog
    # -------------------------------------------------------------------------

    @classmethod
    def get_platform_configuration(cls, lang: str = "en") -> ScreeningPlatformConfigResponse:
        """Returns the complete catalog of vision screening modules and platform settings."""
        lang_key = lang.lower() if lang.lower() in ["en", "hi", "or"] else "en"
        modules: list[TestModuleDefinition] = []

        for mod_key in MODULE_SEQUENCE_ORDER:
            meta = LOCALIZED_MODULE_METADATA[mod_key]
            modules.append(
                TestModuleDefinition(
                    test_type=mod_key,
                    title=meta["title"].get(lang_key, meta["title"]["en"]),
                    description=meta["description"].get(lang_key, meta["description"]["en"]),
                    target_viewing_distance_cm=meta["target_viewing_distance_cm"],
                    supported_eyes=meta["supported_eyes"],
                    instructions=meta["instructions"].get(lang_key, meta["instructions"]["en"]),
                    estimated_duration_seconds=meta["estimated_duration_seconds"],
                    protocol_version=meta["protocol_version"],
                    disclaimer=CLINICAL_DISCLAIMER_TEXT,
                )
            )

        return ScreeningPlatformConfigResponse(
            available_modules=modules,
            default_test_sequence=MODULE_SEQUENCE_ORDER,
            clinical_notice=CLINICAL_DISCLAIMER_TEXT,
        )

    @classmethod
    def get_module_definition(cls, test_type: str, lang: str = "en") -> TestModuleDefinition:
        """Returns detailed metadata and instructions for a single screening module."""
        type_upper = test_type.strip().upper()
        if type_upper not in LOCALIZED_MODULE_METADATA:
            raise EntityNotFoundException("ScreeningModule", test_type)

        lang_key = lang.lower() if lang.lower() in ["en", "hi", "or"] else "en"
        meta = LOCALIZED_MODULE_METADATA[type_upper]

        return TestModuleDefinition(
            test_type=type_upper,
            title=meta["title"].get(lang_key, meta["title"]["en"]),
            description=meta["description"].get(lang_key, meta["description"]["en"]),
            target_viewing_distance_cm=meta["target_viewing_distance_cm"],
            supported_eyes=meta["supported_eyes"],
            instructions=meta["instructions"].get(lang_key, meta["instructions"]["en"]),
            estimated_duration_seconds=meta["estimated_duration_seconds"],
            protocol_version=meta["protocol_version"],
            disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    @classmethod
    def start_session(cls, db: Session, user: User, session_id: uuid.UUID) -> ScreeningSession:
        """Confirms informed consent, verifies session state, and marks session as IN_PROGRESS."""
        session = db.get(ScreeningSession, session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", session_id)
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to session owner.")
        if session.status in ["completed", "cancelled", "COMPLETED", "CANCELLED"]:
            raise InvalidSessionTransitionException(
                f"Cannot restart session in terminal state '{session.status}'."
            )

        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        if not active_consent:
            raise ConsentRequiredException(
                "Active informed consent is required to start vision screening."
            )

        session.status = "in_progress"
        db.commit()
        db.refresh(session)
        return session

    # -------------------------------------------------------------------------
    # Calibration Subsystem
    # -------------------------------------------------------------------------

    @classmethod
    def record_calibration(
        cls,
        db: Session,
        user: User,
        session_id: uuid.UUID,
        payload: CalibrationSubmitRequest,
    ) -> CalibrationResponse:
        """Processes and saves display calibration and physical viewing distance parameters."""
        session = db.get(ScreeningSession, session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", session_id)
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to session owner.")

        # Compute PPI if reported_card_width_px is supplied (standard ISO/IEC 7810 ID-1 card = 85.6mm = 3.370 in)
        computed_ppi: float | None = None
        calib_status = "UNCALIBRATED"

        if payload.reported_card_width_px and payload.reported_card_width_px > 50.0:
            ppi_calc = payload.reported_card_width_px / 3.370
            if 60.0 <= ppi_calc <= 800.0:
                computed_ppi = round(ppi_calc, 2)
                calib_status = "SERVER_VERIFIED"
            else:
                calib_status = "CLIENT_REPORTED"

        existing = OnlineScreeningRepository.get_calibration_by_session(db, session_id)
        if existing:
            existing.device_category = payload.device_category
            existing.screen_width_px = payload.screen_width_px
            existing.screen_height_px = payload.screen_height_px
            existing.device_pixel_ratio = payload.device_pixel_ratio
            existing.calibration_method = payload.calibration_method
            existing.calibration_status = calib_status
            existing.computed_ppi = computed_ppi
            existing.target_viewing_distance_cm = payload.target_viewing_distance_cm
            existing.user_confirmed_distance = payload.user_confirmed_distance
            existing.calibration_notes = payload.calibration_notes
            calibration = OnlineScreeningRepository.create_or_update_calibration(db, existing)
        else:
            calibration = ScreeningCalibration(
                session_id=session_id,
                user_id=user.id,
                device_category=payload.device_category,
                screen_width_px=payload.screen_width_px,
                screen_height_px=payload.screen_height_px,
                device_pixel_ratio=payload.device_pixel_ratio,
                calibration_method=payload.calibration_method,
                calibration_status=calib_status,
                computed_ppi=computed_ppi,
                target_viewing_distance_cm=payload.target_viewing_distance_cm,
                user_confirmed_distance=payload.user_confirmed_distance,
                calibration_notes=payload.calibration_notes,
            )
            calibration = OnlineScreeningRepository.create_or_update_calibration(db, calibration)

        return CalibrationResponse.model_validate(calibration)

    @classmethod
    def get_calibration(cls, db: Session, user: User, session_id: uuid.UUID) -> CalibrationResponse:
        """Retrieves active calibration metadata for the session."""
        session = db.get(ScreeningSession, session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", session_id)
        if session.user_id != user.id and user.role not in [
            "admin",
            "optometrist",
            "ophthalmologist",
        ]:
            raise ForbiddenException("Access restricted to session owner.")

        calib = OnlineScreeningRepository.get_calibration_by_session(db, session_id)
        if not calib:
            raise EntityNotFoundException("ScreeningCalibration", session_id)
        return CalibrationResponse.model_validate(calib)

    # -------------------------------------------------------------------------
    # Interactive Test Execution Lifecycle
    # -------------------------------------------------------------------------

    @classmethod
    def start_test_instance(
        cls,
        db: Session,
        user: User,
        session_id: uuid.UUID,
        test_type: str,
        payload: TestStartRequest | None = None,
    ) -> TestChallengeResponse:
        """Initiates an interactive screening module instance and produces the initial stimulus challenge."""
        type_upper = test_type.strip().upper()
        if type_upper not in LOCALIZED_MODULE_METADATA:
            raise ValidationException(f"Unsupported screening test module: '{test_type}'.")

        session = db.get(ScreeningSession, session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", session_id)
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to session owner.")
        if session.status != "in_progress":
            raise InvalidSessionTransitionException(
                f"Cannot start tests in session with status '{session.status}'."
            )

        # Enforce informed consent requirement
        active_consent = ScreeningRepository.get_active_consent(db, user.id)
        if not active_consent:
            raise ConsentRequiredException(
                "Active informed consent is required before initiating tests."
            )

        eye = payload.eye.upper() if payload and payload.eye else "OU"
        if eye in ["RIGHT", "OD"]:
            eye = "OD"
        elif eye in ["LEFT", "OS"]:
            eye = "OS"
        elif eye in ["BOTH", "OU"]:
            eye = "OU"

        viewing_cond = payload.viewing_condition if payload else "WITH_GLASSES"

        # Determine total steps per module
        step_counts = {
            "VISUAL_ACUITY": 5,
            "ASTIGMATISM": 1,
            "CONTRAST_SENSITIVITY": 3,
            "NEAR_VISION_READING": 3,
            "NEAR_VISION_DUOCHROME": 1,
            "COLOR_VISION": 6,
            "CENTRAL_VISION_AMSLER": 3,
        }
        total_steps = step_counts.get(type_upper, 1)

        instance = ScreeningTestInstance(
            session_id=session_id,
            user_id=user.id,
            test_type=type_upper,
            status="IN_PROGRESS",
            eye=eye,
            viewing_condition=viewing_cond,
            current_step=0,
            total_steps=total_steps,
            protocol_version=LOCALIZED_MODULE_METADATA[type_upper]["protocol_version"],
            started_at=datetime.now(UTC),
        )
        instance = OnlineScreeningRepository.create_test_instance(db, instance)

        return cls._generate_challenge_for_step(instance, step_index=0)

    @classmethod
    def get_current_challenge(
        cls, db: Session, user: User, test_id: uuid.UUID
    ) -> TestChallengeResponse:
        """Retrieves the active challenge for an in-progress test instance."""
        instance = OnlineScreeningRepository.get_test_instance_by_id(db, test_id)
        if not instance:
            raise EntityNotFoundException("ScreeningTestInstance", test_id)
        if instance.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to test instance owner.")
        if instance.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Test instance is not active (current status: '{instance.status}')."
            )

        return cls._generate_challenge_for_step(instance, step_index=instance.current_step)

    @classmethod
    def submit_test_response(
        cls,
        db: Session,
        user: User,
        test_id: uuid.UUID,
        payload: TestResponseSubmitRequest,
    ) -> TestStepResponse:
        """Evaluates a stimulus response strictly server-side and progresses the test module."""
        instance = OnlineScreeningRepository.get_test_instance_by_id(db, test_id)
        if not instance:
            raise EntityNotFoundException("ScreeningTestInstance", test_id)
        if instance.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to test instance owner.")
        if instance.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Cannot submit response to test with status '{instance.status}'."
            )
        if payload.step_index != instance.current_step:
            raise ValidationException(
                f"Out of sequence submission: expected step {instance.current_step}, received {payload.step_index}."
            )

        # Retrieve challenge definition and expected answer strictly server-side
        challenge = cls._generate_challenge_for_step(instance, step_index=instance.current_step)
        expected_ans = cls.get_expected_answer(instance, step_index=instance.current_step)

        is_correct: bool | None = None
        if expected_ans and expected_ans not in ["ANY_VALID_OBSERVATION", "ANY_CHOICE"]:
            is_correct = payload.user_response.strip().upper() == str(expected_ans).strip().upper()
        elif expected_ans:
            is_correct = True

        # Persist response record
        response_rec = ScreeningTestResponse(
            test_instance_id=instance.id,
            step_index=instance.current_step,
            stimulus_id=payload.stimulus_id,
            stimulus_version=challenge.stimulus_content.get("version", "1.0"),
            expected_answer=str(expected_ans),
            user_response=payload.user_response.strip(),
            is_correct=is_correct,
            response_time_ms=payload.response_time_ms,
            details=json.dumps({"eye": instance.eye, "condition": instance.viewing_condition}),
        )
        OnlineScreeningRepository.create_test_response(db, response_rec)

        # Advance step
        instance.current_step += 1
        is_completed = instance.current_step >= instance.total_steps

        if is_completed:
            instance.status = "COMPLETED"
            instance.completed_at = datetime.now(UTC)
            cls._evaluate_final_test_outcome(db, instance)
            db.commit()
            db.refresh(instance)

            metrics = json.loads(instance.result_details) if instance.result_details else {}
            return TestStepResponse(
                test_id=instance.id,
                test_type=instance.test_type,
                status=instance.status,
                step_index=instance.current_step,
                total_steps=instance.total_steps,
                is_completed=True,
                next_challenge=None,
                result_summary={
                    "classification": instance.result_classification,
                    "observation": instance.clinical_observation,
                    "metrics": metrics,
                },
            )
        else:
            db.commit()
            db.refresh(instance)
            next_ch = cls._generate_challenge_for_step(instance, step_index=instance.current_step)
            return TestStepResponse(
                test_id=instance.id,
                test_type=instance.test_type,
                status=instance.status,
                step_index=instance.current_step,
                total_steps=instance.total_steps,
                is_completed=False,
                next_challenge=next_ch,
                result_summary=None,
            )

    @classmethod
    def complete_test_instance(
        cls, db: Session, user: User, test_id: uuid.UUID
    ) -> TestResultResponse:
        """Manually completes an active test instance and computes preliminary evaluation."""
        instance = OnlineScreeningRepository.get_test_instance_by_id(db, test_id)
        if not instance:
            raise EntityNotFoundException("ScreeningTestInstance", test_id)
        if instance.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to test instance owner.")
        if instance.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Test instance is not active (current status: '{instance.status}')."
            )

        instance.status = "COMPLETED"
        instance.completed_at = datetime.now(UTC)
        cls._evaluate_final_test_outcome(db, instance)
        db.commit()
        db.refresh(instance)

        metrics = json.loads(instance.result_details) if instance.result_details else {}
        return TestResultResponse(
            test_id=instance.id,
            session_id=instance.session_id,
            test_type=instance.test_type,
            status=instance.status,
            eye=instance.eye,
            viewing_condition=instance.viewing_condition,
            result_classification=instance.result_classification or "INCOMPLETE",
            clinical_observation=instance.clinical_observation or "Test finalized by user.",
            metrics=metrics,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

    @classmethod
    def cancel_test_instance(
        cls,
        db: Session,
        user: User,
        test_id: uuid.UUID,
        payload: TestCancelRequest | None = None,
    ) -> TestResultResponse:
        """Cancels an active test instance."""
        instance = OnlineScreeningRepository.get_test_instance_by_id(db, test_id)
        if not instance:
            raise EntityNotFoundException("ScreeningTestInstance", test_id)
        if instance.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to test instance owner.")
        if instance.status != "IN_PROGRESS":
            raise InvalidSessionTransitionException(
                f"Cannot cancel test with status '{instance.status}'."
            )

        instance.status = "CANCELLED"
        instance.cancelled_at = datetime.now(UTC)
        instance.cancellation_reason = payload.reason if payload else "Cancelled by user"
        instance.result_classification = "INCOMPLETE"
        instance.clinical_observation = "Screening test cancelled before completion."
        db.commit()
        db.refresh(instance)

        metrics = json.loads(instance.result_details) if instance.result_details else {}
        return TestResultResponse(
            test_id=instance.id,
            session_id=instance.session_id,
            test_type=instance.test_type,
            status=instance.status,
            eye=instance.eye,
            viewing_condition=instance.viewing_condition,
            result_classification="INCOMPLETE",
            clinical_observation=instance.clinical_observation,
            metrics=metrics,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

    @classmethod
    def get_test_result(cls, db: Session, user: User, test_id: uuid.UUID) -> TestResultResponse:
        """Retrieves evaluated clinical results for a completed test instance."""
        instance = OnlineScreeningRepository.get_test_instance_by_id(db, test_id)
        if not instance:
            raise EntityNotFoundException("ScreeningTestInstance", test_id)
        if instance.user_id != user.id and user.role not in [
            "admin",
            "optometrist",
            "ophthalmologist",
        ]:
            raise ForbiddenException("Access restricted to test instance owner.")

        metrics = json.loads(instance.result_details) if instance.result_details else {}
        return TestResultResponse(
            test_id=instance.id,
            session_id=instance.session_id,
            test_type=instance.test_type,
            status=instance.status,
            eye=instance.eye,
            viewing_condition=instance.viewing_condition,
            result_classification=instance.result_classification or "INCOMPLETE",
            clinical_observation=instance.clinical_observation or "Observation pending.",
            metrics=metrics,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )

    # -------------------------------------------------------------------------
    # Final Screening Report Engine
    # -------------------------------------------------------------------------

    @classmethod
    def generate_final_report(
        cls, db: Session, user: User, session_id: uuid.UUID
    ) -> FinalScreeningReportResponse:
        """Compiles an aggregate screening report across all 7 modules for the session."""
        session = db.get(ScreeningSession, session_id)
        if not session:
            raise EntityNotFoundException("ScreeningSession", session_id)
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Access restricted to session owner.")

        existing_report = OnlineScreeningRepository.get_final_report_by_session(db, session_id)
        if existing_report:
            return cls._build_report_response(existing_report)

        # Retrieve all test instances and calibration for session
        instances = OnlineScreeningRepository.get_test_instances_for_session(db, session_id)
        calib = OnlineScreeningRepository.get_calibration_by_session(db, session_id)

        completed_count = sum(1 for inst in instances if inst.status == "COMPLETED")
        skipped_count = len(MODULE_SEQUENCE_ORDER) - completed_count
        skipped_count = max(skipped_count, 0)

        # Assess aggregate findings
        has_follow_up = any(
            inst.result_classification == "OBSERVATION_REQUIRES_FOLLOW_UP" for inst in instances
        )
        is_uncalibrated = not calib or calib.calibration_status == "UNCALIBRATED"

        if has_follow_up:
            overall_class = "OBSERVATION_REQUIRES_FOLLOW_UP"
            referral_needed = True
            recommendation = (
                "One or more screening observations indicate visual variance. "
                "Consultation with a licensed optometrist or ophthalmologist is recommended for in-person evaluation."
            )
        elif completed_count >= 3:
            overall_class = "UNCALIBRATED" if is_uncalibrated else "NO_CONCERN_REPORTED"
            referral_needed = False
            recommendation = (
                "Screening responses showed no notable visual concerns under the tested conditions. "
                "Maintain regular routine annual eye check-ups with your eye care professional."
            )
        else:
            overall_class = "INCOMPLETE"
            referral_needed = False
            recommendation = "Screening session was incomplete. We recommend completing all modules for a full observation."

        limitations = [
            "Screening conducted on uncalibrated consumer display hardware."
            if is_uncalibrated
            else "Calibrated via client reference.",
            "Ambient illumination and precise optical pupil alignment were self-managed.",
            "Non-diagnostic functional screening only; refractive powers cannot be determined from this report.",
        ]

        # Structure individual module results dictionary
        results_dict: dict[str, Any] = {}
        for inst in instances:
            metrics = json.loads(inst.result_details) if inst.result_details else {}
            results_dict[inst.test_type.lower()] = {
                "test_id": str(inst.id),
                "status": inst.status,
                "eye": inst.eye,
                "classification": inst.result_classification or "INCOMPLETE",
                "observation": inst.clinical_observation,
                "metrics": metrics,
            }

        calib_dict = {
            "status": calib.calibration_status if calib else "UNCALIBRATED",
            "device": calib.device_category if calib else "DESKTOP",
            "distance_cm": calib.target_viewing_distance_cm if calib else 40.0,
            "ppi": calib.computed_ppi if calib else None,
        }

        # Generate unique report reference
        report_num = (
            f"OPT-REP-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        )

        report = ScreeningFinalReport(
            session_id=session.id,
            user_id=user.id,
            report_number=report_num,
            overall_classification=overall_class,
            protocol_version="OPTIGUIDE_V1",
            completed_tests_count=completed_count,
            skipped_tests_count=skipped_count,
            summary_content=json.dumps(results_dict),
            follow_up_recommendation=recommendation,
            professional_referral_indicated=referral_needed,
            limitations_disclaimer=json.dumps(limitations),
        )
        report = OnlineScreeningRepository.create_final_report(db, report)

        # Transition session to completed if still in progress
        if session.status == "in_progress":
            session.status = "completed"
            session.completed_at = datetime.now(UTC)
            db.commit()

        return cls._build_report_response(report, calib_dict=calib_dict)

    @classmethod
    def get_report_by_id(
        cls, db: Session, user: User, report_id: uuid.UUID
    ) -> FinalScreeningReportResponse:
        """Retrieves an existing final screening report by report UUID."""
        report = OnlineScreeningRepository.get_final_report_by_id(db, report_id)
        if not report:
            raise EntityNotFoundException("ScreeningFinalReport", report_id)
        if report.user_id != user.id and user.role not in [
            "admin",
            "optometrist",
            "ophthalmologist",
        ]:
            raise ForbiddenException("Access restricted to report owner or authorized clinician.")
        return cls._build_report_response(report)

    @classmethod
    def get_report_for_session(
        cls, db: Session, user: User, session_id: uuid.UUID
    ) -> FinalScreeningReportResponse:
        """Retrieves or generates the final screening report for a screening session."""
        report = OnlineScreeningRepository.get_final_report_by_session(db, session_id)
        if report:
            if report.user_id != user.id and user.role not in [
                "admin",
                "optometrist",
                "ophthalmologist",
            ]:
                raise ForbiddenException(
                    "Access restricted to session owner or authorized clinician."
                )
            return cls._build_report_response(report)
        return cls.generate_final_report(db, user, session_id)

    @classmethod
    def list_user_history(
        cls, db: Session, user: User, limit: int = 20, offset: int = 0
    ) -> ScreeningHistoryResponse:
        """Lists historical screening sessions and completed reports for the user."""
        sessions, total = ScreeningRepository.list_sessions_for_user(
            db, user_id=user.id, limit=limit, offset=offset
        )
        items: list[ScreeningHistoryItem] = []

        for s in sessions:
            rep = OnlineScreeningRepository.get_final_report_by_session(db, s.id)
            instances = OnlineScreeningRepository.get_test_instances_for_session(db, s.id)
            comp_modules = [inst.test_type for inst in instances if inst.status == "COMPLETED"]

            items.append(
                ScreeningHistoryItem(
                    session_id=s.id,
                    status=s.status,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    report_id=rep.id if rep else None,
                    report_number=rep.report_number if rep else None,
                    overall_classification=rep.overall_classification if rep else None,
                    completed_modules=comp_modules,
                )
            )

        return ScreeningHistoryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    # -------------------------------------------------------------------------
    # Internal Challenge & Scoring Evaluators
    # -------------------------------------------------------------------------

    @classmethod
    def _get_step_spec(cls, instance: ScreeningTestInstance, step_index: int) -> dict[str, Any]:
        """Internal helper returning full step specifications and server-side expected answers."""
        test_type = instance.test_type

        if test_type == "VISUAL_ACUITY":
            levels = [
                {"snellen": "20/200", "logmar": 1.0, "size_mm": 43.6},
                {"snellen": "20/100", "logmar": 0.7, "size_mm": 21.8},
                {"snellen": "20/50", "logmar": 0.4, "size_mm": 10.9},
                {"snellen": "20/30", "logmar": 0.18, "size_mm": 6.5},
                {"snellen": "20/20", "logmar": 0.0, "size_mm": 4.4},
            ]
            idx = min(step_index, len(levels) - 1)
            lvl = levels[idx]
            orientations = ["UP", "RIGHT", "DOWN", "LEFT"]
            seed_bytes = hashlib.sha256(f"{instance.id}:{step_index}".encode()).digest()
            chosen_orient = orientations[seed_bytes[0] % len(orientations)]

            return {
                "stimulus_id": f"VA_STEP_{step_index}_{lvl['snellen'].replace('/', '_')}",
                "stimulus_type": "TUMBLING_E",
                "stimulus_content": {
                    "optotype": "E",
                    "orientation": chosen_orient,
                    "target_snellen": lvl["snellen"],
                    "nominal_size_mm": lvl["size_mm"],
                    "viewing_distance_m": 3.0,
                },
                "options": ["UP", "RIGHT", "DOWN", "LEFT"],
                "prompt_question": "Which direction is the opening of the letter 'E' pointing?",
                "target_viewing_distance_cm": 300.0,
                "instructions": "Stand or sit at 3 meters. Keep non-tested eye covered.",
                "expected_answer": chosen_orient,
            }

        elif test_type == "ASTIGMATISM":
            return {
                "stimulus_id": "ASTIG_CLOCK_DIAL_12",
                "stimulus_type": "RADIAL_CLOCK_DIAL",
                "stimulus_content": {
                    "spoke_count": 12,
                    "dial_hours": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                },
                "options": [
                    "ALL_LINES_UNIFORM",
                    "SOME_LINES_DARKER",
                    "SOME_LINES_SHARPER",
                    "CANNOT_DETERMINE",
                ],
                "prompt_question": "While looking at the center, do all spoke lines appear equally sharp and dark?",
                "target_viewing_distance_cm": 60.0,
                "instructions": "Sit at 60 cm. Observe radial spokes without squinting.",
                "expected_answer": "ALL_LINES_UNIFORM",
            }

        elif test_type == "CONTRAST_SENSITIVITY":
            contrast_levels = [
                {"contrast_pct": 50, "triplet": "D S N"},
                {"contrast_pct": 10, "triplet": "C K R"},
                {"contrast_pct": 2.5, "triplet": "Z H V"},
            ]
            idx = min(step_index, len(contrast_levels) - 1)
            item = contrast_levels[idx]
            return {
                "stimulus_id": f"CS_STEP_{step_index}_{item['contrast_pct']}PCT",
                "stimulus_type": "LOW_CONTRAST_TRIPLET",
                "stimulus_content": {
                    "contrast_percentage": item["contrast_pct"],
                    "characters": item["triplet"],
                },
                "options": [item["triplet"], "CANNOT_READ", "NO_LETTERS_SEEN"],
                "prompt_question": "What 3 letters do you distinguish on the faint grey card?",
                "target_viewing_distance_cm": 60.0,
                "instructions": "Observe without leaning forward or changing screen angle.",
                "expected_answer": item["triplet"],
            }

        elif test_type == "NEAR_VISION_READING":
            paragraphs = [
                {
                    "size_label": "N12",
                    "text": "Good vision supports daily reading, learning, and clear work.",
                },
                {
                    "size_label": "N8",
                    "text": "Proper lighting helps reduce eye strain and fatigue during prolonged tasks.",
                },
                {
                    "size_label": "N5",
                    "text": "OptiGuide recommends annual vision screenings with a registered eye doctor.",
                },
            ]
            idx = min(step_index, len(paragraphs) - 1)
            p = paragraphs[idx]
            return {
                "stimulus_id": f"NV_READ_{step_index}_{p['size_label']}",
                "stimulus_type": "READING_PASSAGE",
                "stimulus_content": {
                    "size_label": p["size_label"],
                    "passage": p["text"],
                },
                "options": ["CAN_READ_EASILY", "CAN_READ_WITH_EFFORT", "CANNOT_READ"],
                "prompt_question": f"Can you clearly and comfortably read the {p['size_label']} paragraph at 40 cm?",
                "target_viewing_distance_cm": 40.0,
                "instructions": "Hold screen at 40 cm in even light. Wear reading glasses if used.",
                "expected_answer": "CAN_READ_EASILY",
            }

        elif test_type == "NEAR_VISION_DUOCHROME":
            return {
                "stimulus_id": "DUOCHROME_RED_GREEN_1",
                "stimulus_type": "DUOCHROME_SPLIT",
                "stimulus_content": {
                    "left_bg": "#D32F2F",
                    "right_bg": "#388E3C",
                    "symbols": "O H T C",
                },
                "options": [
                    "RED_BACKGROUND_CLEARER",
                    "GREEN_BACKGROUND_CLEARER",
                    "BOTH_EQUALLY_CLEAR",
                    "CANNOT_DETERMINE",
                ],
                "prompt_question": "Do the black letters appear darker or sharper on the Red or Green background?",
                "target_viewing_distance_cm": 40.0,
                "instructions": "Hold screen at 40 cm. Compare letter clarity on both background halves.",
                "expected_answer": "BOTH_EQUALLY_CLEAR",
            }

        elif test_type == "COLOR_VISION":
            plates = [
                {"plate_num": 1, "expected": "12", "type": "DEMONSTRATION"},
                {"plate_num": 2, "expected": "8", "type": "TRANSFORMATION"},
                {"plate_num": 3, "expected": "29", "type": "RED_GREEN"},
                {"plate_num": 4, "expected": "5", "type": "RED_GREEN"},
                {"plate_num": 5, "expected": "74", "type": "RED_GREEN"},
                {"plate_num": 6, "expected": "NO_NUMBER", "type": "VANISHING"},
            ]
            idx = min(step_index, len(plates) - 1)
            pl = plates[idx]
            return {
                "stimulus_id": f"ISHIHARA_PLATE_{pl['plate_num']}",
                "stimulus_type": "PSEUDOISOCHROMATIC_PLATE",
                "stimulus_content": {
                    "plate_number": pl["plate_num"],
                    "plate_type": pl["type"],
                    "asset_reference": f"assets/plates/plate_{pl['plate_num']}.png",
                },
                "options": [pl["expected"], "3", "7", "70", "NO_NUMBER"],
                "prompt_question": "What number do you see in the circle of colored dots?",
                "target_viewing_distance_cm": 60.0,
                "instructions": "View in natural daylight. Respond within 5 seconds without squinting.",
                "expected_answer": pl["expected"],
            }

        elif test_type == "CENTRAL_VISION_AMSLER":
            questions = [
                {
                    "prompt": "While looking directly at the center white dot, can you see all 4 corners and borders of the grid?",
                    "options": ["YES_ALL_CORNERS_VISIBLE", "NO_CORNERS_MISSING"],
                    "expected": "YES_ALL_CORNERS_VISIBLE",
                },
                {
                    "prompt": "While staring at the center dot, do any of the straight lines appear wavy, bent, or distorted?",
                    "options": ["NO_ALL_LINES_STRAIGHT", "YES_WAVY_OR_DISTORTED"],
                    "expected": "NO_ALL_LINES_STRAIGHT",
                },
                {
                    "prompt": "Are any areas of the grid blurred, dark, discolored, or missing (holes)?",
                    "options": ["NO_UNIFORM_GRID", "YES_DARK_OR_MISSING_AREAS"],
                    "expected": "NO_UNIFORM_GRID",
                },
            ]
            idx = min(step_index, len(questions) - 1)
            q = questions[idx]
            return {
                "stimulus_id": f"AMSLER_QUESTION_{step_index + 1}",
                "stimulus_type": "AMSLER_GRID_FIXATION",
                "stimulus_content": {
                    "grid_type": "WHITE_GRID_BLACK_BACKGROUND",
                    "central_fixation": True,
                },
                "options": q["options"],
                "prompt_question": q["prompt"],
                "target_viewing_distance_cm": 30.0,
                "instructions": "Cover non-tested eye. Look straight at the center dot.",
                "expected_answer": q["expected"],
            }

        # Fallback default
        return {
            "stimulus_id": f"GENERIC_STEP_{step_index}",
            "stimulus_type": "GENERIC",
            "stimulus_content": {"status": "ACTIVE"},
            "options": ["CONFIRMED"],
            "prompt_question": "Please confirm this screening step.",
            "target_viewing_distance_cm": 40.0,
            "instructions": "Follow on-screen prompt.",
            "expected_answer": "CONFIRMED",
        }

    @classmethod
    def get_expected_answer(cls, instance: ScreeningTestInstance, step_index: int) -> str:
        """Evaluates or retrieves expected answer strictly server-side."""
        spec = cls._get_step_spec(instance, step_index)
        return str(spec.get("expected_answer", ""))

    @classmethod
    def _generate_challenge_for_step(
        cls, instance: ScreeningTestInstance, step_index: int
    ) -> TestChallengeResponse:
        """Generates the stimulus challenge for a given module and step without exposing the expected answer."""
        spec = cls._get_step_spec(instance, step_index)
        return TestChallengeResponse(
            test_id=instance.id,
            test_type=instance.test_type,
            eye=instance.eye,
            viewing_condition=instance.viewing_condition,
            step_index=step_index,
            total_steps=instance.total_steps,
            stimulus_id=spec["stimulus_id"],
            stimulus_type=spec["stimulus_type"],
            stimulus_content=spec["stimulus_content"],
            options=spec["options"],
            prompt_question=spec["prompt_question"],
            target_viewing_distance_cm=spec["target_viewing_distance_cm"],
            instructions=spec["instructions"],
        )

    @classmethod
    def _evaluate_final_test_outcome(cls, db: Session, instance: ScreeningTestInstance) -> None:
        """Computes module-specific metrics and clinical observations upon test completion."""
        responses = OnlineScreeningRepository.get_responses_for_test(db, instance.id)
        test_type = instance.test_type

        if test_type == "VISUAL_ACUITY":
            passed_levels = [r.step_index for r in responses if r.is_correct]
            snellen_map = {0: "20/200", 1: "20/100", 2: "20/50", 3: "20/30", 4: "20/20"}
            logmar_map = {0: 1.0, 1: 0.7, 2: 0.4, 3: 0.18, 4: 0.0}

            highest_passed = max(passed_levels) if passed_levels else 0
            final_snellen = snellen_map.get(highest_passed, "20/200")
            final_logmar = logmar_map.get(highest_passed, 1.0)

            needs_followup = final_logmar >= 0.4  # Worse than 20/40
            classification = (
                "OBSERVATION_REQUIRES_FOLLOW_UP" if needs_followup else "NO_CONCERN_REPORTED"
            )
            observation = f"Preliminary distance visual acuity recorded at {final_snellen} (LogMAR {final_logmar:.2f}) in {instance.eye} eye."
            details = {
                "final_snellen": final_snellen,
                "final_logmar": final_logmar,
                "correct_count": len(passed_levels),
                "total_steps": len(responses),
            }

        elif test_type == "ASTIGMATISM":
            resp_val = responses[0].user_response.upper() if responses else "NO_DIFFERENCE"
            if "DARKER" in resp_val or "SHARPER" in resp_val:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Meridian clarity variance reported on clock dial spokes. Suggests potential astigmatic refractive variance."
            elif resp_val == "CANNOT_DETERMINE":
                classification = "INCONCLUSIVE"
                observation = "Clock dial meridian discrimination was inconclusive."
            else:
                classification = "NO_CONCERN_REPORTED"
                observation = "Uniform radial line clarity observed across all 12 meridians."
            details = {"user_choice": resp_val}

        elif test_type == "CONTRAST_SENSITIVITY":
            passed = sum(1 for r in responses if r.is_correct)
            if passed >= 2:
                classification = "NO_CONCERN_REPORTED"
                observation = (
                    "Normal contrast sensitivity discrimination across screening triplets."
                )
            else:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Difficulty resolving low-contrast stimuli. Clinical contrast sensitivity assessment suggested."
            details = {"passed_steps": passed, "total_steps": len(responses)}

        elif test_type == "NEAR_VISION_READING":
            can_read_n5 = any(
                r.step_index == 2 and r.user_response == "CAN_READ_EASILY" for r in responses
            )
            can_read_n8 = any(
                r.step_index == 1 and r.user_response in ["CAN_READ_EASILY", "CAN_READ_WITH_EFFORT"]
                for r in responses
            )

            if can_read_n5 or can_read_n8:
                classification = "NO_CONCERN_REPORTED"
                observation = "Comfortable near-reading clarity demonstrated at 40 cm."
            else:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Difficulty reading small near text at standard 40cm distance. Suggests presbyopia assessment."
            details = {"steps_completed": len(responses)}

        elif test_type == "NEAR_VISION_DUOCHROME":
            choice = responses[0].user_response.upper() if responses else "BOTH_EQUALLY_CLEAR"
            if "RED" in choice:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Red background letters reported sharper; exploratory finding suggests myopic focus bias."
            elif "GREEN" in choice:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Green background letters reported sharper; exploratory finding suggests hyperopic focus bias."
            else:
                classification = "NO_CONCERN_REPORTED"
                observation = "Balanced chromatic focus reported between red and green backgrounds."
            details = {"duochrome_choice": choice}

        elif test_type == "COLOR_VISION":
            correct_count = sum(1 for r in responses if r.is_correct)
            if correct_count >= 5:
                classification = "NO_CONCERN_REPORTED"
                observation = f"Standard chromatic discrimination: {correct_count}/{len(responses)} plates identified correctly."
            else:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = f"Color discrimination variance indicated: {correct_count}/{len(responses)} plates correct. Suggests formal Ishihara screening."
            details = {"correct_plates": correct_count, "total_plates": len(responses)}

        elif test_type == "CENTRAL_VISION_AMSLER":
            has_wavy = any("WAVY" in r.user_response.upper() for r in responses)
            has_missing = any("MISSING" in r.user_response.upper() for r in responses)

            if has_wavy or has_missing:
                classification = "OBSERVATION_REQUIRES_FOLLOW_UP"
                observation = "Metamorphopsia or scotoma (wavy lines or missing grid areas) reported. URGENT professional macular evaluation recommended."
            else:
                classification = "NO_CONCERN_REPORTED"
                observation = "Normal central grid perception without reported line distortion or blind spots."
            details = {"distortion_reported": has_wavy or has_missing}

        else:
            classification = "NO_CONCERN_REPORTED"
            observation = "Module completed."
            details = {}

        instance.result_classification = classification
        instance.clinical_observation = observation
        instance.result_details = json.dumps(details)

    @classmethod
    def _build_report_response(
        cls, report: ScreeningFinalReport, calib_dict: dict[str, Any] | None = None
    ) -> FinalScreeningReportResponse:
        """Helper to format database report entity into FinalScreeningReportResponse."""
        results = json.loads(report.summary_content) if report.summary_content else {}
        limitations = (
            json.loads(report.limitations_disclaimer) if report.limitations_disclaimer else []
        )

        return FinalScreeningReportResponse(
            report_id=report.id,
            report_number=report.report_number,
            session_id=report.session_id,
            status="COMPLETED",
            created_at=report.created_at,
            overall_classification=report.overall_classification,
            protocol_version=report.protocol_version,
            completed_tests_count=report.completed_tests_count,
            skipped_tests_count=report.skipped_tests_count,
            calibration=calib_dict or {"status": "UNCALIBRATED"},
            results=results,
            follow_up_recommendation=report.follow_up_recommendation,
            professional_referral_indicated=report.professional_referral_indicated,
            limitations=limitations,
            clinical_disclaimer=CLINICAL_DISCLAIMER_TEXT,
        )
