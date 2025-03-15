import json
import os
import datetime
from src.logging.logger import debug_log


def log_external_request(
    service_name, endpoint, request_payload, request_id, method="POST"
):
    """
    Log details of an external API request before it's sent
    """
    log_dir = os.path.join("logs", "external_services")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    log_file = os.path.join(
        log_dir, f"{service_name}_{request_id}_{timestamp}_request.json"
    )

    log_data = {
        "timestamp": timestamp,
        "service": service_name,
        "endpoint": endpoint,
        "method": method,
        "request_id": request_id,
        "payload": request_payload,
    }

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2, default=str)

    debug_log(
        f"External request to {service_name}: {endpoint}", service_name, request_id
    )
    return log_file


def log_external_response(
    service_name,
    endpoint,
    response_data,
    request_id,
    status_code=200,
    error=None,
    request_log_file=None,
):
    """
    Log details of an external API response after it's received
    """
    log_dir = os.path.join("logs", "external_services")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    log_file = os.path.join(
        log_dir, f"{service_name}_{request_id}_{timestamp}_response.json"
    )

    log_data = {
        "timestamp": timestamp,
        "service": service_name,
        "endpoint": endpoint,
        "request_id": request_id,
        "status_code": status_code,
        "error": error,
        "response": response_data,
        "request_log_file": request_log_file,
    }

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2, default=str)

    if error:
        debug_log(
            f"External response error from {service_name}: {error}",
            service_name,
            request_id,
        )
    else:
        debug_log(
            f"External response from {service_name} received (status: {status_code})",
            service_name,
            request_id,
        )

    return log_file
