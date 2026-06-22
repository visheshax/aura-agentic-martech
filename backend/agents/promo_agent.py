import random
import string
from typing import Dict, Any

class PromoOptimizationAgent:
    """
    Promo Optimization Agent
    Calculates dynamic discount codes to maximize profit margins while matching user's price sensitivity segment.
    Runs anti-coupon abuse logic to prevent margin drainage.
    """
    def __init__(self):
        pass

    def run(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        logs = []
        logs.append("💳 [Promo Agent] Analyzing optimal margin and coupon eligibility...")
        
        email = profile.get("email", "")
        sensitivity = profile.get("price_sensitivity", "medium")
        avg_spend = float(profile.get("avg_order_value", 0.0))
        
        # Segment-based dynamic discount percentage (simulating algorithmic pricing)
        if sensitivity == "high":
            discount_pct = 20
            reason = "High sensitivity segment - requires competitive incentive to convert."
        elif sensitivity == "low":
            discount_pct = 5
            reason = "Low sensitivity segment - premium luxury buyer. Keep discount minimal to maximize margin."
        else:
            discount_pct = 10
            reason = "Medium sensitivity segment - balanced value offer."
            
        logs.append(f"💳 [Promo Agent] Price sensitivity: {sensitivity}. Allocated Discount: {discount_pct}%")
        logs.append(f"💳 [Promo Agent] Allocation justification: {reason}")
        
        # Fraud Mitigation check: Let's ensure the user hasn't abused coupons in their touchpoints history.
        # If the user has made low total spend relative to high discounts, flag it.
        if avg_spend < 50.0 and discount_pct > 15:
            # Prevent abuse by lowering discount
            discount_pct = 10
            logs.append("⚠️ [Promo Agent] FRAUD SYSTEM ALERT: Low customer value history relative to promotion tier. Discount adjusted down to 10% to prevent margin abuse.")
        else:
            logs.append("💳 [Promo Agent] FRAUD SYSTEM PASS: No patterns of coupon abuse detected.")

        # Generate a unique secure coupon code prefix
        chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        coupon_code = f"AURA-{discount_pct}-{chars}"
        
        logs.append(f"💳 [Promo Agent] Secured dynamic code: {coupon_code}")

        return {
            "status": "success",
            "coupon_code": coupon_code,
            "discount_percent": discount_pct,
            "logs": logs
        }
