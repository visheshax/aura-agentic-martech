import os
from typing import Dict, Any
from openai import OpenAI

class CopywriterAgent:
    """
    Creative Copywriting Agent
    Generates tailored, high-converting copy based on user segmentation and interests.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and self.api_key != "your_openai_api_key":
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def run(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        logs = []
        logs.append("✍️ [Copywriter Agent] Initializing email generation...")
        
        name = profile.get("full_name", "Valued Customer")
        interests = ", ".join(profile.get("interests", []))
        sensitivity = profile.get("price_sensitivity", "medium")
        
        logs.append(f"✍️ [Copywriter Agent] Tailoring content for {name} (Interests: {interests}, Sensitivity: {sensitivity})")
        
        # Base Prompting / Content generation logic
        subject = ""
        body = ""
        
        if self.client:
            try:
                prompt = f"""
                You are a premium copywriter at a luxury retail brand.
                Write a highly personalized, compelling email to a customer with the following profile:
                - Name: {name}
                - Interests: {interests}
                - Price Sensitivity: {sensitivity}
                
                Keep the tone elegant, welcoming, and crisp. Focus on their interests.
                Return exactly in this JSON format:
                {{
                    "subject": "Email Subject Line",
                    "body": "Email Body Paragraphs (HTML formatted with <br/> but no raw HTML wrapping blocks)"
                }}
                """
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                import json
                result = json.loads(response.choices[0].message.content)
                subject = result.get("subject", "")
                body = result.get("body", "")
                logs.append("✍️ [Copywriter Agent] LLM email copy successfully generated.")
            except Exception as e:
                logs.append(f"⚠️ [Copywriter Agent] LLM generation failed: {e}. Using rule-based fallback.")
                subject, body = self._get_fallback_copy(name, interests, sensitivity)
        else:
            logs.append("ℹ️ [Copywriter Agent] No OpenAI API Key found. Using high-quality rule-based copy engine.")
            subject, body = self._get_fallback_copy(name, interests, sensitivity)

        logs.append("✅ [Copywriter Agent] Personalization draft finalized.")
        return {
            "status": "success",
            "subject": subject,
            "body": body,
            "logs": logs
        }

    def _get_fallback_copy(self, name: str, interests: str, sensitivity: str) -> tuple:
        if sensitivity == "high":
            subject = f"Exclusive Inside Offer: Elevate Your Training, {name}!"
            body = (
                f"Hello {name},<br/><br/>"
                f"We noticed your passion for {interests}. As a marathoner and dedicated athlete, you deserve "
                f"gear that keeps up with your stride. To support your next milestone, we've prepared a "
                f"special performance offer just for you.<br/><br/>"
                f"Unlock your exclusive discount below and gear up for your next run with premium comfort.<br/><br/>"
                f"Best regards,<br/>Aura Team"
            )
        elif sensitivity == "low":
            subject = f"Introducing the Next Horizon in Luxury: Custom Selections for {name}"
            body = (
                f"Dear {name},<br/><br/>"
                f"True craftsmanship speaks for itself. Since you appreciate the finer details of {interests}, "
                f"we wanted to extend an invitation to experience our newest curated smart technology collections.<br/><br/>"
                f"Crafted with hand-finished materials and precision sensors, these pieces are designed to match your taste for "
                f"quality and refinement.<br/><br/>"
                f"Discover our private collection today.<br/><br/>"
                f"Warmly,<br/>Aura Luxury Concierge"
            )
        else:
            subject = f"Specially Selected for You: Handpicked {interests} Designs"
            body = (
                f"Hello {name},<br/><br/>"
                f"We've curated a bespoke line of {interests} options tailored precisely to your browsing journey. "
                f"Explore our catalog of balanced style and performance to find the perfect addition to your collection.<br/><br/>"
                f"Enjoy personalized shipping on us as a welcome gesture.<br/><br/>"
                f"Sincerely,<br/>Aura Support"
            )
        return subject, body
