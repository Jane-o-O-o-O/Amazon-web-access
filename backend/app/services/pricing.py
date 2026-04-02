"""
Pricing service: calculate profit margins for a product.
"""
from dataclasses import dataclass


@dataclass
class CostParams:
    purchase_price: float        # CNY unit cost
    domestic_shipping: float = 0.0
    international_shipping: float = 0.0
    fba_fee: float = 0.0
    commission_rate: float = 0.15   # Amazon referral fee %
    ads_rate: float = 0.08          # Advertising %
    tax_rate: float = 0.03          # Tax %
    exchange_rate: float = 7.2      # CNY -> USD


def calculate_margin(params: CostParams, sell_price: float) -> dict:
    """
    Calculate full profit breakdown given cost params and selling price (USD).
    """
    # Convert CNY costs to USD
    purchase_usd = params.purchase_price / params.exchange_rate
    domestic_usd = params.domestic_shipping / params.exchange_rate
    intl_usd = params.international_shipping  # already USD typically

    # Variable costs based on sell price
    commission = sell_price * params.commission_rate
    ads_cost = sell_price * params.ads_rate
    tax = sell_price * params.tax_rate

    total_cost = (
        purchase_usd
        + domestic_usd
        + intl_usd
        + params.fba_fee
        + commission
        + ads_cost
        + tax
    )

    gross_profit = sell_price - commission - (purchase_usd + domestic_usd + intl_usd + params.fba_fee)
    net_profit = sell_price - total_cost
    gross_margin = gross_profit / sell_price if sell_price else 0
    net_margin = net_profit / sell_price if sell_price else 0

    # Suggested price for ~25-35% net margin
    target_margin = 0.30
    fixed_costs = purchase_usd + domestic_usd + intl_usd + params.fba_fee
    variable_rate = params.commission_rate + params.ads_rate + params.tax_rate
    suggested_price = fixed_costs / (1 - variable_rate - target_margin) if (1 - variable_rate - target_margin) > 0 else 0

    return {
        "purchase_usd": round(purchase_usd, 4),
        "domestic_shipping_usd": round(domestic_usd, 4),
        "international_shipping": round(intl_usd, 4),
        "fba_fee": round(params.fba_fee, 4),
        "commission": round(commission, 4),
        "ads_cost": round(ads_cost, 4),
        "tax": round(tax, 4),
        "total_cost": round(total_cost, 4),
        "sell_price": round(sell_price, 2),
        "gross_profit": round(gross_profit, 4),
        "net_profit": round(net_profit, 4),
        "gross_margin": round(gross_margin, 4),
        "net_margin": round(net_margin, 4),
        "suggested_price_min": round(suggested_price * 0.95, 2),
        "suggested_price_max": round(suggested_price * 1.15, 2),
    }
