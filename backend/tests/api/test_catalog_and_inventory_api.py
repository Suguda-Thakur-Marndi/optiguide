"""
Integration test suite for Phase 4 Eyewear Product Catalogue and Shop Inventory.
Verifies category/brand creation, product search, shop onboarding, inventory adjustment,
negative stock protection, transaction auditing, and authorization boundaries.
"""

from fastapi import status
from starlette.testclient import TestClient

from app.core.security import create_access_token


def test_catalog_category_and_brand_admin_flow(
    client: TestClient, admin_user, shopkeeper_user, patient_user
):
    """Verifies that only admins can create categories and brands, while all users can list them."""
    admin_token, _ = create_access_token(
        user_id=admin_user.id, email=admin_user.email, role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    shop_token, _ = create_access_token(
        user_id=shopkeeper_user.id, email=shopkeeper_user.email, role="shopkeeper"
    )
    shop_headers = {"Authorization": f"Bearer {shop_token}"}

    # 1. Shopkeeper tries to create category -> 403 Forbidden
    res = client.post(
        "/api/v1/catalog/admin/categories",
        json={"name": "Spectacles", "slug": "spectacles", "description": "Standard optical frames"},
        headers=shop_headers,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admin creates category
    cat_res = client.post(
        "/api/v1/catalog/admin/categories",
        json={
            "name": "Eyeglasses",
            "slug": "eyeglasses",
            "description": "Prescription and screening frames",
        },
        headers=admin_headers,
    )
    assert cat_res.status_code == status.HTTP_201_CREATED
    category_id = cat_res.json()["id"]

    # 3. Admin creates brand
    brand_res = client.post(
        "/api/v1/catalog/admin/brands",
        json={"name": "OptiCraft", "slug": "opticraft"},
        headers=admin_headers,
    )
    assert brand_res.status_code == status.HTTP_201_CREATED
    brand_id = brand_res.json()["id"]

    # 4. List categories and brands
    list_cat = client.get("/api/v1/catalog/categories", headers=shop_headers)
    assert list_cat.status_code == status.HTTP_200_OK
    assert any(c["id"] == category_id for c in list_cat.json())

    list_brands = client.get("/api/v1/catalog/brands", headers=shop_headers)
    assert list_brands.status_code == status.HTTP_200_OK
    assert any(b["id"] == brand_id for b in list_brands.json())


def test_product_catalogue_search_and_admin_guards(client: TestClient, admin_user, patient_user):
    """Verifies product creation, querying with multiple filters, and role restrictions."""
    admin_token, _ = create_access_token(
        user_id=admin_user.id, email=admin_user.email, role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    patient_token, _ = create_access_token(
        user_id=patient_user.id, email=patient_user.email, role="patient"
    )
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Setup category and brand
    cat = client.post(
        "/api/v1/catalog/admin/categories",
        json={"name": "Budget Line", "slug": "budget-line"},
        headers=admin_headers,
    ).json()
    brand = client.post(
        "/api/v1/catalog/admin/brands",
        json={"name": "RuralVision", "slug": "ruralvision"},
        headers=admin_headers,
    ).json()

    # Patient cannot create product
    prod_payload = {
        "sku": "RV-RECT-01",
        "name": "RuralVision Classic Rectangular",
        "category_id": cat["id"],
        "brand_id": brand["id"],
        "frame_shape": "RECTANGULAR",
        "frame_type": "FULL_RIM",
        "frame_material": "TR90",
        "gender_target": "unisex",
        "base_price_inr": 850.0,
        "lens_width_mm": 52.0,
        "bridge_width_mm": 18.0,
        "temple_length_mm": 140.0,
    }
    fail_res = client.post(
        "/api/v1/catalog/admin/products", json=prod_payload, headers=patient_headers
    )
    assert fail_res.status_code == status.HTTP_403_FORBIDDEN

    # Admin creates product
    create_res = client.post(
        "/api/v1/catalog/admin/products", json=prod_payload, headers=admin_headers
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    product_data = create_res.json()
    assert product_data["sku"] == "RV-RECT-01"
    product_id = product_data["id"]

    # Filter products by shape and price
    search_res = client.get(
        f"/api/v1/catalog/products?frame_shape=RECTANGULAR&max_price=1000&category_id={cat['id']}",
        headers=patient_headers,
    )
    assert search_res.status_code == status.HTTP_200_OK
    results = search_res.json()
    assert len(results["items"]) >= 1
    assert any(p["id"] == product_id for p in results["items"])

    # Detail lookup
    detail_res = client.get(f"/api/v1/catalog/products/{product_id}", headers=patient_headers)
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.json()["name"] == "RuralVision Classic Rectangular"


def test_shop_inventory_lifecycle_and_negative_stock_defense(
    client: TestClient, admin_user, shopkeeper_user, patient_user
):
    """
    Verifies shop creation, inventory stocking, quantity adjustment,
    transaction audit logging, and rejection of negative stock operations.
    """
    admin_token, _ = create_access_token(
        user_id=admin_user.id, email=admin_user.email, role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    shop_token, _ = create_access_token(
        user_id=shopkeeper_user.id, email=shopkeeper_user.email, role="shopkeeper"
    )
    shop_headers = {"Authorization": f"Bearer {shop_token}"}

    # 1. Setup a product
    cat = client.post(
        "/api/v1/catalog/admin/categories",
        json={"name": "Safety Frames", "slug": "safety-frames"},
        headers=admin_headers,
    ).json()
    brand = client.post(
        "/api/v1/catalog/admin/brands",
        json={"name": "KiranOptics", "slug": "kiranoptics"},
        headers=admin_headers,
    ).json()
    prod = client.post(
        "/api/v1/catalog/admin/products",
        json={
            "sku": "KO-ROUND-99",
            "name": "Kiran Round Polycarbonate",
            "category_id": cat["id"],
            "brand_id": brand["id"],
            "frame_shape": "ROUND",
            "frame_type": "FULL_RIM",
            "frame_material": "POLYCARBONATE",
            "gender_target": "unisex",
            "base_price_inr": 600.0,
        },
        headers=admin_headers,
    ).json()

    # 2. Shopkeeper creates shop
    shop_res = client.post(
        "/api/v1/shops",
        json={
            "name": "Gramin Netra Kendra",
            "location_city": "Dharwad",
            "location_state": "Karnataka",
            "phone_number": "+919876543210",
        },
        headers=shop_headers,
    )
    assert shop_res.status_code == status.HTTP_201_CREATED
    shop_id = shop_res.json()["id"]

    # 3. Add inventory item: initial quantity 15
    inv_res = client.post(
        f"/api/v1/shops/{shop_id}/inventory/adjust",
        json={
            "product_id": prod["id"],
            "quantity_delta": 15,
            "reason": "RESTOCK",
            "notes": "Initial stocking from regional warehouse",
        },
        headers=shop_headers,
    )
    assert inv_res.status_code == status.HTTP_200_OK
    inv_data = inv_res.json()
    inv_id = inv_data["id"]
    assert inv_data["stock_quantity"] == 15
    assert inv_data["available_quantity"] == 15

    # 4. Adjust inventory: sale of 5 frames
    adjust_res = client.post(
        f"/api/v1/shops/{shop_id}/inventory/adjust",
        json={
            "product_id": prod["id"],
            "quantity_delta": -5,
            "reason": "SALE",
            "notes": "Dispensed to screening camp participant",
        },
        headers=shop_headers,
    )
    assert adjust_res.status_code == status.HTTP_200_OK
    assert adjust_res.json()["stock_quantity"] == 10

    # 5. Business safety check: Attempt to deduct more stock than available (-20 when stock is 10)
    over_deduct_res = client.post(
        f"/api/v1/shops/{shop_id}/inventory/adjust",
        json={
            "product_id": prod["id"],
            "quantity_delta": -20,
            "reason": "ADJUSTMENT",
            "notes": "Excessive deduction test",
        },
        headers=shop_headers,
    )
    assert over_deduct_res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Insufficient stock" in over_deduct_res.json()["error"]["message"]

    # 6. Verify audit trail / inventory transactions
    tx_res = client.get(
        f"/api/v1/shops/{shop_id}/inventory/{inv_id}/transactions",
        headers=shop_headers,
    )
    assert tx_res.status_code == status.HTTP_200_OK
    tx_json = tx_res.json()
    # At least RESTOCK (+15) and SALE (-5)
    assert tx_json["total"] >= 2
    reasons = [t["reason"] for t in tx_json["items"]]
    assert "RESTOCK" in reasons
    assert "SALE" in reasons
