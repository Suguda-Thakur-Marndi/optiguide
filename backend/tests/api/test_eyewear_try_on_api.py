"""
Comprehensive Integration Tests for Virtual Eyewear Try-On API (/api/v1/eyewear).
Validates catalogue auto-seeding, AR asset telemetry, geometric attributes,
session lifecycle, frame/color switching, customer favourites, and snapshot tracking.
"""

import uuid
from fastapi import status
from starlette.testclient import TestClient

from app.core.security import create_access_token


def test_list_eyewear_frames_seeds_and_returns_catalogue(client: TestClient):
    """Verifies that GET /api/v1/eyewear/frames seeds and returns standard try-on models."""
    res = client.get("/api/v1/eyewear/frames")
    assert res.status_code == status.HTTP_200_OK

    frames = res.json()
    assert isinstance(frames, list)
    assert len(frames) >= 8

    first = frames[0]
    # Check essential geometric and try-on telemetry fields
    assert "frame_id" in first
    assert "sku" in first
    assert "name" in first
    assert "brand_name" in first
    assert "frame_shape" in first
    assert "frame_material" in first
    assert "base_price_inr" in first
    assert "try_on_asset_url" in first
    assert "available_colors" in first
    assert len(first["available_colors"]) >= 1
    assert "left_lens_center_x" in first
    assert "right_lens_center_x" in first
    assert "bridge_center_x" in first
    assert "asset_scale" in first
    assert "is_try_on_available" in first
    assert first["is_try_on_available"] is True


def test_filter_frames_by_shape_and_search(client: TestClient):
    """Verifies shape filtering, brand/name search, and categories listing."""
    # List categories
    cat_res = client.get("/api/v1/eyewear/frames/categories")
    assert cat_res.status_code == status.HTTP_200_OK
    categories = cat_res.json()
    assert isinstance(categories, list)

    # Filter by shape = round
    res_round = client.get("/api/v1/eyewear/frames?shape=round")
    assert res_round.status_code == status.HTTP_200_OK
    round_frames = res_round.json()
    assert len(round_frames) >= 1
    for f in round_frames:
        assert f["frame_shape"].lower() == "round"

    # Filter by shape = rectangular
    res_rec = client.get("/api/v1/eyewear/frames?shape=rectangular")
    assert res_rec.status_code == status.HTTP_200_OK
    rec_frames = res_rec.json()
    assert len(rec_frames) >= 1
    for f in rec_frames:
        assert f["frame_shape"].lower() == "rectangular"

    # Search query
    res_search = client.get("/api/v1/eyewear/frames?search=Vedic")
    assert res_search.status_code == status.HTTP_200_OK
    search_frames = res_search.json()
    assert len(search_frames) >= 1
    assert "Vedic" in search_frames[0]["name"]


def test_get_specific_frame_and_asset_telemetry(client: TestClient):
    """Verifies fetching single frame detail and dedicated try-on asset telemetry."""
    # List to obtain an active frame ID
    list_res = client.get("/api/v1/eyewear/frames")
    frames = list_res.json()
    target_frame_id = frames[0]["frame_id"]

    # 1. GET /frames/{id}
    res = client.get(f"/api/v1/eyewear/frames/{target_frame_id}")
    assert res.status_code == status.HTTP_200_OK
    frame_detail = res.json()
    assert frame_detail["frame_id"] == target_frame_id
    assert frame_detail["try_on_asset_url"] is not None
    assert frame_detail["left_lens_center_x"] < frame_detail["right_lens_center_x"]

    # 2. GET /frames/{id}/try-on-assets
    assets_res = client.get(f"/api/v1/eyewear/frames/{target_frame_id}/try-on-assets")
    assert assets_res.status_code == status.HTTP_200_OK
    assert assets_res.json()["frame_id"] == target_frame_id

    # 3. GET with non-existent UUID -> 404
    non_existent = str(uuid.uuid4())
    err_res = client.get(f"/api/v1/eyewear/frames/{non_existent}")
    assert err_res.status_code == status.HTTP_404_NOT_FOUND


def test_try_on_session_lifecycle(client: TestClient):
    """Verifies creating an AR try-on session, switching frames, taking snapshots, and ending session."""
    # List frames
    frames = client.get("/api/v1/eyewear/frames").json()
    frame1_id = frames[0]["frame_id"]
    frame2_id = frames[1]["frame_id"]

    # 1. Create try-on session
    session_res = client.post(
        "/api/v1/eyewear/try-on/sessions",
        json={
            "selected_product_id": frame1_id,
            "selected_color": "#111827",
            "selected_scale": 1.0,
            "selected_offset_y": 0.0,
            "camera_facing": "user",
            "device_type": "desktop",
        },
    )
    assert session_res.status_code == status.HTTP_201_CREATED
    session_data = session_res.json()
    session_id = session_data["id"]
    assert session_data["selected_product_id"] == frame1_id
    assert session_data["is_active"] is True
    assert session_data["snapshots_count"] == 0

    # 2. Get session
    get_res = client.get(f"/api/v1/eyewear/try-on/sessions/{session_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == session_id

    # 3. Select different frame & color
    select_res = client.post(
        f"/api/v1/eyewear/try-on/sessions/{session_id}/select-frame",
        json={
            "product_id": frame2_id,
            "selected_color": "#92400e",
            "selected_scale": 1.05,
            "selected_offset_y": 2.0,
        },
    )
    assert select_res.status_code == status.HTTP_200_OK
    updated_session = select_res.json()
    assert updated_session["selected_product_id"] == frame2_id
    assert updated_session["selected_color"] == "#92400e"
    assert updated_session["selected_scale"] == 1.05

    # 4. Record snapshot preview
    snapshot_res = client.post(
        f"/api/v1/eyewear/try-on/sessions/{session_id}/capture",
        json={
            "product_id": frame2_id,
            "selected_color": "#92400e",
            "title": "OptiGuide Try-On Test Snapshot",
            "face_detected": True,
        },
    )
    assert snapshot_res.status_code == status.HTTP_201_CREATED
    snapshot_data = snapshot_res.json()
    assert snapshot_data["session_id"] == session_id
    assert snapshot_data["face_detected"] is True

    # 5. End session
    end_res = client.delete(f"/api/v1/eyewear/try-on/sessions/{session_id}")
    assert end_res.status_code == status.HTTP_200_OK
    assert end_res.json()["status"] == "closed"


def test_try_on_favourites_authenticated_flow(client: TestClient, patient_user):
    """Verifies that authenticated customers can toggle favourites and retrieve saved frames."""
    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    frames = client.get("/api/v1/eyewear/frames").json()
    target_frame_id = frames[0]["frame_id"]

    # 1. Create try-on session with patient auth
    session_res = client.post(
        "/api/v1/eyewear/try-on/sessions",
        json={"selected_product_id": target_frame_id},
        headers=patient_headers,
    )
    assert session_res.status_code == status.HTTP_201_CREATED
    session_id = session_res.json()["id"]

    # 2. Toggle favourite -> added
    fav_res = client.post(
        f"/api/v1/eyewear/try-on/sessions/{session_id}/favourite",
        json={"product_id": target_frame_id, "selected_color": "#111827"},
        headers=patient_headers,
    )
    assert fav_res.status_code == status.HTTP_200_OK
    assert fav_res.json()["action"] == "added"

    # 3. List favourites -> target_frame_id is present
    list_fav = client.get("/api/v1/eyewear/try-on/favourites", headers=patient_headers)
    assert list_fav.status_code == status.HTTP_200_OK
    fav_items = list_fav.json()
    assert len(fav_items) >= 1
    assert any(str(item["product_id"]) == target_frame_id for item in fav_items)

    # 4. Toggle favourite again -> removed
    unfav_res = client.post(
        f"/api/v1/eyewear/try-on/sessions/{session_id}/favourite",
        json={"product_id": target_frame_id},
        headers=patient_headers,
    )
    assert unfav_res.status_code == status.HTTP_200_OK
    assert unfav_res.json()["action"] == "removed"

    # 5. Favourites without token -> 401 Unauthorized
    anon_fav = client.get("/api/v1/eyewear/try-on/favourites")
    assert anon_fav.status_code == status.HTTP_401_UNAUTHORIZED


def test_try_on_validation_and_boundaries(client: TestClient):
    """Verifies that invalid scales, offsets, and non-existent IDs are properly rejected."""
    # Scale too large (> 2.0) -> 422
    res_large = client.post(
        "/api/v1/eyewear/try-on/sessions",
        json={"selected_scale": 3.5},
    )
    assert res_large.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Scale too small (< 0.5) -> 422
    res_small = client.post(
        "/api/v1/eyewear/try-on/sessions",
        json={"selected_scale": 0.1},
    )
    assert res_small.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid camera facing mode -> 422
    res_camera = client.post(
        "/api/v1/eyewear/try-on/sessions",
        json={"camera_facing": "invalid_mode"},
    )
    assert res_camera.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
