"""Small Flask web app used for the CI/CD, Docker, Kubernetes and monitoring labs."""
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


def calculate_total(prices, tax_rate=0.0):
    """Return the sum of prices with tax applied.

    Raises ValueError for negative prices or a negative tax rate.
    """
    if tax_rate < 0:
        raise ValueError("tax_rate must not be negative")
    if any(price < 0 for price in prices):
        raise ValueError("prices must not be negative")
    subtotal = sum(prices)
    return round(subtotal * (1 + tax_rate), 2)


def fetch_discount(code):
    """Look up a discount rate for a code.

    In a real system this would call an external service; tests mock it.
    """
    known_codes = {"STUDENT10": 0.10, "WELCOME5": 0.05}
    return known_codes.get(code, 0.0)


def total_with_discount(prices, code, tax_rate=0.0):
    """Return the total after applying a discount code."""
    subtotal = calculate_total(prices, tax_rate)
    discount = fetch_discount(code)
    return round(subtotal * (1 - discount), 2)


@app.before_request
def start_timer():
    """Record the request start time."""
    request.start_time = time.time()


@app.after_request
def record_metrics(response):
    """Record request count and latency for Prometheus."""
    endpoint = request.path
    if endpoint != "/metrics":
        latency = time.time() - getattr(request, "start_time", time.time())
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()
    return response


@app.route("/")
def index():
    """Return a hello message."""
    return jsonify(message="Hello from hogjuulelt!")


@app.route("/health")
def health():
    """Health check used by Docker and Kubernetes probes."""
    return jsonify(status="ok")


@app.route("/total", methods=["POST"])
def total():
    """Calculate a total from a JSON body: {"prices": [...], "tax_rate": 0.1}."""
    data = request.get_json(silent=True) or {}
    try:
        result = calculate_total(data.get("prices", []), data.get("tax_rate", 0.0))
    except (ValueError, TypeError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(total=result)


@app.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
