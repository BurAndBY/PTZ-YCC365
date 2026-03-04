import logging
import time

import requests

DOMAIN = "ptz_camera"
LOGGER = logging.getLogger(__name__)

ATTR_HOST = "host"
ATTR_PROFILE = "profile"
ATTR_PAN_TIME = "pan_time"
ATTR_MOVE_TIME = "move_time"

DEFAULT_HOST = "192.168.1.244"
DEFAULT_PROFILE = "Profile_1"
DEFAULT_PAN_TIME = 10
DEFAULT_MOVE_TIME = 0.3
DEFAULT_HEADERS = {"Content-Type": "application/soap+xml;charset=UTF8"}


def _post_soap(host, xml):
    response = requests.post(
        f"http://{host}/onvif/PTZ",
        data=xml,
        headers=DEFAULT_HEADERS,
        timeout=5,
    )
    response.raise_for_status()


def _stop_xml(profile):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
 <soap:Body>
 <tptz:Stop>
 <tptz:ProfileToken>{profile}</tptz:ProfileToken>
 <tptz:PanTilt>true</tptz:PanTilt>
 <tptz:Zoom>true</tptz:Zoom>
 </tptz:Stop>
 </soap:Body>
</soap:Envelope>"""


def _move_xml(profile, x, y):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <soap:Body>
 <tptz:ContinuousMove>
 <tptz:ProfileToken>{profile}</tptz:ProfileToken>
 <tptz:Velocity>
 <tt:PanTilt x="{x}" y="{y}"/>
 <tt:Zoom x="1"/>
 </tptz:Velocity>
 </tptz:ContinuousMove>
 </soap:Body>
</soap:Envelope>"""


def _get_service_handlers():
    def stop(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        try:
            _post_soap(host, _stop_xml(profile))
        except requests.RequestException as err:
            LOGGER.error("PTZ stop failed for host %s: %s", host, err)

    def move_left(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        move_time = call.data.get(ATTR_MOVE_TIME, DEFAULT_MOVE_TIME)
        try:
            _post_soap(host, _move_xml(profile, "-0.5", "0"))
            time.sleep(move_time)
            stop(call)
        except requests.RequestException as err:
            LOGGER.error("PTZ move_left failed for host %s: %s", host, err)

    def move_right(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        move_time = call.data.get(ATTR_MOVE_TIME, DEFAULT_MOVE_TIME)
        try:
            _post_soap(host, _move_xml(profile, "0.5", "0"))
            time.sleep(move_time)
            stop(call)
        except requests.RequestException as err:
            LOGGER.error("PTZ move_right failed for host %s: %s", host, err)

    def move_up(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        move_time = call.data.get(ATTR_MOVE_TIME, DEFAULT_MOVE_TIME)
        try:
            _post_soap(host, _move_xml(profile, "0", "0.5"))
            time.sleep(move_time)
            stop(call)
        except requests.RequestException as err:
            LOGGER.error("PTZ move_up failed for host %s: %s", host, err)

    def move_down(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        move_time = call.data.get(ATTR_MOVE_TIME, DEFAULT_MOVE_TIME)
        try:
            _post_soap(host, _move_xml(profile, "0", "-0.5"))
            time.sleep(move_time)
            stop(call)
        except requests.RequestException as err:
            LOGGER.error("PTZ move_down failed for host %s: %s", host, err)

    def move_origin_pan(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        try:
            _post_soap(host, _move_xml(profile, "-0.5", "0"))
        except requests.RequestException as err:
            LOGGER.error("PTZ move_origin_pan failed for host %s: %s", host, err)

    def move_origin_tilt(call):
        host = call.data.get(ATTR_HOST, DEFAULT_HOST)
        profile = call.data.get(ATTR_PROFILE, DEFAULT_PROFILE)
        try:
            _post_soap(host, _move_xml(profile, "0", "-0.5"))
        except requests.RequestException as err:
            LOGGER.error("PTZ move_origin_tilt failed for host %s: %s", host, err)

    def move_origin(call):
        pan_time = call.data.get(ATTR_PAN_TIME, DEFAULT_PAN_TIME)
        move_origin_pan(call)
        time.sleep(pan_time)
        move_origin_tilt(call)

    return {
        "move_left": move_left,
        "move_right": move_right,
        "move_up": move_up,
        "move_down": move_down,
        "stop": stop,
        "move_origin": move_origin,
        "move_origin_pan": move_origin_pan,
        "move_origin_tilt": move_origin_tilt,
    }


def _register_services_sync(hass):
    handlers = _get_service_handlers()
    for service_name, handler in handlers.items():
        hass.services.register(DOMAIN, service_name, handler)


async def _register_services_async(hass):
    handlers = _get_service_handlers()
    for service_name, handler in handlers.items():

        async def async_wrapper(call, _handler=handler):
            await hass.async_add_executor_job(_handler, call)

        hass.services.async_register(DOMAIN, service_name, async_wrapper)


def setup(hass, config):
    LOGGER.info("Setting up PTZ Camera integration")
    _register_services_sync(hass)
    return True


async def async_setup(hass, config):
    LOGGER.info("Setting up PTZ Camera integration (async)")
    await _register_services_async(hass)
    return True
