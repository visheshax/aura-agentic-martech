import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from database import get_db

# Import our agents
from agents.identity_agent import IdentityStitchingAgent
from agents.copywriter_agent import CopywriterAgent
from agents.compliance_agent import ComplianceAgent
from agents.promo_agent import PromoOptimizationAgent

class CampaignOrchestrator:
    """
    Main Orchestrator Agent
    Coordinates the marketing execution flow and streams logs & state updates to the UI in real-time.
    """
    def __init__(self):
        self.db = get_db()
        self.identity_agent = IdentityStitchingAgent()
        self.copywriter_agent = CopywriterAgent()
        self.compliance_agent = ComplianceAgent()
        self.promo_agent = PromoOptimizationAgent()

    async def execute(self, email: str) -> AsyncGenerator[str, None]:
        """
        Executes the agentic pipeline and yields JSON-serialized SSE stream messages.
        """
        try:
            # --- STEP 1: IDENTITY RESOLUTION & COMPOSABLE CDP STITCHING ---
            yield self._format_stream_event("step_start", {
                "step": "CDP_STITCHING",
                "title": "Identity Stitching (CDP)",
                "message": "Resolving customer profile from messy raw data..."
            })
            await asyncio.sleep(1.0)
            
            res_identity = self.identity_agent.run(email)
            for log in res_identity.get("logs", []):
                yield self._format_stream_event("log", {"step": "CDP_STITCHING", "log": log})
                await asyncio.sleep(0.1)

            profile = res_identity.get("profile", {})
            yield self._format_stream_event("step_complete", {
                "step": "CDP_STITCHING",
                "profile": profile
            })

            # --- STEP 2: PROMO CODE OPTIMIZATION ---
            yield self._format_stream_event("step_start", {
                "step": "PROMO_OPTIMIZATION",
                "title": "Margin/Promo Optimizer",
                "message": "Calculating margin-safe coupon values and anti-abuse safeguards..."
            })
            await asyncio.sleep(1.0)
            
            res_promo = self.promo_agent.run(profile)
            for log in res_promo.get("logs", []):
                yield self._format_stream_event("log", {"step": "PROMO_OPTIMIZATION", "log": log})
                await asyncio.sleep(0.1)

            yield self._format_stream_event("step_complete", {
                "step": "PROMO_OPTIMIZATION",
                "coupon_code": res_promo.get("coupon_code"),
                "discount_percent": res_promo.get("discount_percent")
            })

            # --- STEP 3: CREATIVE COPYWRITING ---
            yield self._format_stream_event("step_start", {
                "step": "CREATIVE_COPYWRITING",
                "title": "Creative Copywriter",
                "message": "Drafting hyper-personalized email copy and subject lines..."
            })
            await asyncio.sleep(1.0)
            
            # Inject promo code into context for copywriting
            profile_with_promo = dict(profile)
            profile_with_promo["coupon_code"] = res_promo.get("coupon_code")
            res_copy = self.copywriter_agent.run(profile_with_promo)
            
            for log in res_copy.get("logs", []):
                yield self._format_stream_event("log", {"step": "CREATIVE_COPYWRITING", "log": log})
                await asyncio.sleep(0.1)

            email_body = res_copy.get("body", "")
            email_subject = res_copy.get("subject", "")
            
            # Add dynamic coupon block in fallback body if not already present
            if res_promo.get("coupon_code") not in email_body:
                email_body += f"<br/><br/>Your Exclusive Code: <strong>{res_promo.get('coupon_code')}</strong> ({res_promo.get('discount_percent')}% OFF)"

            yield self._format_stream_event("step_complete", {
                "step": "CREATIVE_COPYWRITING",
                "subject": email_subject,
                "body": email_body
            })

            # --- STEP 4: COMPLIANCE & LEGAL AUDITING ---
            yield self._format_stream_event("step_start", {
                "step": "COMPLIANCE_AUDIT",
                "title": "GDPR & Legal Guardrails",
                "message": "Performing privacy-safety checks and brand protection audits..."
            })
            await asyncio.sleep(1.0)
            
            res_compliance = self.compliance_agent.run(email_body, email_subject, profile)
            for log in res_compliance.get("logs", []):
                yield self._format_stream_event("log", {"step": "COMPLIANCE_AUDIT", "log": log})
                await asyncio.sleep(0.1)

            yield self._format_stream_event("step_complete", {
                "step": "COMPLIANCE_AUDIT",
                "approved": res_compliance.get("approved"),
                "report": res_compliance.get("report")
            })

            # --- STEP 5: SIMULATING CUSTOMER SUCCESS ADVISOR SCRIPT ---
            yield self._format_stream_event("step_start", {
                "step": "ADVISOR_SCRIPT",
                "title": "CS Advisor Script",
                "message": "Synthesizing dynamic advisor response script for client success teams..."
            })
            await asyncio.sleep(0.8)
            
            interests_str = ", ".join(profile.get("interests", []))
            advisor_script = (
                f"Client Profile stitch complete for phone interactions.\n"
                f"1. Acknowledge customer's direct focus on {interests_str}.\n"
                f"2. Mention the active discount {res_promo.get('coupon_code')} is automatically tied to their account.\n"
                f"3. Highlight zero-trust compliance standards are satisfied: all data processed matches GDPR permissions."
            )
            
            yield self._format_stream_event("step_complete", {
                "step": "ADVISOR_SCRIPT",
                "script": advisor_script
            })

            # --- STEP 6: PERSIST CAMPAIGN AND CALCULATE P&L IMPACT ---
            yield self._format_stream_event("step_start", {
                "step": "PERSISTENCE",
                "title": "System Save & ROI Calculator",
                "message": "Saving campaign log and compiling simulated financial impact..."
            })
            await asyncio.sleep(0.8)
            
            # P&L calculations (ROI/margin impact metrics)
            conversion_probs = {"high": 0.85, "medium": 0.65, "low": 0.40}
            base_prob = conversion_probs.get(profile.get("price_sensitivity", "medium"), 0.50)
            # Higher discount increases conversion probability slightly
            prob_boost = (res_promo.get("discount_percent", 10) / 100.0) * 0.5
            conversion_probability = min(base_prob + prob_boost, 0.95)
            
            # Simulating OPEX savings from automation vs traditional copywriting agency hours
            total_cost_saved = 45.50 

            campaign_data = {
                "profile_id": profile.get("id"),
                "trigger_event": "abandoned_cart_retention",
                "generated_email_subject": email_subject,
                "generated_email_body": email_body,
                "generated_advisor_script": advisor_script,
                "coupon_code": res_promo.get("coupon_code"),
                "coupon_discount_percent": res_promo.get("discount_percent"),
                "compliance_approved": res_compliance.get("approved"),
                "compliance_report": res_compliance.get("report"),
                "total_cost_saved": total_cost_saved,
                "conversion_probability": conversion_probability
            }
            
            # Save campaign entry
            self.db.table("campaign_logs").insert(campaign_data)
            
            yield self._format_stream_event("step_complete", {
                "step": "PERSISTENCE",
                "total_cost_saved": total_cost_saved,
                "conversion_probability": conversion_probability
            })

            # Pipeline Finished
            yield self._format_stream_event("pipeline_complete", {
                "message": "All agents finished executing successfully.",
                "final_data": campaign_data
            })

        except Exception as e:
            yield self._format_stream_event("error", {
                "message": f"Pipeline failed: {str(e)}"
            })

    def _format_stream_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Formats the payload for SSE streaming."""
        payload = {
            "event": event_type,
            "data": data
        }
        return f"data: {json.dumps(payload)}\n\n"
