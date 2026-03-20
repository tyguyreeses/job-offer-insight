from __future__ import annotations


def test_create_read_update_delete_offer(client):
    create_payload = {
        "company": "Acme Corp",
        "role": "Software Engineer",
        "location": "Denver, CO",
        "base_salary": 130000,
        "annual_bonus": 10000,
        "annual_equity": 15000,
        "sign_on_bonus": 5000,
        "col_index": 1.1,
    }

    create_response = client.post("/offers", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0

    offer_id = created["id"]
    get_response = client.get(f"/offers/{offer_id}")
    assert get_response.status_code == 200
    assert get_response.json()["company"] == "Acme Corp"

    patch_response = client.patch(f"/offers/{offer_id}", json={"base_salary": 140000})
    assert patch_response.status_code == 200
    assert patch_response.json()["base_salary"] == 140000

    delete_response = client.delete(f"/offers/{offer_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/offers/{offer_id}")
    assert missing_response.status_code == 404


def test_validation_rejects_invalid_values(client):
    invalid_payload = {
        "company": "Bad Offer",
        "role": "Engineer",
        "location": "Remote",
        "base_salary": -10,
        "col_index": 0,
    }

    response = client.post("/offers", json=invalid_payload)
    assert response.status_code == 422


def test_compare_endpoint_returns_computed_fields_and_sorting(client):
    client.post(
        "/offers",
        json={
            "company": "A",
            "role": "Eng",
            "location": "Denver",
            "base_salary": 120000,
            "annual_bonus": 10000,
            "annual_equity": 5000,
            "sign_on_bonus": 2000,
            "col_index": 1.0,
        },
    )
    client.post(
        "/offers",
        json={
            "company": "B",
            "role": "Eng",
            "location": "SF",
            "base_salary": 160000,
            "annual_bonus": 20000,
            "annual_equity": 30000,
            "sign_on_bonus": 10000,
            "col_index": 1.5,
        },
    )

    response = client.get("/offers/compare?sort_by=total_comp_annual&descending=true")
    assert response.status_code == 200

    body = response.json()
    assert len(body["offers"]) == 2
    first = body["offers"][0]
    second = body["offers"][1]

    assert first["total_comp_annual"] >= second["total_comp_annual"]
    assert "total_comp_year1" in first
    assert "total_comp_col_adjusted" in first


def test_compare_rejects_invalid_sort(client):
    response = client.get("/offers/compare?sort_by=unknown")
    assert response.status_code == 400
