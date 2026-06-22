import os
from typing import Dict, Any, List
from database import get_db

class IdentityStitchingAgent:
    """
    Identity & Data Stitching Agent (C360 Profiler)
    Stitches fragmented raw customer touchpoints, calculates price sensitivity, 
    and updates/upserts the unified customer profile (C360).
    """
    def __init__(self):
        self.db = get_db()

    def run(self, email: str) -> Dict[str, Any]:
        logs = []
        logs.append(f"🔍 [Identity Agent] Ingesting raw touchpoints for: {email}")
        
        # 1. Fetch all raw events related to this email
        response = self.db.table("raw_customer_touchpoints").select().eq("email", email).execute()
        events = response.data if hasattr(response, 'data') else response
        
        if not events:
            logs.append(f"⚠️ [Identity Agent] No raw touchpoints found for {email}. Creating base profile.")
            events = []

        logs.append(f"📊 [Identity Agent] Found {len(events)} touchpoints (surveys, cart abandonment, page views).")
        
        # 2. Perform identity stitching & profile compilation
        interests = set()
        avg_order_value = 0.0
        price_sensitivity = "medium"
        phone = ""
        full_name = email.split('@')[0].capitalize()
        
        total_price = 0.0
        price_counts = 0
        
        for event in events:
            evt_type = event.get("event_type")
            data = event.get("event_data", {}) or {}
            
            # Extract interest fields
            if "product_category" in data:
                interests.add(data["product_category"])
            if "preferred_sport" in data:
                interests.add(data["preferred_sport"])
                
            # Extract order values
            if "price" in data:
                total_price += float(data["price"])
                price_counts += 1
                
            # Stitch phone number if available
            if "phone" in data:
                phone = data["phone"]
            elif "phone" in event:
                phone = event["phone"]

        if price_counts > 0:
            avg_order_value = round(total_price / price_counts, 2)
            
        # Segment price sensitivity based on rules (K-Means/Algorithmic simulation)
        if avg_order_value > 500:
            price_sensitivity = "low" # High spender, luxury buyer
        elif avg_order_value < 100:
            price_sensitivity = "high" # Price-sensitive bargain seeker
        else:
            price_sensitivity = "medium"

        interests_list = list(interests) if interests else ["General Shopping"]
        logs.append(f"🛠️ [Identity Agent] Resolved attributes -> Interests: {interests_list}, Avg Spend: £{avg_order_value}, Price Sensitivity: {price_sensitivity}")

        # 3. Compile profiles into Supabase
        profile_data = {
            "email": email,
            "phone": phone or "+44 7000 000000",
            "full_name": full_name,
            "interests": interests_list,
            "avg_order_value": avg_order_value,
            "price_sensitivity": price_sensitivity,
            # Mocking a 1536-dim embedding vector representing preference context
            "profile_embedding": [0.1] * 1536 
        }

        # Save profile
        self.db.table("customer_profiles").upsert(profile_data, on_conflict="email")
        logs.append(f"✅ [Identity Agent] Successfully updated C360 Customer Profile for {email}")

        return {
            "status": "success",
            "logs": logs,
            "profile": profile_data
        }
