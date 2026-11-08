"""Config flow tests."""
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.georide.const import DOMAIN


async def test_user_flow(hass, mock_api, no_socket):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"email": "moi@example.com", "password": "pwd"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["token"]


async def test_user_flow_bad_credentials(hass, aioclient_mock):
    aioclient_mock.post("https://api.georide.com/user/login", status=403)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"email": "moi@example.com", "password": "bad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "faulty_credentials"}
