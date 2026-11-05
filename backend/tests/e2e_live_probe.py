import sys
import struct
import uuid
import httpx

def main():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    # 1. Register test patient
    email = f"voice_e2e_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "SecurePassword123!"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": "Voice Test Patient",
        "phone_number": "+919876543210",
        "role": "patient",
        "preferred_language": "en"
    })
    assert reg.status_code == 201, f"Register failed: {reg.text}"
    tokens = reg.json()
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[E2E-LIVE] 1. Registered and logged in patient:", email)

    # 2. Accept screening consent
    consent = client.post("/api/v1/screening/consent/accept", json={
        "version": "1.0.0"
    }, headers=headers)
    assert consent.status_code in [200, 201], f"Consent failed: {consent.text}"
    print("[E2E-LIVE] 2. Consent accepted")

    # 3. Create screening session
    session = client.post("/api/v1/screening/sessions", json={}, headers=headers)
    assert session.status_code == 201, f"Session failed: {session.text}"
    s_id = session.json()["id"]
    print("[E2E-LIVE] 3. Session created:", s_id)

    # 4. Calibration
    calib = client.post(f"/api/v1/screening/sessions/{s_id}/calibration", json={
        "calibration_card_width_px": 324.0,
        "viewing_distance_cm": 100.0,
        "screen_diagonal_inches": 15.6,
        "screen_resolution_w": 1920,
        "screen_resolution_h": 1080
    }, headers=headers)
    assert calib.status_code in [200, 201], f"Calibration failed: {calib.text}"
    print("[E2E-LIVE] 4. Screen calibrated at viewing distance 100cm")

    # 5. Start Adaptive Acuity
    test_init = client.post(f"/api/v1/screening/sessions/{s_id}/acuity/start", json={
        "tested_eye": "RIGHT_EYE",
        "optotype_type": "TUMBLING_E",
        "viewing_distance_cm": 100.0,
        "screen_calibrated": True
    }, headers=headers)
    assert test_init.status_code in [200, 201], f"Start adaptive failed: {test_init.text}"
    chall_data = test_init.json()
    test_id = chall_data["test_id"]
    print(f"[E2E-LIVE] 5. Adaptive acuity test started: test_id={test_id}")
    print(f"[E2E-LIVE] 6. Challenge received: symbol={chall_data['presented_symbol']}, size_px={chall_data['target_height_px']}, attempt={chall_data['attempt_sequence']}")

    # 7. Submit voice step with real WAV byte stream
    sample_rate = 16000
    num_samples = sample_rate // 2  # 0.5s of silence/tone
    wav_bytes = bytearray()
    wav_bytes.extend(b"RIFF")
    wav_bytes.extend(struct.pack("<I", 36 + num_samples * 2))
    wav_bytes.extend(b"WAVEfmt ")
    wav_bytes.extend(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    wav_bytes.extend(b"data")
    wav_bytes.extend(struct.pack("<I", num_samples * 2))
    wav_bytes.extend(b"\x00" * (num_samples * 2))

    step_resp = client.post(
        f"/api/v1/screening/acuity/tests/{test_id}/voice-response",
        data={
            "attempt_sequence": chall_data["attempt_sequence"],
            "response_duration_ms": 500,
        },
        files={"file": ("speech.wav", bytes(wav_bytes), "audio/wav")},
        headers=headers
    )
    assert step_resp.status_code in [200, 201], f"Voice step failed: {step_resp.text}"
    step_data = step_resp.json()
    print(f"[E2E-LIVE] 7. Voice step processed:")
    print(f"   Audio received & analyzed, raw_transcript='{step_data['raw_transcript']}'")
    print(f"   Interpretation: recognized='{step_data['recognized_symbol']}', was_correct={step_data['was_correct']}, status={step_data['test_status']}")

    # 8. Complete test
    complete = client.post(f"/api/v1/screening/acuity/tests/{test_id}/complete", headers=headers)
    assert complete.status_code == 200, f"Complete failed: {complete.text}"
    res_data = complete.json()
    print("[E2E-LIVE] 8. Test completed successfully!")
    print(f"   Snellen: {res_data['final_snellen']}, LogMAR: {res_data['final_logmar']}, Decimal: {res_data['final_decimal']}")
    print(f"   Calibration Status: {res_data['calibration_status']}")
    print(f"   Disclaimer: {res_data['clinical_disclaimer']}")

    # 9. Complete the overall screening session
    sess_comp = client.post(f"/api/v1/screening/sessions/{s_id}/complete", headers=headers)
    assert sess_comp.status_code == 200, f"Session complete failed: {sess_comp.text}"
    print(f"[E2E-LIVE] 9. Screening session completed: status={sess_comp.json()['status']}")
    print("\n>>> ALL LIVE END-TO-END SCREENING & VOICE ADAPTIVE VERIFICATIONS PASSED! <<<")

if __name__ == "__main__":
    main()
