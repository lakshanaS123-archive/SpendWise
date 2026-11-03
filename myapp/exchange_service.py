import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("spendwise.exchange")

# In-memory last known successful cache as persistent local fallback
_LAST_KNOWN_RATES: Dict[str, Any] = {
    "provider": "Open Exchange Rates API (Fallback Cache)",
    "base": "USD",
    "updated_at": "2026-11-01T00:00:00Z",
    "is_live": False,
    "rates": {
        "INR": 85.50,
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "AED": 3.67,
        "SGD": 1.34,
        "CAD": 1.39,
        "AUD": 1.54,
        "JPY": 152.20,
    },
}


class ExchangeRateService:
    """
    Robust currency exchange rate service with timeout, cache,
    and automatic offline fallback.
    """

    CACHE_KEY = "spendwise_exchange_rates"
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_exchange_rates(cls) -> Dict[str, Any]:
        """
        Retrieves exchange rates. Attempts live API request with 5s timeout.
        Falls back to cached rates if remote API fails or times out.
        """
        cached = cache.get(cls.CACHE_KEY)
        if cached:
            cached["from_cache"] = True
            return cached

        api_url = getattr(
            settings,
            "EXCHANGE_RATE_API_URL",
            "https://open.er-api.com/v6/latest/USD",
        )
        api_key = getattr(settings, "EXCHANGE_RATE_API_KEY", "")

        headers = {"User-Agent": "SpendWise-App/2.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            start_t = time.time()
            response = requests.get(api_url, headers=headers, timeout=5)
            duration_ms = round((time.time() - start_t) * 1000, 2)

            if response.status_code == 200:
                data = response.json()
                raw_rates = data.get("rates", {})

                # Validate expected rates
                if "INR" in raw_rates and "USD" in raw_rates:
                    target_currencies = [
                        "INR", "USD", "EUR", "GBP", "AED", "SGD", "CAD", "AUD", "JPY"
                    ]
                    filtered_rates = {
                        k: float(raw_rates[k])
                        for k in target_currencies
                        if k in raw_rates
                    }

                    result = {
                        "provider": "open.er-api.com",
                        "base": data.get("base_code", "USD"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "is_live": True,
                        "duration_ms": duration_ms,
                        "rates": filtered_rates,
                    }

                    # Store in Django cache and update memory cache
                    cache.set(cls.CACHE_KEY, result, cls.CACHE_TIMEOUT)
                    _LAST_KNOWN_RATES.update(result)
                    _LAST_KNOWN_RATES["is_live"] = False
                    return result

            logger.warning(
                f"Exchange API returned unexpected status {response.status_code}"
            )
        except requests.exceptions.Timeout:
            logger.warning("Exchange rate API request timed out after 5 seconds.")
        except Exception as e:
            logger.warning(f"Exchange rate API request failed: {e}")

        # Fallback to last known rates
        fallback_data = dict(_LAST_KNOWN_RATES)
        fallback_data["from_fallback"] = True
        fallback_data["warning"] = "Live exchange rates temporarily unreachable; showing cached rates."
        return fallback_data
