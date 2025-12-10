"""Contract tests for OpenAPI schema validation."""

import pytest
import yaml


def test_openapi_schema_loads():
    """Test OpenAPI schema can be loaded and parsed."""
    schema_path = "specs/001-telegram-marketplace/contracts/openapi.yaml"

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    assert schema["openapi"] == "3.0.3"
    assert "paths" in schema
    assert "components" in schema


def test_openapi_required_endpoints():
    """Test OpenAPI defines required endpoints."""
    schema_path = "specs/001-telegram-marketplace/contracts/openapi.yaml"

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    paths = schema["paths"]

    # Check critical endpoints exist
    assert "/businesses" in paths
    assert "/businesses/{businessId}/offers" in paths
    assert "/offers/{offerId}/publish" in paths
    assert "/offers/{offerId}/pause" in paths
    assert "/offers/{offerId}/purchase" in paths
    assert "/offers" in paths
    assert "/purchases/{purchaseId}/cancel" in paths


def test_openapi_schemas_defined():
    """Test OpenAPI defines required schemas."""
    schema_path = "specs/001-telegram-marketplace/contracts/openapi.yaml"

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    schemas = schema["components"]["schemas"]

    # Check critical schemas exist
    assert "Business" in schemas
    assert "Offer" in schemas
    assert "Purchase" in schemas
    assert "Item" in schemas
    assert "PurchaseRequest" in schemas
